from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cliente, Reserva
from .forms import ClienteForm, ReservaForm


def home_page(request):
    """Página de inicio con acceso a Reservas y Clientes."""
    return render(request, "home.html", {})


# RESERVAS 
def reservas_page(request, pk=None, delete_id=None):
    reservas = Reserva.objects.select_related('cliente').order_by('-fecha_reserva', '-hora_reserva')

    # EDITAR
    if pk:
        reserva = get_object_or_404(Reserva, pk=pk)
        form = ReservaForm(request.POST or None, instance=reserva)
        editing = True
    else:
        reserva = None
        form = ReservaForm(request.POST or None)
        editing = False

    # ELIMINAR
    if delete_id:
        reserva = get_object_or_404(Reserva, pk=delete_id)
        reserva.delete()
        messages.success(request, "Reserva eliminada correctamente.")
        return redirect('reservas')

    # GUARDAR
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if editing:
                messages.success(request, "Reserva actualizada correctamente.")
            else:
                messages.success(request, "Reserva creada correctamente.")
            return redirect('reservas')
        else:
            messages.error(request, "Error al guardar. Revisa los campos.")

    return render(request, "reserva_page.html", {
        "reservas": reservas,
        "form": form,
        "editing": editing,
    })


# CLIENTES
def clientes_page(request, pk=None, delete_id=None):
    clientes = Cliente.objects.order_by('-fecha_creacion')

    if pk:
        cliente = get_object_or_404(Cliente, pk=pk)
        form = ClienteForm(request.POST or None, instance=cliente)
        editing = True
    else:
        cliente = None
        form = ClienteForm(request.POST or None)
        editing = False

    if delete_id:
        cliente = get_object_or_404(Cliente, pk=delete_id)
        cliente.delete()
        messages.success(request, "Cliente eliminado correctamente.")
        return redirect('clientes')

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if editing:
                messages.success(request, "Cliente actualizado correctamente.")
            else:
                messages.success(request, "Cliente creado correctamente.")
            return redirect('clientes')
        else:
            messages.error(request, "Error al guardar los datos.")

    return render(request, "cliente_page.html", {
        "clientes": clientes,
        "form": form,
        "editing": editing,
    })
