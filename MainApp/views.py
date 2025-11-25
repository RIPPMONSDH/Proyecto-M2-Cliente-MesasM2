from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

# Imports de API
from rest_framework import viewsets
from .serializers import MesaSerializer, ClienteSerializer, ReservaSerializer, HistorialOcupacionSerializer
from .models import Cliente, Mesa, Reserva, HistorialOcupacion
from .forms import ClienteForm, MesaForm, ReservaForm

# --- API VIEWSETS (Esenciales para urls.py) ---
class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer

# --- Dashboard ---
def home(request):
    cap_min = request.GET.get('cap_min')
    estado_filtro = request.GET.get('estado')
    
    # Excluir mesas "eliminadas" (Fuera de Servicio) del plano visual
    mesas = Mesa.objects.exclude(estado='FUERA_SERVICIO').order_by('numero')
    
    if cap_min:
        mesas = mesas.filter(capacidad__gte=cap_min)
    if estado_filtro:
        mesas = mesas.filter(estado=estado_filtro)

    # Contadores
    base = Mesa.objects.exclude(estado='FUERA_SERVICIO')
    total = base.count()
    libres = base.filter(estado='LIBRE').count()
    ocupadas = base.filter(estado='OCUPADA').count()
    reservadas = base.filter(estado='RESERVADA').count()
    limpieza = base.filter(estado='LIMPIEZA').count()
    
    # Reservas Activas Ahora
    ahora = timezone.localtime(timezone.now())
    activas = Reserva.objects.filter(
        fecha=ahora.date(), estado='CONFIRMADA',
        hora_inicio__lte=ahora.time(), hora_fin__gte=ahora.time()
    )
    mapa_reservas = {r.mesa_asignada.id: r for r in activas if r.mesa_asignada}

    return render(request, 'home.html', {
        'mesas': mesas, 
        'total_mesas': total, 'mesas_libres': libres,
        'mesas_ocupadas': ocupadas, 'mesas_reservadas': reservadas,
        'mesas_limpieza': limpieza,
        'mapa_reservas': mapa_reservas, 'ahora': ahora
    })

# --- Mesas ---
def crear_mesa(request):
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mesa creada.')
            return redirect('home')
    else: form = MesaForm()
    return render(request, 'mesa_form.html', {'form': form, 'titulo': 'Crear Mesa'})

def editar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actualizada.')
            return redirect('home')
    else: form = MesaForm(instance=mesa)
    return render(request, 'mesa_form.html', {'form': form, 'titulo': 'Editar Mesa'})

def eliminar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if mesa.estado in ['OCUPADA', 'RESERVADA']:
        messages.error(request, 'No se puede eliminar una mesa activa (Ocupada/Reservada).')
        return redirect('home')
    if request.method == 'POST':
        # Soft Delete
        mesa.estado = 'FUERA_SERVICIO'
        mesa.save()
        messages.success(request, 'Mesa marcada como Fuera de Servicio.')
        return redirect('home')
    return render(request, 'mesa_confirm_delete.html', {'mesa': mesa})

# --- Reservas ---
def listar_reservas(request):
    q_fecha = request.GET.get('fecha', str(timezone.localdate()))
    reservas = Reserva.objects.filter(fecha=q_fecha).order_by('hora_inicio')
    return render(request, 'reservas_list.html', {'reservas': reservas, 'fecha_filtro': q_fecha})

def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save()
            # Simulación Notificación
            cliente = reserva.cliente
            medios = []
            if cliente.email: medios.append("Email")
            if cliente.telefono: medios.append("SMS")
            extra = f" (Notificado por {'/'.join(medios)})" if medios else ""
            
            messages.success(request, f'Reserva creada.{extra}')
            
            # Auto-reservar
            ahora = timezone.localtime(timezone.now())
            if reserva.mesa_asignada and reserva.fecha == ahora.date():
                if reserva.hora_inicio <= ahora.time() <= reserva.hora_fin:
                    if reserva.mesa_asignada.estado == 'LIBRE':
                        reserva.mesa_asignada.estado = 'RESERVADA'
                        reserva.mesa_asignada.save()
            
            return redirect('listar_reservas')
    else: form = ReservaForm()
    return render(request, 'reserva_form.html', {'form': form})

def cambiar_estado_reserva(request, reserva_id, nuevo_estado):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    mesa = reserva.mesa_asignada
    
    if nuevo_estado == 'LLEGO':
        reserva.estado = 'LLEGO'
        reserva.save()
        if mesa:
            if mesa.estado == 'FUERA_SERVICIO':
                 messages.warning(request, 'La mesa asignada está Fuera de Servicio.')
            else:
                mesa.estado = 'OCUPADA'
                mesa.ultima_asignacion = timezone.now()
                mesa.save()
                HistorialOcupacion.objects.create(
                    mesa=mesa, cliente=reserva.cliente,
                    hora_entrada=timezone.now(), cantidad_personas=reserva.cantidad_personas
                )
            messages.success(request, 'Cliente llegó.')
    
    elif nuevo_estado == 'CANCELADA':
        reserva.estado = 'CANCELADA'
        reserva.save()
        if mesa and mesa.estado == 'RESERVADA':
            mesa.estado = 'LIBRE'
            mesa.save()
            messages.info(request, 'Reserva cancelada. Mesa liberada.')

    return redirect('listar_reservas')

# --- Clientes ---
def lista_clientes(request):
    q = request.GET.get('q')
    clientes = Cliente.objects.filter(Q(nombre__icontains=q)|Q(telefono__icontains=q)) if q else Cliente.objects.all()
    return render(request, 'lista_clientes.html', {'clientes': clientes})

def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else: form = ClienteForm()
    return render(request, 'registrar_cliente.html', {'form': form})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else: form = ClienteForm(instance=cliente)
    return render(request, 'registrar_cliente.html', {'form': form, 'editing': True})

# --- Operaciones Mesa ---
def elegir_mesa_para_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    mesas_libres = Mesa.objects.filter(estado='LIBRE').order_by('numero')
    return render(request, 'elegir_mesa.html', {'cliente': cliente, 'mesas': mesas_libres})

def asignar_mesa_cliente(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        personas = int(request.POST.get('personas', 1))
        if mesa.capacidad < personas:
            messages.error(request, 'Capacidad insuficiente.')
            return redirect('home')
        
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        mesa.estado = 'OCUPADA'
        mesa.ultima_asignacion = timezone.now()
        mesa.save()
        HistorialOcupacion.objects.create(
            mesa=mesa, cliente=cliente,
            hora_entrada=timezone.now(), cantidad_personas=personas
        )
        messages.success(request, 'Mesa asignada.')
        return redirect('home')
    clientes = Cliente.objects.all()
    return render(request, 'asignar_mesa.html', {'mesa': mesa, 'clientes': clientes})

def liberar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if request.method == 'POST':
        h = HistorialOcupacion.objects.filter(mesa=mesa, hora_salida__isnull=True).last()
        if h:
            h.hora_salida = timezone.now()
            h.consumo_total = 0 
            h.save()
        mesa.estado = 'LIMPIEZA'
        mesa.save()
        return redirect('home')
    return render(request, 'confirmar_liberacion.html', {'mesa': mesa})

def finalizar_limpieza(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if request.method == 'POST':
        mesa.estado = 'LIBRE'
        mesa.save()
    return redirect('home')

# --- Reportes ---
def ver_historial_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    ocupaciones = HistorialOcupacion.objects.filter(mesa=mesa).order_by('-hora_entrada')
    total = ocupaciones.count()
    cerradas = [o for o in ocupaciones if o.hora_salida]
    
    prom_min = sum([o.duracion_minutos for o in cerradas]) / len(cerradas) if cerradas else 0
    total_consumo = sum([o.consumo_total for o in ocupaciones])
    prom_consumo = total_consumo / total if total > 0 else 0

    return render(request, 'historial_mesa.html', {
        'mesa': mesa, 'ocupaciones': ocupaciones,
        'metricas': {'rotacion': total, 'promedio': round(prom_min, 1), 'consumo_prom': round(prom_consumo, 1)}
    })

def exportar_historial_csv(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="historial_{mesa.numero}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Cliente', 'Entrada', 'Salida', 'Min', 'Pax', 'Consumo'])
    for o in HistorialOcupacion.objects.filter(mesa=mesa):
        writer.writerow([
            o.fecha, o.cliente.nombre if o.cliente else 'Walk-in',
            o.hora_entrada.strftime("%H:%M"), o.hora_salida.strftime("%H:%M") if o.hora_salida else '-',
            o.duracion_minutos, o.cantidad_personas, o.consumo_total
        ])
    return response