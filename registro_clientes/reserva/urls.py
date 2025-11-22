from django.urls import path
from .views import reservas_page, clientes_page, home_page

urlpatterns = [
    path('', home_page, name='home'),

    # RESERVAS
    path('reservas/', reservas_page, name='reservas'),
    path('reservas/editar/<int:pk>/', reservas_page, name='editar_reserva'),
    path('reservas/eliminar/<int:delete_id>/', reservas_page, name='eliminar_reserva'),

    # CLIENTES
    path('clientes/', clientes_page, name='clientes'),
    path('clientes/editar/<int:pk>/', clientes_page, name='editar_cliente'),
    path('clientes/eliminar/<int:delete_id>/', clientes_page, name='eliminar_cliente'),
]
