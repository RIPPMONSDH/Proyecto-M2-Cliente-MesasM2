from django.urls import path
from . import views

urlpatterns = [
    path('', views.obtener_mesas),                         # /api/mesas/
    path('asignar/', views.asignar_mesa),                  # /api/mesas/asignar/
    path('liberar/', views.liberar_mesa),                  # /api/mesas/liberar/
    path('ocupaciones/activas/', views.ocupaciones_activas),  # /api/mesas/ocupaciones/activas/
]

