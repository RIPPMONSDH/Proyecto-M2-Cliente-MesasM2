from rest_framework import serializers
from .models import Mesa, Cliente, Reserva, HistorialOcupacion

class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class ReservaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    class Meta:
        model = Reserva
        fields = '__all__'

class HistorialOcupacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialOcupacion
        fields = '__all__'