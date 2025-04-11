# test_pedidos.py
import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch, MagicMock, call
from pedidos.views import confirmar_pedido, procesar_pedido, historial_pedidos, detalle_pedido, enviarCorreo
from pedidos.models import Pedido, DetallePedido, Cupon
from carrito.models import Carrito, ItemCarrito
from libros.models import Libro

User = get_user_model()

class TestPedidosViews:
    
    @pytest.fixture
    def factory(self):
        return RequestFactory()
    
    @pytest.fixture
    def usuario(self):
        user = MagicMock(spec=User)
        user.is_authenticated = True
        user.email = "usuario@test.com"
        return user
    
    @pytest.fixture
    def libro(self):
        libro_mock = MagicMock(spec=Libro)
        libro_mock.id = 1
        libro_mock.titulo = "Libro Test"
        libro_mock.precio = 19.99
        libro_mock.stock = 10
        return libro_mock
    
    @pytest.fixture
    def item_carrito(self, libro):
        item_mock = MagicMock(spec=ItemCarrito)
        item_mock.libro = libro
        item_mock.cantidad = 2
        return item_mock
    
    @pytest.fixture
    def carrito(self, usuario, item_carrito):
        carrito_mock = MagicMock(spec=Carrito)
        carrito_mock.usuario = usuario
        carrito_mock.items.all.return_value = [item_carrito]
        carrito_mock.items.exists.return_value = True
        carrito_mock.obtener_total.return_value = 39.98  # 2 * 19.99
        carrito_mock.aplicar_cupon.return_value = 31.98  # 20% descuento
        return carrito_mock
    
    @pytest.fixture
    def cupon(self):
        cupon_mock = MagicMock(spec=Cupon)
        cupon_mock.id = 1
        cupon_mock.codigo = "DESCUENTO20"
        cupon_mock.descuento = 20  # 20%
        cupon_mock.es_valido.return_value = True
        return cupon_mock
    
    @pytest.fixture
    def pedido(self, usuario):
        pedido_mock = MagicMock(spec=Pedido)
        pedido_mock.id = 1
        pedido_mock.numero_orden = "ORD-001"
        pedido_mock.usuario = usuario
        pedido_mock.total = 39.98
        return pedido_mock
    
    def setup_request_messages(self, request):
        """Añade soporte para messages framework en el request"""
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    def test_confirmar_pedido_carrito_vacio(self, mock_get_or_create, factory, usuario):
        """Verifica que se maneje correctamente un carrito vacío al confirmar pedido"""
        # Configurar mock de carrito vacío
        carrito_vacio = MagicMock(spec=Carrito)
        carrito_vacio.items.exists.return_value = False
        mock_get_or_create.return_value = (carrito_vacio, False)
        
        # Crear request
        request = factory.get('/pedidos/confirmar/')
        request.user = usuario
        request = self.setup_request_messages(request)
        
        # Ejecutar vista
        response = confirmar_pedido(request)
        
        # Verificaciones
        assert response.status_code == 302  # Redirección
        assert response.url == 'ver_carrito'
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    @patch('pedidos.views.Cupon.objects.get')
    def test_confirmar_pedido_con_cupon(self, mock_cupon_get, mock_get_or_create, factory, usuario, carrito, cupon):
        """Verifica que se aplique correctamente un cupón al confirmar pedido"""
        # Configurar mocks
        mock_get_or_create.return_value = (carrito, False)
        mock_cupon_get.return_value = cupon
        
        # Crear request con cupón en sesión
        request = factory.get('/pedidos/confirmar/')
        request.user = usuario
        request.session = {'cupon_id': cupon.id}
        request = self.setup_request_messages(request)
        
        # Ejecutar vista
        response = confirmar_pedido(request)
        
        # Verificaciones
        assert response.status_code == 200
        assert 'carrito' in response.context
        assert 'cupon' in response.context
        assert 'total' in response.context
        assert response.context['carrito'] == carrito
        assert response.context['cupon'] == cupon
        assert response.context['total'] == 31.98  # Total con descuento
        carrito.aplicar_cupon.assert_called_once_with(cupon)
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    @patch('pedidos.views.Cupon.objects.get')
    @patch('pedidos.views.messages')
    def test_confirmar_pedido_cupon_expirado(self, mock_messages, mock_cupon_get, mock_get_or_create, factory, usuario, carrito, cupon):
        """Verifica que se maneje correctamente un cupón expirado"""
        # Configurar mocks
        mock_get_or_create.return_value = (carrito, False)
        mock_cupon_get.return_value = cupon
        cupon.es_valido.return_value = False  # Cupón expirado
        
        # Crear request con cupón en sesión
        request = factory.get('/pedidos/confirmar/')
        request.user = usuario
        request.session = {'cupon_id': cupon.id}
        request = self.setup_request_messages(request)
        
        # Ejecutar vista
        response = confirmar_pedido(request)
        
        # Verificaciones
        assert response.status_code == 200
        assert 'cupon' in response.context
        assert response.context['cupon'] is None  # No se aplica el cupón
        mock_messages.warning.assert_called_once()
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    @patch('pedidos.views.Pedido.objects.create')
    @patch('pedidos.views.DetallePedido.objects.create')
    @patch('pedidos.views.transaction.atomic')
    @patch('pedidos.views.enviarCorreo')
    @patch('pedidos.views.messages')
    def test_procesar_pedido_exitoso(self, mock_messages, mock_enviar_correo, mock_atomic, 
                                  mock_detalle_create, mock_pedido_create, mock_get_or_create, 
                                  factory, usuario, carrito, item_carrito, libro, pedido):
        """Verifica que se procese correctamente un pedido"""
        # Configurar mocks
        mock_get_or_create.return_value = (carrito, False)
        mock_pedido_create.return_value = pedido
        
        # Crear request POST
        request = factory.post('/pedidos/procesar/', {'direccion': 'Calle Test 123'})
        request.user = usuario
        request.session = {}
        request = self.setup_request_messages(request)
        
        # Ejecutar vista
        response = procesar_pedido(request)
        
        # Verificaciones
        mock_pedido_create.assert_called_once()
        mock_detalle_create.assert_called_once()
        assert libro.save.called  # Verificar que se actualizó el stock
        mock_enviar_correo.assert_called_once_with([usuario.email], f'Tu pedido #{pedido.numero_orden} ha sido procesado con éxito. Total: ${pedido.total}')
        assert carrito.items.all.return_value.delete.called  # Verificar que se vació el carrito
        mock_messages.success.assert_called_once()
        assert response.status_code == 302  # Redirección
        assert response.url == 'historial_pedidos'
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    @patch('pedidos.views.messages')
    def test_procesar_pedido_carrito_vacio(self, mock_messages, mock_get_or_create, factory, usuario):
        """Verifica que se maneje correctamente un carrito vacío al procesar pedido"""
        # Configurar mock de carrito vacío
        carrito_vacio = MagicMock(spec=Carrito)
        carrito_vacio.items.exists.return_value = False
        mock_get_or_create.return_value = (carrito_vacio, False)
        
        # Crear request POST
        request = factory.post('/pedidos/procesar/', {'direccion': 'Calle Test 123'})
        request.user = usuario
        request = self.setup_request_messages(request)
        
        # Ejecutar vista
        response = procesar_pedido(request)
        
        # Verificaciones
        mock_messages.error.assert_called_once()
        assert response.status_code == 302  # Redirección
        assert response.url == 'ver_carrito'
    
    @patch('pedidos.views.Carrito.objects.get_or_create')
    @patch('pedidos.views.transaction.set_rollback')
    @patch('pedidos.views.messages')
    def test_procesar_pedido_stock_insuficiente(self, mock_messages, mock_rollback, mock_get_or_create, 
                                             factory, usuario, carrito, item_carrito):
        """Verifica que se maneje correctamente un pedido con stock insuficiente"""
        # Configurar mocks
        mock_get_or_create.return_value = (carrito, False)
        item_carrito.cantidad = 15  # Mayor que el stock disponible (10)
        
        # Crear request POST
        request = factory.post('/pedidos/procesar/', {'direccion': 'Calle Test 123'})
        request.user = usuario
        request.session = {}
        request = self.setup_request_messages(request)
        
        # Ejecutar vista con contexto transaction.atomic
        with patch('pedidos.views.Pedido.objects.create') as mock_pedido_create:
            response = procesar_pedido(request)
        
        # Verificaciones
        mock_rollback.assert_called_once_with(True)
        mock_messages.error.assert_called_once()
        assert response.status_code == 302  # Redirección
        assert response.url == 'ver_carrito'
    
    @patch('pedidos.views.Pedido.objects.filter')
    def test_historial_pedidos(self, mock_filter, factory, usuario):
        """Verifica que se muestre correctamente el historial de pedidos"""
        # Configurar mock
        pedidos_mock = MagicMock()
        pedidos_mock.order_by.return_value = [MagicMock(spec=Pedido), MagicMock(spec=Pedido)]
        mock_filter.return_value = pedidos_mock
        
        # Crear request
        request = factory.get('/pedidos/historial/')
        request.user = usuario
        
        # Ejecutar vista
        response = historial_pedidos(request)
        
        # Verificaciones
        mock_filter.assert_called_once_with(usuario=usuario)
        assert response.status_code == 200
        assert 'pedidos' in response.context
        assert len(response.context['pedidos']) == 2
    
    @patch('pedidos.views.get_object_or_404')
    def test_detalle_pedido(self, mock_get_object, factory, usuario, pedido):
        """Verifica que se muestre correctamente el detalle de un pedido"""
        # Configurar mock
        mock_get_object.return_value = pedido
        
        # Crear request
        request = factory.get(f'/pedidos/detalle/{pedido.numero_orden}/')
        request.user = usuario
        
        # Ejecutar vista
        response = detalle_pedido(request, pedido.numero_orden)
        
        # Verificaciones
        mock_get_object.assert_called_once_with(Pedido, numero_orden=pedido.numero_orden, usuario=usuario)
        assert response.status_code == 200
        assert 'pedido' in response.context
        assert response.context['pedido'] == pedido

    @patch('pedidos.views.smtplib.SMTP')
    @patch('pedidos.views.MIMEMultipart')
    @patch('pedidos.views.MIMEText')
    def test_enviar_correo(self, mock_mime_text, mock_mime_multipart, mock_smtp, factory):
        """Verifica que la función de envío de correo funcione correctamente"""
        # Configurar mocks
        servidor_mock = MagicMock()
        mock_smtp.return_value = servidor_mock
        
        mensaje_mock = MagicMock()
        mock_mime_multipart.return_value = mensaje_mock
        
        mime_text_mock = MagicMock()
        mock_mime_text.return_value = mime_text_mock
        
        # Parámetros de prueba
        destinatario = ["usuario@test.com"]
        mensaje = "Confirmación de pedido #123"
        
        # Ejecutar función
        enviarCorreo(destinatario, mensaje)
        
        # Verificaciones
        mock_smtp.assert_called_once_with("smtp-mail.outlook.com", 587)
        assert servidor_mock.starttls.called
        assert servidor_mock.login.called
        assert servidor_mock.sendmail.called
        assert servidor_mock.quit.called
        mock_mime_text.assert_called_once_with(mensaje, "plain")
        assert mensaje_mock.attach.called_with(mime_text_mock)