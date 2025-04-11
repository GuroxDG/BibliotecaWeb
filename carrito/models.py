# carrito/models.py
from decimal import Decimal
from django.db import models
from usuarios.models import Usuario
from libros.models import Libro
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Carrito(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Carrito de {self.usuario.email}"
    
    def obtener_total(self):
        return sum(item.obtener_subtotal() for item in self.items.all())
    
    def aplicar_cupon(self, cupon):
        if cupon.es_valido():
            return self.obtener_total() * (1 - Decimal(str(cupon.descuento)) / 100)
        return self.obtener_total()

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('carrito', 'libro')
    
    def __str__(self):
        return f"{self.cantidad} x {self.libro.titulo}"
    
    def obtener_subtotal(self):
        return self.libro.precio * self.cantidad

@receiver(pre_save, sender=ItemCarrito)
def verificar_stock(sender, instance, **kwargs):
    if instance.cantidad > instance.libro.stock:
        raise ValueError(f"No hay suficiente stock para {instance.libro.titulo}")