import pytest
from decimal import Decimal
from carrito.models import Carrito, ItemCarrito
from libros.models import Autor, Libro
from pedidos.models import Cupon
from usuarios.models import Usuario
from unittest.mock import MagicMock
from django.core.exceptions import ObjectDoesNotExist

pytestmark = pytest.mark.django_db

def test_agregar_item_con_stock(db):
    autor = Autor.objects.create(nombre="Autor de prueba")
    usuario = Usuario.objects.create_user(email="test@mail.com", password="testpass123")
    
    libro = Libro.objects.create(
        titulo="Django 101",
        stock=5,
        precio=Decimal("100.00"),
        autor=autor  # ← este es el fix
    )
    
    carrito = Carrito.objects.create(usuario=usuario)
    item = ItemCarrito.objects.create(carrito=carrito, libro=libro, cantidad=1)
    
    assert item.obtener_subtotal() == Decimal("100.00")

def test_error_si_no_hay_stock():
    usuario = Usuario.objects.create(email="test@mail.com", password="testpass123")
    libro = Libro.objects.create(titulo="Python Crash", stock=1, precio=Decimal("50.00"))
    carrito = Carrito.objects.create(usuario=usuario)

    with pytest.raises(ValueError) as exc:
        ItemCarrito.objects.create(carrito=carrito, libro=libro, cantidad=2)

    assert "No hay suficiente stock" in str(exc.value)

def test_total_del_carrito():
    usuario = Usuario.objects.create(email="cliente@mail.com", password="12345678")
    libro1 = Libro.objects.create(titulo="Libro 1", stock=10, precio=Decimal("80.00"))
    libro2 = Libro.objects.create(titulo="Libro 2", stock=10, precio=Decimal("120.00"))
    carrito = Carrito.objects.create(usuario=usuario)

    ItemCarrito.objects.create(carrito=carrito, libro=libro1, cantidad=1)
    ItemCarrito.objects.create(carrito=carrito, libro=libro2, cantidad=2)

    assert carrito.obtener_total() == Decimal("320.00")

def test_aplicar_cupon_valido(mocker):
    usuario = Usuario.objects.create(email="cupon@mail.com", password="testpass")
    carrito = Carrito.objects.create(usuario=usuario)
    libro = Libro.objects.create(titulo="Libro Cupón", stock=5, precio=Decimal("200.00"))
    ItemCarrito.objects.create(carrito=carrito, libro=libro, cantidad=1)

    cupon = MagicMock()
    cupon.es_valido.return_value = True
    cupon.descuento = 25

    total_con_descuento = carrito.aplicar_cupon(cupon)

    assert total_con_descuento == Decimal("150.00")

def test_aplicar_cupon_invalido(mocker):
    usuario = Usuario.objects.create(email="nocupon@mail.com", password="testpass")
    carrito = Carrito.objects.create(usuario=usuario)
    libro = Libro.objects.create(titulo="Libro", stock=5, precio=Decimal("100.00"))
    ItemCarrito.objects.create(carrito=carrito, libro=libro, cantidad=2)

    cupon = MagicMock()
    cupon.es_valido.return_value = False
    cupon.descuento = 50  # No debe importar

    total_sin_descuento = carrito.aplicar_cupon(cupon)

    assert total_sin_descuento == Decimal("200.00")

def test_incrementar_cantidad_si_libro_ya_existe():
    usuario = Usuario.objects.create(email="usuario@mail.com", password="12345678")
    libro = Libro.objects.create(titulo="Libro repetido", stock=3, precio=Decimal("75.00"))
    carrito = Carrito.objects.create(usuario=usuario)

    item = ItemCarrito.objects.create(carrito=carrito, libro=libro, cantidad=1)

    # Simula lógica de la vista
    if item.cantidad + 1 <= libro.stock:
        item.cantidad += 1
        item.save()

    assert item.cantidad == 2
