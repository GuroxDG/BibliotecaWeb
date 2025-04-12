import pytest
from decimal import Decimal
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import IntegrityError
from django.utils import timezone
from usuarios.models import Usuario
from libros.models import Libro, Autor, Categoria
from carrito.models import Carrito, ItemCarrito, verificar_stock
from pedidos.models import Cupon

@pytest.mark.django_db
class TestCarritoModel:
    @pytest.fixture
    def setup_usuario(self):
        return Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def setup_libro(self):
        autor = Autor.objects.create(nombre="Autor Test")
        categoria = Categoria.objects.create(nombre="Categoría Test")
        libro = Libro.objects.create(
            titulo="Libro de prueba",
            autor=autor,
            descripcion="Descripción de prueba",
            precio=Decimal('25.99'),
            stock=10,
            formato="fisico"
        )
        libro.categorias.add(categoria)
        return libro
    
    @pytest.fixture
    def setup_carrito(self, setup_usuario):
        return Carrito.objects.create(usuario=setup_usuario)
    
    def test_crear_carrito(self, setup_usuario):
        carrito = Carrito.objects.create(usuario=setup_usuario)
        assert carrito.usuario.email == "test@example.com"
        assert carrito.items.count() == 0
    
    def test_str_representation(self, setup_carrito):
        assert str(setup_carrito) == "Carrito de test@example.com"
    
    def test_obtener_total_sin_items(self, setup_carrito):
        assert setup_carrito.obtener_total() == 0
    
    def test_obtener_total_con_items(self, setup_carrito, setup_libro):
        # Agregar un item al carrito
        ItemCarrito.objects.create(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=2
        )
        
        # El total debe ser precio * cantidad
        assert setup_carrito.obtener_total() == Decimal('51.98')  # 25.99 * 2
 
    

@pytest.mark.django_db
class TestItemCarritoModel:
    @pytest.fixture
    def setup_usuario(self):
        return Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def setup_libro(self):
        autor = Autor.objects.create(nombre="Autor Test")
        libro = Libro.objects.create(
            titulo="Libro de prueba",
            autor=autor,
            descripcion="Descripción de prueba",
            precio=Decimal('15.50'),
            stock=8,
            formato="fisico"
        )
        return libro
    
    @pytest.fixture
    def setup_carrito(self, setup_usuario):
        return Carrito.objects.create(usuario=setup_usuario)
    
    def test_crear_item_carrito(self, setup_carrito, setup_libro):
        item = ItemCarrito.objects.create(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=3
        )
        assert item.carrito == setup_carrito
        assert item.libro == setup_libro
        assert item.cantidad == 3
    
    def test_str_representation(self, setup_carrito, setup_libro):
        item = ItemCarrito.objects.create(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=2
        )
        assert str(item) == "2 x Libro de prueba"
    
    def test_obtener_subtotal(self, setup_carrito, setup_libro):
        item = ItemCarrito.objects.create(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=4
        )
        assert item.obtener_subtotal() == Decimal('62.00')  # 15.50 * 4
    
    def test_unique_together_constraint(self, setup_carrito, setup_libro):
        # Crear un item
        ItemCarrito.objects.create(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=1
        )
        
        # Intentar crear otro item con el mismo carrito y libro
        with pytest.raises(IntegrityError):
            ItemCarrito.objects.create(
                carrito=setup_carrito,
                libro=setup_libro,
                cantidad=2
            )
    
    def test_verificar_stock_signal(self, setup_carrito, setup_libro):
        # El libro tiene stock=8, así que esto debería funcionar
        item = ItemCarrito(
            carrito=setup_carrito,
            libro=setup_libro,
            cantidad=5
        )
        item.save()  # No debería lanzar error
        
        # Intentar guardar con una cantidad mayor al stock
        item.cantidad = 10  # Esto excede el stock de 8
        with pytest.raises(ValueError):
            item.save()