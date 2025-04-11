# pedidos/models.py
from django.db import models
from usuarios.models import Usuario
from libros.models import Libro
import uuid

class Cupon(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descuento = models.IntegerField(help_text="Porcentaje de descuento")
    fecha_inicio = models.DateTimeField()
    fecha_expiracion = models.DateTimeField()
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} ({self.descuento}%)"
    
    def es_valido(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.activo and 
                self.fecha_inicio <= now and 
                self.fecha_expiracion >= now)

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero_orden = models.CharField(max_length=10, unique=True, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    cupon = models.ForeignKey(Cupon, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pedido #{self.numero_orden}"
    
    def save(self, *args, **kwargs):
        if not self.numero_orden:
            # Generar número de orden único
            self.numero_orden = str(uuid.uuid4()).upper()[:10]
        super().save(*args, **kwargs)

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.cantidad} x {self.libro.titulo}"
    
    def subtotal(self):
        return self.precio_unitario * self.cantidad