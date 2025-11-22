from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Cliente, Reserva

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'fecha_creacion')
    search_fields = ('nombre', 'email')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha_reserva', 'hora_reserva', 'creado_en')
    list_filter = ('fecha_reserva',)
    search_fields = ('cliente__nombre', 'cliente__email')
