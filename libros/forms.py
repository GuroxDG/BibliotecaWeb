# libros/forms.py
from django import forms
from .models import Libro, Autor, Categoria

class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ['titulo', 'autor', 'categorias', 'descripcion', 'precio', 
                  'stock', 'formato', 'fecha_publicacion', 'imagen']
        widgets = {
            'fecha_publicacion': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }