from rest_framework import serializers
from .models import Mesas, Ocupacion

class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesas
        fields = '__all__'


class OcupacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ocupacion
        fields = '__all__'
