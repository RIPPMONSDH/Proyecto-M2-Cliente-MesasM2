from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from MainApp import views

router = routers.DefaultRouter()
router.register(r'mesas', views.MesaViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'reservas', views.ReservaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),

    path('', views.home, name='home'),
    path('mesa/nueva/', views.crear_mesa, name='crear_mesa'),
    path('mesa/<int:mesa_id>/editar/', views.editar_mesa, name='editar_mesa'),
    path('mesa/<int:mesa_id>/eliminar/', views.eliminar_mesa, name='eliminar_mesa'),
    path('mesa/<int:mesa_id>/asignar/', views.asignar_mesa_cliente, name='asignar_mesa_cliente'),
    path('mesa/<int:mesa_id>/liberar/', views.liberar_mesa, name='liberar_mesa'),
    path('mesa/<int:mesa_id>/limpieza-fin/', views.finalizar_limpieza, name='finalizar_limpieza'),
    
    path('mesa/<int:mesa_id>/historial/', views.ver_historial_mesa, name='ver_historial_mesa'),
    path('mesa/<int:mesa_id>/exportar/', views.exportar_historial_csv, name='exportar_historial_csv'),

    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.registrar_cliente, name='registrar_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/elegir-mesa/', views.elegir_mesa_para_cliente, name='elegir_mesa_para_cliente'),

    path('reservas/', views.listar_reservas, name='listar_reservas'),
    path('reservas/nueva/', views.crear_reserva, name='crear_reserva'),
    path('reservas/<int:reserva_id>/estado/<str:nuevo_estado>/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
]