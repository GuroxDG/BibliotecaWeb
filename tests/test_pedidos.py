import pytest
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from unittest.mock import patch
from pedidos.models import Cupon, Pedido, DetallePedido
from usuarios.models import Usuario
from libros.models import Libro

@pytest.mark.django_db
class TestCupon:
    def test_creacion_cupon(self):
        """Test para verificar la creación de un cupón"""
        now = timezone.now()
        cupon = Cupon.objects.create(
            codigo="TEST20",
            descuento=20,
            fecha_inicio=now,
            fecha_expiracion=now + timedelta(days=7),
            activo=True
        )
        
        assert cupon.codigo == "TEST20"
        assert cupon.descuento == 20
        assert cupon.activo is True
        assert str(cupon) == "TEST20 (20%)"
    
    def test_cupon_valido(self):
        """Test para verificar que un cupón sea válido"""
        now = timezone.now()
        cupon = Cupon.objects.create(
            codigo="VALID10",
            descuento=10,
            fecha_inicio=now - timedelta(days=1),
            fecha_expiracion=now + timedelta(days=1),
            activo=True
        )
        
        assert cupon.es_valido() is True
    
    def test_cupon_expirado(self):
        """Test para verificar que un cupón expirado no sea válido"""
        now = timezone.now()
        cupon = Cupon.objects.create(
            codigo="EXPIRED10",
            descuento=10,
            fecha_inicio=now - timedelta(days=2),
            fecha_expiracion=now - timedelta(days=1),
            activo=True
        )
        
        assert cupon.es_valido() is False
    
    def test_cupon_inactivo(self):
        """Test para verificar que un cupón inactivo no sea válido"""
        now = timezone.now()
        cupon = Cupon.objects.create(
            codigo="INACTIVE10",
            descuento=10,
            fecha_inicio=now - timedelta(days=1),
            fecha_expiracion=now + timedelta(days=1),
            activo=False
        )
        
        assert cupon.es_valido() is False

@pytest.mark.django_db
class TestPedido:
    @pytest.fixture
    def usuario(self):
        """Fixture para crear un usuario de prueba"""
        return Usuario.objects.create(
            username="testuser",
            email="test@example.com"
        )
        
    @pytest.fixture
    def cupon_valido(self):
        """Fixture para crear un cupón válido de prueba"""
        now = timezone.now()
        return Cupon.objects.create(
            codigo="VALID20",
            descuento=20,
            fecha_inicio=now - timedelta(days=1),
            fecha_expiracion=now + timedelta(days=1),
            activo=True
        )
    
    def test_creacion_pedido(self, usuario):
        """Test para verificar la creación de un pedido"""
        pedido = Pedido.objects.create(
            usuario=usuario,
            total=Decimal('100.00'),
            direccion_envio="Calle Prueba 123"
        )
        
        assert pedido.usuario == usuario
        assert pedido.total == Decimal('100.00')
        assert pedido.estado == 'pendiente'
        assert pedido.numero_orden is not None
        assert len(pedido.numero_orden) == 10
        assert str(pedido) == f"Pedido #{pedido.numero_orden}"
    
    def test_pedido_con_cupon(self, usuario, cupon_valido):
        """Test para verificar la creación de un pedido con cupón"""
        pedido = Pedido.objects.create(
            usuario=usuario,
            cupon=cupon_valido,
            total=Decimal('80.00'),
            direccion_envio="Calle Prueba 123"
        )
        
        assert pedido.cupon == cupon_valido
        assert pedido.total == Decimal('80.00')
    
    @patch('uuid.uuid4')
    def test_generacion_numero_orden(self, mock_uuid, usuario):
        """Test para verificar que se genera un número de orden único"""
        mock_uuid.return_value = "123e4567-e89b-12d3-a456-426614174000"
        
        pedido = Pedido.objects.create(
            usuario=usuario,
            total=Decimal('100.00'),
        )
        
        assert pedido.numero_orden == "123E4567-E"

@pytest.mark.django_db
class TestDetallePedido:
    @pytest.fixture
    def usuario(self):
        """Fixture para crear un usuario de prueba"""
        return Usuario.objects.create(
            username="testuser",
            email="test@example.com"
        )
    
    @pytest.fixture
    def libro(self):
        """Fixture para crear un libro de prueba"""
        return Libro.objects.create(
            titulo="Libro de prueba",
            precio=Decimal('25.99'),
            stock=10
        )
    
    @pytest.fixture
    def pedido(self, usuario):
        """Fixture para crear un pedido de prueba"""
        return Pedido.objects.create(
            usuario=usuario,
            total=Decimal('25.99'),
            direccion_envio="Calle Prueba 123"
        )