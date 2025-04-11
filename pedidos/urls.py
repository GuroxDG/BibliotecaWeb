
# pedidos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('procesar/', views.procesar_pedido, name='procesar_pedido'),
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('detalle/<str:numero_orden>/', views.detalle_pedido, name='detalle_pedido'),
    
    path('pedidos/', views.listar_pedidos, name='listar_pedidos'),
    path('pedidos/<int:pedido_id>/actualizar/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
]