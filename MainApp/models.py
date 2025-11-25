from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from datetime import timedelta, datetime

class Cliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    telefono = PhoneNumberField(unique=True, verbose_name="Teléfono", help_text="Ej: +56912345678")
    email = models.EmailField(null=True, blank=True, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    PREFERENCIAS_CHOICES = [
        ('NINGUNA', 'Ninguna'),
        ('VEGETARIANO', 'Vegetariano'),
        ('VEGANO', 'Vegano'),
        ('CELIACO', 'Celíaco'),
        ('OTRO', 'Otro'),
    ]
    preferencias = models.CharField(max_length=20, choices=PREFERENCIAS_CHOICES, default='NINGUNA')
    detalle_preferencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Detalle (Si es 'Otro')")
    notas = models.TextField(blank=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.telefono})"

class Mesa(models.Model):
    ESTADOS = [
        ('LIBRE', 'Libre'),       
        ('OCUPADA', 'Ocupada'),
        ('RESERVADA', 'Reservada'),
        ('LIMPIEZA', 'En Limpieza'),
        ('FUERA_SERVICIO', 'Fuera de Servicio'), 
    ]
    
    UBICACION_CHOICES = [
        ('SALA', 'Sala Principal'),
        ('TERRAZA', 'Terraza'),
        ('PRIVADO', 'Privado'),
    ]
    
    numero = models.IntegerField(unique=True, verbose_name="Número de Mesa") 
    capacidad = models.PositiveIntegerField(verbose_name="Capacidad Personas")
    ubicacion = models.CharField(max_length=20, choices=UBICACION_CHOICES, default='SALA', verbose_name="Ubicación")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='LIBRE')

    ultima_asignacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Mesa {self.numero} (Cap: {self.capacidad}) - {self.get_ubicacion_display()}"

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('CONFIRMADA', 'Confirmada'), 
        ('LLEGO', 'Cliente Llegó'),   
        ('CANCELADA', 'Cancelada'),   
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    mesa_asignada = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateField(default=timezone.localdate)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cantidad_personas = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='CONFIRMADA')
    notas = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    @property
    def is_late(self):
        now = timezone.localtime(timezone.now())
        if self.fecha == now.date() and self.estado == 'CONFIRMADA':
            inicio_dt = datetime.combine(self.fecha, self.hora_inicio)
            inicio_dt = timezone.make_aware(inicio_dt)
            if now > (inicio_dt + timedelta(minutes=15)):
                return True
        return False

    def __str__(self):
        return f"Reserva {self.id} - {self.cliente.nombre}"

class HistorialOcupacion(models.Model):
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.DateTimeField()
    hora_salida = models.DateTimeField(null=True, blank=True)
    cantidad_personas = models.IntegerField(default=1)
    consumo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @property
    def duracion_minutos(self):
        if self.hora_salida and self.hora_entrada:
            delta = self.hora_salida - self.hora_entrada
            return int(delta.total_seconds() / 60)
        return 0