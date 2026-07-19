from django import forms

from .models import TmMCliente, TmMMascota, TmMServicio, TmPCiudad, TmPRaza


class ClienteForm(forms.ModelForm):
    TIPO_CHOICES = [('', '---------'), ('Natural', 'Natural'), ('Jurídico', 'Jurídico')]

    tipo_cliente = forms.ChoiceField(choices=TIPO_CHOICES, required=False, label='Tipo de cliente')

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
        self.fields['id_ciudad'].queryset = TmPCiudad.objects.order_by('nombre_ciudad')
        self.fields['id_ciudad'].required = False
        self.fields['nombre_razon_social'].required = True
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
        self.fields['id_raza'].queryset = TmPRaza.objects.select_related('id_especie').order_by('nombre_raza')
        self.fields['id_raza'].label_from_instance = self._raza_label
        self.fields['id_raza'].required = False
        self.fields['id_cliente'].queryset = TmMCliente.objects.order_by('nombre_razon_social')
        self.fields['id_cliente'].required = False
        self.fields['nombre'].required = True
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (css + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (css + ' form-control').strip()

    @staticmethod
    def _raza_label(raza):
        if raza.id_especie_id:
            return f'{raza.nombre_raza} ({raza.id_especie.nombre_especie})'
        return raza.nombre_raza

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
