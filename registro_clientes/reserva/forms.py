from django import forms
from .models import Cliente, Reserva


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cliente', 'fecha_reserva', 'hora_reserva', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'fecha_reserva': DateInput(attrs={'class': 'form-control'}),
            'hora_reserva': TimeInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        cliente = cleaned.get('cliente')
        fecha_reserva = cleaned.get('fecha_reserva')
        # calcular edad en la fecha de reserva (o hoy si no se proporciona fecha_reserva)
        import datetime
        if cliente and cliente.fecha_nacimiento:
            ref_date = fecha_reserva if fecha_reserva else datetime.date.today()
            dob = cliente.fecha_nacimiento
            # calcular edad
            age = ref_date.year - dob.year - ((ref_date.month, ref_date.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError("El cliente es menor de edad y no puede reservar.")
        return cleaned
