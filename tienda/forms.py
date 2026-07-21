from django import forms
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import (
    TmMCliente, TmMHorario, TmMMascota, TmMProducto, TmMProveedor, TmMUsuario, TmPCargo, TmPCategoria, TmPCiudad,
    TmPEspecie, TmPProvincia, TmPRaza, TmPTipocliente,
)


class CiudadSelect(forms.Select):
    """Select de ciudad que anota cada <option> con su provincia para filtrado en cascada por JS."""

    def __init__(self, provincia_map=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.provincia_map = provincia_map or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        raw_value = value.value if hasattr(value, 'value') else value
        provincia_id = self.provincia_map.get(str(raw_value)) if raw_value else None
        if provincia_id:
            option['attrs']['data-provincia'] = str(provincia_id)
        return option


class RazaSelect(forms.Select):
    """Select de raza que anota cada <option> con su especie para filtrado en cascada por JS."""

    def __init__(self, especie_map=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.especie_map = especie_map or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        raw_value = value.value if hasattr(value, 'value') else value
        especie_id = self.especie_map.get(str(raw_value)) if raw_value else None
        if especie_id:
            option['attrs']['data-especie'] = str(especie_id)
        return option


class ClienteForm(forms.ModelForm):
    id_tipo_cliente = forms.ModelChoiceField(
        queryset=TmPTipocliente.objects.order_by('nombre'),
        required=False,
        label='Tipo de cliente',
    )
    id_provincia = forms.ModelChoiceField(
        queryset=TmPProvincia.objects.order_by('nombre_provincia'),
        required=False,
        label='Provincia',
    )

    class Meta:
        model = TmMCliente
        fields = ['nombre', 'apellido', 'id_tipo_cliente', 'identificacion', 'id_ciudad', 'telefono', 'email']
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'identificacion': 'Identificación',
            'id_ciudad': 'Ciudad',
            'telefono': 'Teléfono',
            'email': 'Correo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Ana (o razón social si es empresa)'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej. Torres (vacío para empresas)'}),
            'identificacion': forms.TextInput(attrs={'placeholder': 'Cédula o RUC'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+52 55 ...'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@mail.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ciudades = list(TmPCiudad.objects.select_related('id_provincia').order_by('nombre_ciudad'))
        provincia_map = {str(c.id_ciudad): c.id_provincia_id for c in ciudades if c.id_provincia_id}

        self.fields['id_ciudad'].widget = CiudadSelect(provincia_map=provincia_map)
        self.fields['id_ciudad'].queryset = TmPCiudad.objects.order_by('nombre_ciudad')
        self.fields['id_ciudad'].required = False
        self.fields['nombre'].required = True
        self.fields['apellido'].required = False

        if self.instance and self.instance.pk and self.instance.id_ciudad_id:
            ciudad_actual = next((c for c in ciudades if c.id_ciudad == self.instance.id_ciudad_id), None)
            if ciudad_actual and ciudad_actual.id_provincia_id:
                self.fields['id_provincia'].initial = ciudad_actual.id_provincia_id

        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()


class ProveedorForm(forms.ModelForm):
    id_provincia = forms.ModelChoiceField(
        queryset=TmPProvincia.objects.order_by('nombre_provincia'),
        required=False,
        label='Provincia',
    )

    class Meta:
        model = TmMProveedor
        fields = ['razon_social', 'ruc', 'id_ciudad', 'telefono', 'email']
        labels = {
            'razon_social': 'Razón social',
            'ruc': 'RUC',
            'id_ciudad': 'Ciudad',
            'telefono': 'Teléfono',
            'email': 'Correo',
        }
        widgets = {
            'razon_social': forms.TextInput(attrs={'placeholder': 'Ej. Distribuidora Mascomida S.A.'}),
            'ruc': forms.TextInput(attrs={'placeholder': 'RUC'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+593 99 ...'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@proveedor.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ciudades = list(TmPCiudad.objects.select_related('id_provincia').order_by('nombre_ciudad'))
        provincia_map = {str(c.id_ciudad): c.id_provincia_id for c in ciudades if c.id_provincia_id}

        self.fields['id_ciudad'].widget = CiudadSelect(provincia_map=provincia_map)
        self.fields['id_ciudad'].queryset = TmPCiudad.objects.order_by('nombre_ciudad')
        self.fields['id_ciudad'].required = False
        self.fields['razon_social'].required = True

        if self.instance and self.instance.pk and self.instance.id_ciudad_id:
            ciudad_actual = next((c for c in ciudades if c.id_ciudad == self.instance.id_ciudad_id), None)
            if ciudad_actual and ciudad_actual.id_provincia_id:
                self.fields['id_provincia'].initial = ciudad_actual.id_provincia_id

        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()


class MascotaForm(forms.ModelForm):
    SEXO_CHOICES = [('', '---------'), ('Macho', 'Macho'), ('Hembra', 'Hembra')]
    TALLA_CHOICES = [('', '---------'), ('Pequeña', 'Pequeña'), ('Mediana', 'Mediana'), ('Grande', 'Grande')]

    sexo = forms.ChoiceField(choices=SEXO_CHOICES, required=False)
    talla = forms.ChoiceField(choices=TALLA_CHOICES, required=False)
    id_especie = forms.ModelChoiceField(
        queryset=TmPEspecie.objects.order_by('nombre_especie'),
        required=False,
        label='Especie',
    )

    class Meta:
        model = TmMMascota
        fields = ['nombre', 'id_raza', 'fecha_nacimiento', 'sexo', 'talla', 'id_cliente']
        labels = {
            'nombre': 'Nombre de la mascota',
            'id_raza': 'Raza',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'id_cliente': 'Dueño',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Firulais'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        razas = list(TmPRaza.objects.select_related('id_especie').order_by('nombre_raza'))
        especie_map = {str(r.id_raza): r.id_especie_id for r in razas if r.id_especie_id}

        self.fields['id_raza'].widget = RazaSelect(especie_map=especie_map)
        self.fields['id_raza'].queryset = TmPRaza.objects.order_by('nombre_raza')
        self.fields['id_raza'].label_from_instance = lambda r: r.nombre_raza
        self.fields['id_raza'].required = False
        self.fields['id_cliente'].queryset = TmMCliente.objects.order_by('nombre', 'apellido')
        self.fields['id_cliente'].required = False
        self.fields['nombre'].required = True

        if self.instance and self.instance.pk and self.instance.id_raza_id:
            raza_actual = next((r for r in razas if r.id_raza == self.instance.id_raza_id), None)
            if raza_actual and raza_actual.id_especie_id:
                self.fields['id_especie'].initial = raza_actual.id_especie_id

        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = TmPCategoria
        fields = ['nombre_categoria', 'descripcion']
        labels = {
            'nombre_categoria': 'Nombre',
            'descripcion': 'Descripción',
        }
        widgets = {
            'nombre_categoria': forms.TextInput(attrs={'placeholder': 'Ej. Alimentos', 'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'placeholder': 'Descripción breve (opcional)', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre_categoria'].required = True
        self.fields['descripcion'].required = False


class ProductoForm(forms.ModelForm):
    class Meta:
        model = TmMProducto
        fields = [
            'nombre_producto', 'id_categoria', 'precio_venta_actual', 'precio_costo_referencial',
            'stock_actual', 'stock_minimo',
        ]
        labels = {
            'nombre_producto': 'Nombre del producto',
            'id_categoria': 'Categoría',
            'precio_venta_actual': 'Precio de venta',
            'precio_costo_referencial': 'Costo referencial',
            'stock_actual': 'Stock actual',
            'stock_minimo': 'Stock mínimo',
        }
        widgets = {
            'nombre_producto': forms.TextInput(attrs={'placeholder': 'Ej. Alimento premium 10kg'}),
            'precio_venta_actual': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'precio_costo_referencial': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_actual': forms.NumberInput(attrs={'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_categoria'].queryset = TmPCategoria.objects.order_by('nombre_categoria')
        self.fields['id_categoria'].required = False
        self.fields['nombre_producto'].required = True

        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.ultima_actualizacion = timezone.now()
        if commit:
            obj.save()
        return obj


class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
    )


class CargoForm(forms.ModelForm):
    class Meta:
        model = TmPCargo
        fields = ['nombre_cargo', 'descripcion']
        labels = {
            'nombre_cargo': 'Nombre',
            'descripcion': 'Descripción',
        }
        widgets = {
            'nombre_cargo': forms.TextInput(attrs={'placeholder': 'Ej. Cajero', 'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'placeholder': 'Descripción breve (opcional)', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre_cargo'].required = True
        self.fields['descripcion'].required = False


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
    )
    activo = forms.BooleanField(label='Activo', required=False, initial=True)

    class Meta:
        model = TmMUsuario
        fields = ['nombre_usuario', 'id_cargo', 'activo']
        labels = {
            'nombre_usuario': 'Nombre de usuario',
            'id_cargo': 'Cargo',
            'activo': 'Activo',
        }
        widgets = {
            'nombre_usuario': forms.TextInput(attrs={'placeholder': 'Ej. jperez'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_cargo'].queryset = TmPCargo.objects.order_by('nombre_cargo')
        self.fields['id_cargo'].required = False
        self.fields['nombre_usuario'].required = True
        self.fields['activo'].required = False
        if not (self.instance and self.instance.pk):
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Obligatoria para un usuario nuevo.'
        else:
            self.fields['password'].help_text = 'Deja en blanco para no cambiar la contraseña actual.'

        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (css + ' form-check-input').strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()

    def save(self, commit=True):
        obj = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            obj.contrasena_hash = make_password(password)
        if commit:
            obj.save()
        return obj


class HorarioForm(forms.ModelForm):
    class Meta:
        model = TmMHorario
        fields = ['id_usuario', 'fecha', 'hora_inicio', 'hora_fin']
        labels = {
            'id_usuario': 'Empleado',
            'fecha': 'Fecha',
            'hora_inicio': 'Hora de inicio',
            'hora_fin': 'Hora de fin',
        }
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].queryset = TmMUsuario.objects.order_by('nombre_usuario')
        self.fields['id_usuario'].required = True

        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()
