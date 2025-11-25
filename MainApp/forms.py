from django import forms
from .models import Cliente, Mesa, Reserva
from django.utils import timezone
from django.db.models import Q

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'preferencias': forms.Select(attrs={'class': 'form-select', 'id': 'select-pref'}),
            'detalle_preferencia': forms.TextInput(attrs={'class': 'form-control', 'id': 'input-detalle', 'placeholder': 'Especifique...'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        pref = cleaned_data.get('preferencias')
        det = cleaned_data.get('detalle_preferencia')
        if pref == 'OTRO' and not det:
            self.add_error('detalle_preferencia', "Debe especificar el detalle si selecciona 'Otro'.")
        return cleaned_data

class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['numero', 'capacidad', 'ubicacion']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
        }

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cliente', 'fecha', 'hora_inicio', 'hora_fin', 'cantidad_personas', 'mesa_asignada', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'cantidad_personas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'mesa_asignada': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    def clean(self):
        cleaned_data = super().clean()
        mesa = cleaned_data.get('mesa_asignada')
        personas = cleaned_data.get('cantidad_personas')
        fecha = cleaned_data.get('fecha')
        inicio = cleaned_data.get('hora_inicio')
        fin = cleaned_data.get('hora_fin')
        # 1. Validar Capacidad
        if mesa and personas:
            if personas > mesa.capacidad:
                self.add_error('cantidad_personas', f"La Mesa {mesa.numero} tiene capacidad máxima de {mesa.capacidad}. Estás intentando reservar para {personas}.")
                
                # Buscar sugerencias
                mesas_aptas = Mesa.objects.filter(capacidad__gte=personas, estado='LIBRE')[:3]
                if mesas_aptas.exists():
                    sug = ", ".join([str(m.numero) for m in mesas_aptas])
                    self.add_error('mesa_asignada', f"Sugerencia: Las mesas {sug} tienen capacidad suficiente.")
                else:
                    self.add_error('mesa_asignada', "No hay mesas disponibles con esa capacidad.")
        # 2. Validar Fecha Pasada
        if fecha and fecha < timezone.now().date():
            self.add_error('fecha', "No se puede reservar en una fecha pasada.")
        # 3. Validar Superposición con Sugerencias
        if mesa and fecha and inicio and fin:
            if inicio >= fin:
                self.add_error('hora_fin', "La hora de fin debe ser posterior al inicio.")
            
            solapamiento = Reserva.objects.filter(
                mesa_asignada=mesa,
                fecha=fecha,
                estado__in=['CONFIRMADA', 'LLEGO']
            ).filter(
                Q(hora_inicio__lt=fin) & Q(hora_fin__gt=inicio)
            ).exclude(pk=self.instance.pk)
            if solapamiento.exists():
                self.add_error('mesa_asignada', f"La Mesa {mesa.numero} ya está reservada en ese horario.")
                
                # Sugerir mesas libres
                mesas_ocupadas_ids = Reserva.objects.filter(
                    fecha=fecha,
                    estado__in=['CONFIRMADA', 'LLEGO']
                ).filter(
                    Q(hora_inicio__lt=fin) & Q(hora_fin__gt=inicio)
                ).values_list('mesa_asignada_id', flat=True)
                mesas_libres = Mesa.objects.exclude(id__in=mesas_ocupadas_ids).filter(
                    capacidad__gte=(personas or 1)
                )[:5]
                if mesas_libres.exists():
                    sugerencias = ", ".join([str(m.numero) for m in mesas_libres])
                    self.add_error('hora_inicio', f"Conflicto de horario. Mesas disponibles: {sugerencias}")
                else:
                    self.add_error('hora_inicio', "No hay mesas disponibles en este rango horario.")

        return cleaned_data