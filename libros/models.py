# libros/models.py
from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    
class Autor(models.Model):
    nombre = models.CharField(max_length=200)
    biografia = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre

class Libro(models.Model):
    FORMATO_CHOICES = [
        ('fisico', 'Físico'),
        ('digital', 'Digital'),
    ]
    
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    categorias = models.ManyToManyField(Categoria)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES)
    fecha_publicacion = models.DateField(blank=True, null=True)
    imagen = models.ImageField(upload_to='libros/', blank=True, null=True)   
    vectorImg = models.BinaryField(blank=True, null=True) 
    
    def __str__(self):
        return self.titulo
    
    def disponible(self):
        return self.stock > 0