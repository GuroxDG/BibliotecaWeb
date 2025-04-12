import pytest
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from pedidos.models import Pedido, DetallePedido, Cupon
from pedidos.views import confirmar_pedido, procesar_pedido, historial_pedidos, detalle_pedido, listar_pedidos, actualizar_estado_pedido
from carrito.models import Carrito, ItemCarrito
from usuarios.models import Usuario
from libros.models import Libro, Autor

@pytest.mark.django_db
class TestVistasPedidos:
    @pytest.fixture
    def usuario(self):
        """Fixture para crear un usuario de prueba"""
        return Usuario.objects.create(
            username="testuser",
            email="test@example.com"
        )
    
    @pytest.fixture
    def usuario_admin(self):
        """Fixture para crear un usuario administrador"""
        return Usuario.objects.create(
            username="admin",
            email="admin@example.com",
            is_superuser=True
        )
    
    @pytest.fixture
    def libro(self):
        """Fixture para crear un libro de prueba"""
        autor = Autor.objects.create(nombre="Autor de prueba")
        return Libro.objects.create(
            titulo="Libro de prueba",
            precio=Decimal('25.99'),
            stock=10,
            autor=autor,  # Asigna el autor creado
        )
    
    @pytest.fixture
    def cupon_valido(self):
        """Fixture para crear un cupón válido"""
        now = timezone.now()
        return Cupon.objects.create(
            codigo="VALID20",
            descuento=20,
            fecha_inicio=now - timedelta(days=1),
            fecha_expiracion=now + timedelta(days=1),
            activo=True
        )
    
    @pytest.fixture
    def carrito_con_items(self, usuario, libro):
        """Fixture para crear un carrito con items"""
        carrito = Carrito.objects.create(usuario=usuario)
        ItemCarrito.objects.create(
            carrito=carrito,
            libro=libro,
            cantidad=2
        )
        return carrito
    
    @pytest.fixture
    def factory(self):
        """Fixture para crear un RequestFactory"""
        return RequestFactory()
    
    @pytest.fixture
    def session(self):
        """Fixture para simular una sesión"""
        return {}
    
    def setup_request(self, request, user, session=None):
        """Configura el request con usuario y sesión"""
        request.user = user
        request.session = session or {}
        
        # Configurar messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_confirmar_pedido_carrito_vacio(self, factory, usuario):
        """Test para confirmar_pedido con carrito vacío"""
        request = factory.get(reverse('confirmar_pedido'))
        request = self.setup_request(request, usuario)
        
        # Crear carrito vacío
        Carrito.objects.create(usuario=usuario)
        
        response = confirmar_pedido(request)
        
        assert response.status_code == 302
        assert response.url == reverse('ver_carrito')
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "Tu carrito está vacío" in str(messages[0])
    
    def test_confirmar_pedido_con_items(self, factory, usuario, carrito_con_items):
        """Test para confirmar_pedido con items en el carrito"""
        request = factory.get(reverse('confirmar_pedido'))
        request = self.setup_request(request, usuario)

        with patch('carrito.models.Carrito.obtener_total', return_value=Decimal('51.98')):
            response = confirmar_pedido(request)

        assert response.status_code == 200
        # Aquí podrías verificar el contenido de la respuesta en lugar de context_data
        assert 'carrito' in response.content.decode()  # O cualquier otra verificación que sea relevante

    @patch('pedidos.views.enviarCorreo')
    def test_procesar_pedido_exitoso(self, mock_enviar_correo, factory, usuario, libro, carrito_con_items):
        """Test para procesar_pedido exitoso"""
        # Configurar request
        request = factory.post(reverse('procesar_pedido'), {'direccion': 'Calle Prueba 123'})
        request = self.setup_request(request, usuario)
        
        # Mockear métodos del carrito
        with patch('carrito.models.Carrito.obtener_total', return_value=Decimal('51.98')):
            response = procesar_pedido(request)
        
        # Verificar resultados
        assert response.status_code == 302
        assert response.url == reverse('historial_pedidos')
        
        # Verificar que se creó el pedido
        assert Pedido.objects.filter(usuario=usuario).exists()
        pedido = Pedido.objects.get(usuario=usuario)
        assert pedido.total == Decimal('51.98')
        assert pedido.direccion_envio == 'Calle Prueba 123'
        
        # Verificar que se creó el detalle del pedido
        assert DetallePedido.objects.filter(pedido=pedido).exists()
        detalle = DetallePedido.objects.get(pedido=pedido)
        assert detalle.libro == libro
        assert detalle.cantidad == 2
        
        # Verificar que se actualizó el stock
        libro.refresh_from_db()
        assert libro.stock == 8
        
        # Verificar que se envió el correo
        mock_enviar_correo.assert_called_once()
        
        # Verificar mensajes
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert f"¡Pedido #{pedido.numero_orden} completado con éxito!" in str(messages[0])
    
    def test_procesar_pedido_stock_insuficiente(self, factory, usuario, libro, carrito_con_items):
        """Test para procesar_pedido con stock insuficiente"""
        # Reducir el stock del libro
        libro.stock = 1
        libro.save()
        
        # Configurar request
        request = factory.post(reverse('procesar_pedido'), {'direccion': 'Calle Prueba 123'})
        request = self.setup_request(request, usuario)
        
        # Mockear métodos del carrito
        with patch('carrito.models.Carrito.obtener_total', return_value=Decimal('51.98')):
            response = procesar_pedido(request)
        
        # Verificar resultados
        assert response.status_code == 302
        assert response.url == reverse('ver_carrito')
        
        # Verificar que no se creó el pedido
        assert not Pedido.objects.filter(usuario=usuario).exists()
        
        # Verificar mensajes
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "No hay suficiente stock" in str(messages[0])
    
    def test_detalle_pedido(self, factory, usuario, libro):
        """Test para detalle_pedido"""
        # Crear un pedido con detalle
        pedido = Pedido.objects.create(usuario=usuario, total=Decimal('100.00'))
        DetallePedido.objects.create(
            pedido=pedido,
            libro=libro,
            cantidad=2,
            precio_unitario=libro.precio
        )

        # Configurar request
        request = factory.get(reverse('detalle_pedido', kwargs={'numero_orden': pedido.numero_orden}))
        request = self.setup_request(request, usuario)

        # Llamar a la vista
        response = detalle_pedido(request, pedido.numero_orden)

        # Verificar resultados
        assert response.status_code == 200
        # Aquí podrías verificar el contenido de la respuesta en lugar de context_data
        assert 'pedido' in response.content.decode()  # O cualquier otra verificación que sea relevante
        assert str(pedido.numero_orden) in response.content.decode()  # Verifica que el número de orden esté presente
    
    def test_actualizar_estado_pedido(self, factory, usuario_admin):
        """Test para actualizar_estado_pedido"""
        # Crear un pedido
        pedido = Pedido.objects.create(usuario=usuario_admin, total=Decimal('100.00'))
        
        # Configurar request
        request = factory.post(reverse('actualizar_estado_pedido', kwargs={'pedido_id': pedido.id}), {'estado': 'pagado'})
        request = self.setup_request(request, usuario_admin)
        
        # Llamar a la vista
        response = actualizar_estado_pedido(request, pedido.id)
        
        # Verificar resultados
        assert response.status_code == 302
        assert response.url == reverse('listar_pedidos')
        
        # Verificar que se actualizó el estado
        pedido.refresh_from_db()
        assert pedido.estado == 'pagado'
        
        # Verificar mensajes
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert f"Estado del pedido #{pedido.numero_orden} actualizado a pagado" in str(messages[0])