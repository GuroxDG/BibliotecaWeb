# libros/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Libro, Categoria, Autor
from django.db.models import Q

@login_required
def lista_libros(request):
    categorias = Categoria.objects.all()
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    formato = request.GET.get('formato')
    busqueda = request.GET.get('busqueda')
    
    libros = Libro.objects.all()
    
    # Aplicar filtros
    if categoria_id:
        libros = libros.filter(categorias__id=categoria_id)
    
    if formato:
        libros = libros.filter(formato=formato)
    
    if busqueda:
        libros = libros.filter(
            Q(titulo__icontains=busqueda) | 
            Q(autor__nombre__icontains=busqueda)
        )
    
    return render(request, 'libros/lista_libros.html', {
        'libros': libros,
        'categorias': categorias
    })

@login_required
def detalle_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    libros_relacionados = Libro.objects.filter(categorias__in=libro.categorias.all()).exclude(id=libro.id).distinct()[:4]
    
    return render(request, 'libros/detalle_libro.html', {
        'libro': libro,
        'libros_relacionados': libros_relacionados
    })
    
# libros/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .models import Libro
from .forms import LibroForm

# Asumo que ya tienes estas vistas
class LibroListView(ListView):
    model = Libro
    template_name = 'libros/lista_libros.html'
    context_object_name = 'libros'

class LibroDetailView(DetailView):
    model = Libro
    template_name = 'libros/detalle_libro.html'
    context_object_name = 'libro'

# Nuevas vistas CRUD
class LibroCreateView(CreateView):
    model = Libro
    form_class = LibroForm
    template_name = 'libros/libro_form.html'
    success_url = reverse_lazy('lista_libros')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Nuevo Libro'
        return context

class LibroUpdateView(UpdateView):
    model = Libro
    form_class = LibroForm
    template_name = 'libros/libro_form.html'
    success_url = reverse_lazy('lista_libros')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Libro'
        return context

class LibroDeleteView(DeleteView):
    model = Libro
    template_name = 'libros/libro_confirm_delete.html'
    success_url = reverse_lazy('lista_libros')