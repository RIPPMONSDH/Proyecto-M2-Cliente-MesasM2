from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
from datetime import datetime

# Importaciones para API REST (Integración)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import MesaSerializer, ClienteSerializer, ReservaSerializer

from .models import Cliente, Mesa, Reserva


# Endpoint: api-mesas
class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all().order_by('numero')
    serializer_class = MesaSerializer

    #  Asignar mesa (API para integración futura)
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        mesa = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado in dict(Mesa.ESTADOS):
            mesa.estado = nuevo_estado
            mesa.save()
            return Response({'status': f'Mesa {mesa.numero} ahora está {mesa.estado}'})
        return Response({'error': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer




# Vista Principal --- Plano de Mesas 
def home(request):
    mesas = Mesa.objects.all().order_by('numero')
    today = timezone.localtime(timezone.now()).date()
    now_time = timezone.localtime(timezone.now()).time()
    reservas_hoy = Reserva.objects.filter(
        fecha=today
    ).order_by('hora_inicio')

    # reservas activas en este momento (inicio <= now < fin)
    reservas_activas = reservas_hoy.filter(hora_inicio__lte=now_time, hora_fin__gt=now_time)
    
    # Métricas para el dashboard 
    libres = mesas.filter(estado='LIBRE').count()
    total = mesas.count()
    # Clientes recientes para facilitar la asignación desde el modal
    clientes_recientes = Cliente.objects.all().order_by('-id')[:20]

    # también pasar las reservas del día para mostrarlas en las tarjetas de mesa
    return render(request, 'home.html', {
        'mesas': mesas,
        'reservas': reservas_hoy,
        'reservas_activas': reservas_activas,
        'libres': libres,
        'total': total,
        'clientes': clientes_recientes,
    })
# Página de inicio (landing) con botones grandes
def inicio(request):
    """Landing inicial con botones grandes: Ver Mesas, Ver Clientes, Crear Cliente"""
    return render(request, 'inicio.html')


# Registrar Cliente 
def registrar_cliente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        notas = request.POST.get('notas')
        email = request.POST.get('email')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')

        if nombre and telefono:
            try:
                fecha_obj = None
                if fecha_nacimiento:
                    fecha_obj = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

                Cliente.objects.create(
                    nombre=nombre,
                    telefono=telefono,
                    notas=notas,
                    email=email or None,
                    fecha_nacimiento=fecha_obj,
                )
                messages.success(request, f'✅ Cliente {nombre} registrado correctamente.')
                return redirect('lista_clientes')
            except Exception as e:
                messages.error(request, f'❌ Error: El teléfono ya existe o datos inválidos.')
        else:
            messages.error(request, '❌ Nombre y Teléfono son obligatorios.')
            
    return render(request, 'registrar_cliente.html')

def lista_clientes(request):
    query = request.GET.get('q')
    if query:
        # Búsqueda parcial por nombre o teléfono 
        clientes = Cliente.objects.filter(nombre__icontains=query) | Cliente.objects.filter(telefono__icontains=query)
    else:
        clientes = Cliente.objects.all().order_by('-id')[:20]
        
    return render(request, 'lista_clientes.html', {'clientes': clientes})


# Editar Cliente
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        notas = request.POST.get('notas')
        email = request.POST.get('email')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')

        if nombre and telefono:
            try:
                fecha_obj = None
                if fecha_nacimiento:
                    fecha_obj = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

                cliente.nombre = nombre
                cliente.telefono = telefono
                cliente.notas = notas
                cliente.email = email or None
                cliente.fecha_nacimiento = fecha_obj
                cliente.save()

                messages.success(request, f'✅ Cliente {cliente.nombre} actualizado correctamente.')
                return redirect('lista_clientes')
            except Exception as e:
                messages.error(request, '❌ Error al actualizar el cliente. Verifica los datos.')
        else:
            messages.error(request, '❌ Nombre y Teléfono son obligatorios.')

    return render(request, 'registrar_cliente.html', {'cliente': cliente})


# Mostrar mesas libres para asignar a un cliente específico
def elegir_mesa_para_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    mesas_libres = Mesa.objects.filter(estado='LIBRE').order_by('numero')
    return render(request, 'elegir_mesa.html', {'cliente': cliente, 'mesas': mesas_libres})


# Asignar una mesa concreta a un cliente (accionada por POST desde la lista de mesas libres)
def asignar_cliente_mesa(request, cliente_id, mesa_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    mesa = get_object_or_404(Mesa, id=mesa_id)

    if request.method == 'POST':
        if mesa.estado != 'LIBRE':
            messages.error(request, '❌ La mesa no está libre.')
            return redirect('elegir_mesa_para_cliente', cliente_id=cliente.id)

        with transaction.atomic():
            mesa.estado = 'OCUPADA'
            mesa.save()

            # Crear una reserva mínima: fecha = hoy, hora_inicio = ahora, hora_fin = ahora + 2 horas
            inicio_dt = timezone.localtime(timezone.now())
            fin_dt = inicio_dt + timedelta(hours=2)
            Reserva.objects.create(
                cliente=cliente,
                mesa_asignada=mesa,
                fecha=inicio_dt.date(),
                hora_inicio=inicio_dt.time().replace(microsecond=0),
                hora_fin=fin_dt.time().replace(microsecond=0),
                cantidad_personas=1,
                estado='LLEGO'
            )

        messages.success(request, f' {cliente.nombre} asignado a Mesa {mesa.numero}.')
        return redirect('lista_clientes')

    return redirect('elegir_mesa_para_cliente', cliente_id=cliente.id)

# Asignar Cliente a Mesa 
def asignar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        # Puede venir de una reserva 
        if mesa.estado == 'LIBRE':
            mesa.estado = 'OCUPADA'
            mesa.save()
            
            # AQUÍ INTEGRACIÓN FUTURA (SPRINT 3):
            # Podrías llamar a la API de M3 para crear el pedido automáticamente
            # requests.post('http://api-m3/crear_pedido', data={...})
            
            messages.success(request, f' Mesa {mesa.numero} asignada. Estado: OCUPADA.')
            return redirect('home')
        else:
            messages.error(request, ' La mesa no está libre.')
            
    return render(request, 'asignar_mesa.html', {'mesa': mesa})

# Liberar Mesa 
def liberar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    if request.method == 'POST':
        if mesa.estado == 'OCUPADA':
            # Lógica de ciclo: Ocupada -> Limpieza (no se pasa automáticamente a Libre)
            mesa.estado = 'LIMPIEZA'
            mesa.save()
            messages.info(request, f'🧹 Mesa {mesa.numero} enviada a LIMPIEZA. Marca limpieza completada cuando esté lista.')
            # Desvincular reservas activas para que no aparezca el nombre del cliente
            today = timezone.localtime(timezone.now()).date()
            now_time = timezone.localtime(timezone.now()).time()
            reservas = Reserva.objects.filter(mesa_asignada=mesa, fecha=today).filter(
                Q(estado='LLEGO') | (Q(hora_inicio__lte=now_time) & Q(hora_fin__gt=now_time))
            )
            for r in reservas:
                r.mesa_asignada = None
                r.save()

        return redirect('home')
        
    return render(request, 'confirmar_liberacion.html', {'mesa': mesa})


def finalizar_limpieza(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == 'POST':
        if mesa.estado == 'LIMPIEZA':
            mesa.estado = 'LIBRE'
            mesa.save()
            messages.success(request, f'✅ Mesa {mesa.numero} ahora está LIBRE.')
            # Al finalizar limpieza también desvincular reservas activas antiguas
            today = timezone.localtime(timezone.now()).date()
            now_time = timezone.localtime(timezone.now()).time()
            reservas = Reserva.objects.filter(mesa_asignada=mesa, fecha=today).filter(
                Q(estado='LLEGO') | (Q(hora_inicio__lte=now_time) & Q(hora_fin__gt=now_time))
            )
            for r in reservas:
                r.mesa_asignada = None
                r.save()
        else:
            messages.error(request, 'La mesa no está en limpieza.')

    return redirect('home')


# Crear / Editar / Eliminar Mesas (UI básica)
def crear_mesa(request):
    if request.method == 'POST':
        numero = request.POST.get('numero')
        capacidad = request.POST.get('capacidad')
        ubicacion = request.POST.get('ubicacion')
        try:
            mesa = Mesa.objects.create(numero=int(numero), capacidad=int(capacidad), ubicacion=ubicacion)
            messages.success(request, f'✅ Mesa {mesa.numero} creada correctamente.')
            return redirect('home')
        except Exception as e:
            messages.error(request, '❌ Error al crear la mesa. Verifica los datos.')

    return render(request, 'mesa_form.html', {'mesa': None})


def editar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == 'POST':
        mesa.numero = int(request.POST.get('numero'))
        mesa.capacidad = int(request.POST.get('capacidad'))
        mesa.ubicacion = request.POST.get('ubicacion')
        mesa.save()
        messages.success(request, f'✅ Mesa {mesa.numero} actualizada.')
        return redirect('home')

    return render(request, 'mesa_form.html', {'mesa': mesa})


def eliminar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == 'POST':
        mesa.delete()
        messages.success(request, f'✅ Mesa {mesa.numero} eliminada.')
        return redirect('home')

    return render(request, 'mesa_confirm_delete.html', {'mesa': mesa})


# Cambiar estado de mesa (endpoint genérico con validación simple)
def cambiar_estado_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        estados_validos = dict(Mesa.ESTADOS).keys()
        if nuevo_estado in estados_validos:
            mesa.estado = nuevo_estado
            mesa.save()
            messages.success(request, f'✅ Mesa {mesa.numero} ahora está {mesa.get_estado_display()}.')
        else:
            messages.error(request, '❌ Estado inválido.')

    return redirect('home')


# Reservas: crear y listar con filtros
def crear_reserva(request):
    clientes = Cliente.objects.all().order_by('-id')[:50]
    mesas = Mesa.objects.all().order_by('numero')

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        fecha = request.POST.get('fecha')  # YYYY-MM-DD
        hora_inicio = request.POST.get('hora_inicio')    # HH:MM
        hora_fin = request.POST.get('hora_fin')    # HH:MM
        mesa_id = request.POST.get('mesa_id')
        cantidad = request.POST.get('cantidad') or 1
        estado = request.POST.get('estado') or 'CONFIRMADA'

        try:
            cliente = get_object_or_404(Cliente, id=int(cliente_id))
            # Parsear inicio y fin
            # Parsear fecha y horas
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            # Bloquear reservas si el cliente es menor de edad (si tenemos fecha de nacimiento)
            if cliente.fecha_nacimiento:
                edad = fecha_obj.year - cliente.fecha_nacimiento.year - ((fecha_obj.month, fecha_obj.day) < (cliente.fecha_nacimiento.month, cliente.fecha_nacimiento.day))
                if edad < 18:
                    messages.error(request, '❌ El cliente es menor de edad y no puede reservar.')
                    return render(request, 'reserva_form.html', {'clientes': clientes, 'mesas': mesas})
            hora_inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
            hora_fin_obj = datetime.strptime(hora_fin, "%H:%M").time()

            # Validaciones
            hoy = timezone.localtime(timezone.now()).date()
            if fecha_obj < hoy:
                messages.error(request, '❌ La fecha de la reserva no puede ser en el pasado.')
                return render(request, 'reserva_form.html', {'clientes': clientes, 'mesas': mesas})
            if hora_fin_obj <= hora_inicio_obj:
                messages.error(request, '❌ La hora de fin debe ser posterior a la hora de inicio.')
                return render(request, 'reserva_form.html', {'clientes': clientes, 'mesas': mesas})

            mesa_obj = None
            if mesa_id:
                mesa_obj = get_object_or_404(Mesa, id=int(mesa_id))

            Reserva.objects.create(
                cliente=cliente,
                mesa_asignada=mesa_obj,
                fecha=fecha_obj,
                hora_inicio=hora_inicio_obj,
                hora_fin=hora_fin_obj,
                cantidad_personas=int(cantidad),
                estado=estado
            )

            # Si la reserva es para HOY y se asignó una mesa libre, marcarla como RESERVADA
            if mesa_obj and fecha_obj == hoy:
                if mesa_obj.estado == 'LIBRE':
                    mesa_obj.estado = 'RESERVADA'
                    mesa_obj.save()
                    messages.info(request, f'ℹ️ Mesa {mesa_obj.numero} marcada como RESERVADA para hoy.')

            # Si la reserva indica que el cliente ya llegó, marcar la mesa como OCUPADA
            if estado == 'LLEGO' and mesa_obj:
                mesa_obj.estado = 'OCUPADA'
                mesa_obj.save()
                messages.info(request, f'ℹ️ Mesa {mesa_obj.numero} marcada como OCUPADA (cliente llegó).')

            messages.success(request, '✅ Reserva creada correctamente.')
            return redirect('listar_reservas')
        except Exception as e:
            messages.error(request, '❌ Error al crear la reserva. Revisa los datos.')

    return render(request, 'reserva_form.html', {'clientes': clientes, 'mesas': mesas})


def listar_reservas(request):
    # filtros: fecha, cliente, estado
    q_fecha = request.GET.get('fecha')
    q_cliente = request.GET.get('cliente')
    q_estado = request.GET.get('estado')

    reservas = Reserva.objects.all().order_by('-fecha', '-hora_inicio')
    if q_fecha:
        try:
            fecha_obj = datetime.strptime(q_fecha, "%Y-%m-%d").date()
            reservas = reservas.filter(fecha=fecha_obj)
        except Exception:
            pass
    else:
        # por defecto mostrar reservas del día actual
        reservas = reservas.filter(fecha=timezone.now().date())

    if q_cliente:
        reservas = reservas.filter(cliente__id=q_cliente)
    if q_estado:
        reservas = reservas.filter(estado=q_estado)

    clientes = Cliente.objects.all().order_by('nombre')[:200]

    return render(request, 'reservas_list.html', {
        'reservas': reservas,
        'clientes': clientes,
        'filtros': {'fecha': q_fecha, 'cliente': q_cliente, 'estado': q_estado}
    })