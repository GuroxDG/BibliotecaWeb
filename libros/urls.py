# libros/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_libros, name='lista_libros'),
    path('libro/<int:libro_id>/', views.detalle_libro, name='detalle_libro'),
    
    path('nuevo/', views.LibroCreateView.as_view(), name='crear_libro'),
    path('<int:pk>/editar/', views.LibroUpdateView.as_view(), name='editar_libro'),
    path('<int:pk>/eliminar/', views.LibroDeleteView.as_view(), name='eliminar_libro'),
]