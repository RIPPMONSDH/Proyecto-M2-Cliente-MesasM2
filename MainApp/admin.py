from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, Mesa, Reserva, HistorialOcupacion

# --- CLIENTES ---
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'preferencias', 'fecha_creacion')
    list_filter = ('preferencias', 'fecha_creacion')
    search_fields = ('nombre', 'telefono', 'email')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'telefono', 'email', 'fecha_nacimiento')
        }),
        ('Preferencias', {
            'fields': ('preferencias', 'detalle_preferencia', 'notas')
        }),
    )

# --- MESAS ---
@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'capacidad', 'ubicacion', 'estado', 'ultima_asignacion')
    list_filter = ('estado', 'ubicacion', 'capacidad')
    search_fields = ('numero',)
    ordering = ('numero',)
    list_editable = ('estado',) 
    def estado_color(self, obj):
        colors = {
            'LIBRE': 'green',
            'OCUPADA': 'red',
            'RESERVADA': 'orange',
            'LIMPIEZA': 'blue',
            'FUERA_SERVICIO': 'gray',
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_color.short_description = 'Estado'

# --- RESERVAS ---
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'hora_inicio', 'mesa_asignada', 'estado_badge', 'is_late_alert')
    list_filter = ('estado', 'fecha', 'mesa_asignada')
    search_fields = ('cliente__nombre', 'cliente__telefono')
    date_hierarchy = 'fecha'
    ordering = ('-fecha', 'hora_inicio')
    autocomplete_fields = ['cliente', 'mesa_asignada'] 

    def estado_badge(self, obj):
        colors = {
            'CONFIRMADA': 'green',
            'LLEGO': 'blue',
            'CANCELADA': 'gray',
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def is_late_alert(self, obj):
        return "⚠️ RETRASO" if obj.is_late else "-"
    is_late_alert.short_description = 'Alerta'

# --- HISTORIAL ---
@admin.register(HistorialOcupacion)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ('mesa', 'cliente', 'fecha', 'hora_entrada', 'hora_salida', 'duracion_display', 'consumo_total')
    list_filter = ('fecha', 'mesa')
    readonly_fields = ('duracion_minutos',) 
    def duracion_display(self, obj):
        return f"{obj.duracion_minutos} min"
    duracion_display.short_description = 'Duración'