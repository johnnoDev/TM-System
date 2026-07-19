from django import forms

from .models import TmMCliente, TmMMascota, TmMServicio, TmPCiudad, TmPEspecie, TmPProvincia, TmPRaza


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
    TIPO_CHOICES = [('', '---------'), ('Natural', 'Natural'), ('Jurídico', 'Jurídico')]

    tipo_cliente = forms.ChoiceField(choices=TIPO_CHOICES, required=False, label='Tipo de cliente')
    id_provincia = forms.ModelChoiceField(
        queryset=TmPProvincia.objects.order_by('nombre_provincia'),
        required=False,
        label='Provincia',
    )

    class Meta:
        model = TmMCliente
        fields = ['nombre_razon_social', 'tipo_cliente', 'identificacion', 'id_ciudad', 'telefono', 'email']
        labels = {
            'nombre_razon_social': 'Nombre completo',
            'identificacion': 'Identificación',
            'id_ciudad': 'Ciudad',
            'telefono': 'Teléfono',
            'email': 'Correo',
        }
        widgets = {
            'nombre_razon_social': forms.TextInput(attrs={'placeholder': 'Ej. Ana Torres'}),
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
        self.fields['nombre_razon_social'].required = True

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

    def save(self, commit=True):
        obj = super().save(commit=False)
        if obj.pk is None:
            last = TmMCliente.objects.order_by('-id_cliente').first()
            obj.id_cliente = (last.id_cliente + 1) if last else 1
        if commit:
            obj.save()
        return obj


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
        self.fields['id_cliente'].queryset = TmMCliente.objects.order_by('nombre_razon_social')
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

    def save(self, commit=True):
        obj = super().save(commit=False)
        if obj.pk is None:
            last = TmMMascota.objects.order_by('-id_mascota').first()
            obj.id_mascota = (last.id_mascota + 1) if last else 1
        if commit:
            obj.save()
        return obj


class CitaForm(forms.Form):
    id_mascota = forms.ModelChoiceField(queryset=TmMMascota.objects.none(), label='Mascota')
    fecha_hora_reserva = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Fecha y hora',
    )
    id_servicio = forms.ModelChoiceField(queryset=TmMServicio.objects.none(), label='Tipo de servicio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_mascota'].queryset = TmMMascota.objects.select_related('id_cliente').order_by('nombre')
        self.fields['id_mascota'].widget.attrs['class'] = 'form-select'
        self.fields['id_servicio'].queryset = TmMServicio.objects.order_by('nombre_servicio')
        self.fields['id_servicio'].widget.attrs['class'] = 'form-select'
