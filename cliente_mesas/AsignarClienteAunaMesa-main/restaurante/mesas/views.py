from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Mesas, Ocupacion
from django.utils import timezone


@api_view(['GET'])
def obtener_mesas(request):
    mesas = Mesas.objects.all()
    data = [
        {
            "id": m.id,
            "capacidad": m.capacidad,
            "estado": m.estado,
            "meseroId": m.meseroId
        } for m in mesas
    ]
    return Response(data)


@api_view(['POST'])
def asignar_mesa(request):
    mesaId = request.data.get("mesaId")
    clienteId = request.data.get("clienteId")
    grupo = request.data.get("grupo")
    tieneReserva = request.data.get("tieneReserva", False)

    try:
        mesa = Mesas.objects.get(id=mesaId)
    except Mesas.DoesNotExist:
        return Response({"error": "Mesa no encontrada"}, status=404)

    # ❗ Validar si la mesa ya está ocupada
    if mesa.estado == "Ocupada":
        return Response({"error": "La mesa ya está ocupada"}, status=400)

    # ❗ Validar capacidad
    if grupo > mesa.capacidad:
        return Response({"error": "El grupo supera la capacidad de la mesa"}, status=400)

    # Crear registro de ocupación
    Ocupacion.objects.create(
        mesa=mesa,
        clienteId=clienteId,
        grupo=grupo,
        tieneReserva=tieneReserva
    )

    # Actualizar estado de la mesa
    mesa.estado = "Ocupada"
    mesa.save()

    return Response({"mensaje": "Mesa asignada correctamente"})


@api_view(['POST'])
def liberar_mesa(request):
    mesaId = request.data.get("mesaId")

    try:
        mesa = Mesas.objects.get(id=mesaId)
    except Mesas.DoesNotExist:
        return Response({"error": "Mesa no encontrada"}, status=404)

    # Buscar ocupación activa
    try:
        ocupacion = Ocupacion.objects.get(mesa=mesa, horaSalida__isnull=True)
    except Ocupacion.DoesNotExist:
        return Response({"error": "La mesa no tiene ocupaciones activas"}, status=400)

    # Registrar salida
    ocupacion.horaSalida = timezone.now()
    ocupacion.save()

    # Cambiar estado de mesa
    mesa.estado = "Libre"
    mesa.save()

    return Response({"mensaje": "Mesa liberada correctamente"})


@api_view(['GET'])
def ocupaciones_activas(request):
    activas = Ocupacion.objects.filter(horaSalida__isnull=True)

    data = [
        {
            "id": o.id,
            "mesaId": o.mesa.id,
            "clienteId": o.clienteId,
            "grupo": o.grupo,
            "tieneReserva": o.tieneReserva,
            "horaAsignacion": o.horaAsignacion
        } for o in activas
    ]

    return Response(data)
