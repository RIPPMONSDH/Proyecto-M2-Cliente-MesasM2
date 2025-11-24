"""
URL configuration for cliente_mesas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from MainApp import views

# Router API para que los otros módulos se conecten
router = DefaultRouter()
router.register(r'Mesa', views.MesaViewSet)     # M3 consumirá esto
router.register(r'Cliente', views.ClienteViewSet)
router.register(r'Reserva', views.ReservaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas API (Contratos JSON para M1, M3, M4)
    path('api/v1/', include(router.urls)),

    # Rutas Visuales (Para Modulo 2)
    path('', views.inicio, name='inicio'),
    path('home/', views.home, name='home'),
    path('Cliente/', views.lista_clientes, name='lista_clientes'),
    path('Cliente/nuevo/', views.registrar_cliente, name='registrar_cliente'),
    path('Cliente/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('Cliente/<int:cliente_id>/elegir_mesa/', views.elegir_mesa_para_cliente, name='elegir_mesa_para_cliente'),
    path('Cliente/<int:cliente_id>/asignar/<int:mesa_id>/', views.asignar_cliente_mesa, name='asignar_cliente_mesa'),
    path('Mesa/<int:mesa_id>/asignar/', views.asignar_mesa, name='asignar_mesa'),
    path('Mesa/<int:mesa_id>/liberar/', views.liberar_mesa, name='liberar_mesa'),
    path('Mesa/<int:mesa_id>/finalizar_limpieza/', views.finalizar_limpieza, name='finalizar_limpieza'),
    # CRUD mesas
    path('Mesa/nueva/', views.crear_mesa, name='crear_mesa'),
    path('Mesa/<int:mesa_id>/editar/', views.editar_mesa, name='editar_mesa'),
    path('Mesa/<int:mesa_id>/eliminar/', views.eliminar_mesa, name='eliminar_mesa'),
    path('Mesa/<int:mesa_id>/cambiar_estado/', views.cambiar_estado_mesa, name='cambiar_estado_mesa'),

    # Reservas
    path('Reserva/nueva/', views.crear_reserva, name='crear_reserva'),
    path('Reservas/', views.listar_reservas, name='listar_reservas'),
]
