from django.db import models

class Mesas(models.Model):
    capacidad = models.IntegerField()
    estado = models.CharField(max_length=20, default="Libre")
    meseroId = models.IntegerField()

    def __str__(self):
        return f"Mesa {self.id} ({self.estado})"


class Ocupacion(models.Model):
    mesa = models.ForeignKey(Mesas, on_delete=models.CASCADE)
    clienteId = models.IntegerField()
    grupo = models.IntegerField(null=True)
    tieneReserva = models.BooleanField(default=False)
    horaAsignacion = models.DateTimeField(auto_now_add=True)
    horaSalida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ocupación {self.id} - Mesa {self.mesa_id}"
