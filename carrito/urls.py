# carrito/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:libro_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar/<int:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('aplicar-cupon/', views.aplicar_cupon, name='aplicar_cupon'),
]