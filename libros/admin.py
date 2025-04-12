from django.contrib import admin

# Register your models here.
from .models import Libro, Autor, Categoria

admin.site.register(Libro)
admin.site.register(Autor)
admin.site.register(Categoria)