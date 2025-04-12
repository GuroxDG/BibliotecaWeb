# carrito/tests/test_views.py
from django.utils import timezone
from datetime import timedelta
import pytest
from django.urls import reverse
from django.test import Client, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth import get_user_model
from unittest import mock
from decimal import Decimal
from usuarios.models import Usuario
from libros.models import Libro, Autor
from carrito.models import Carrito, ItemCarrito
from carrito.views import ver_carrito, agregar_al_carrito, eliminar_del_carrito, actualizar_cantidad, aplicar_cupon
from pedidos.models import Cupon
from django.contrib.sessions.middleware import SessionMiddleware

@pytest.mark.django_db
class TestCarritoViews:
    @pytest.fixture
    def usuario(self):
        return Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def libro(self):
        autor = Autor.objects.create(nombre="Autor Test")
        return Libro.objects.create(
            titulo="Libro de prueba",
            autor=autor,
            descripcion="Descripción de prueba",
            precio=Decimal('19.99'),
            stock=5,
            formato="fisico"
        )
    
    @pytest.fixture
    def carrito(self, usuario):
        return Carrito.objects.create(usuario=usuario)
    
    @pytest.fixture
    def item_carrito(self, carrito, libro):
        return ItemCarrito.objects.create(
            carrito=carrito,
            libro=libro,
            cantidad=1
        )
    
    @pytest.fixture
    def setup_request(self, usuario):
        factory = RequestFactory()
        request = factory.get(reverse('ver_carrito'))
        request.user = usuario

        # Añadir sesión manualmente
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Configurar mensajes
        setattr(request, '_messages', FallbackStorage(request))

        return request
    
    def test_ver_carrito(self, usuario, carrito):
        client = Client()
        client.force_login(usuario)

        response = client.get(reverse('ver_carrito'))

        assert response.status_code == 200
        assert 'carrito' in response.context
        assert response.context['carrito'] == carrito
       
    def test_ver_carrito_crear_nuevo(self, usuario):
        # Asegurar que no hay carrito previo
        Carrito.objects.filter(usuario=usuario).delete()

        client = Client()
        client.force_login(usuario)

        response = client.get(reverse('ver_carrito'))

        assert response.status_code == 200
        assert 'carrito' in response.context
        assert Carrito.objects.filter(usuario=usuario).exists()
    
    
    def test_agregar_al_carrito_nuevo_item(self, usuario, libro):
        client = Client()
        client.force_login(usuario)
        
        # Asegurar que no hay carrito previo
        Carrito.objects.filter(usuario=usuario).delete()
        
        response = client.get(reverse('agregar_al_carrito', args=[libro.id]))
        
        # Verificar que se creó el carrito y el item
        assert Carrito.objects.filter(usuario=usuario).exists()
        carrito = Carrito.objects.get(usuario=usuario)
        assert carrito.items.count() == 1
        assert carrito.items.first().libro == libro
        assert carrito.items.first().cantidad == 1
    
    def test_agregar_al_carrito_item_existente(self, usuario, libro, carrito):
        # Crear un item existente
        item = ItemCarrito.objects.create(
            carrito=carrito,
            libro=libro,
            cantidad=1
        )
        
        client = Client()
        client.force_login(usuario)
        
        response = client.get(reverse('agregar_al_carrito', args=[libro.id]))
        
        # Verificar que se actualizó la cantidad
        item.refresh_from_db()
        assert item.cantidad == 2
    
    def test_eliminar_del_carrito(self, usuario, carrito, item_carrito):
        client = Client()
        client.force_login(usuario)
        
        assert carrito.items.count() == 1
        
        response = client.get(reverse('eliminar_del_carrito', args=[item_carrito.id]))
        
        # Verificar que se eliminó el item
        assert carrito.items.count() == 0
    
    def test_actualizar_cantidad(self, usuario, carrito, item_carrito, libro):
        client = Client()
        client.force_login(usuario)
        
        # Actualizar a una cantidad válida
        response = client.post(reverse('actualizar_cantidad', args=[item_carrito.id]), {
            'cantidad': 3
        })
        
        # Verificar que se actualizó la cantidad
        item_carrito.refresh_from_db()
        assert item_carrito.cantidad == 3
    
    def test_actualizar_cantidad_excede_stock(self, usuario, carrito, item_carrito, libro):
        client = Client()
        client.force_login(usuario)
        
        # Intentar actualizar a una cantidad que excede el stock
        response = client.post(reverse('actualizar_cantidad', args=[item_carrito.id]), {
            'cantidad': 10  # El stock es 5
        })
        
        # Verificar que no se actualizó la cantidad
        item_carrito.refresh_from_db()
        assert item_carrito.cantidad == 1  # Mantiene la cantidad original
    
    def test_actualizar_cantidad_cero(self, usuario, carrito, item_carrito):
        client = Client()
        client.force_login(usuario)
        
        # Actualizar a cantidad cero debe eliminar el item
        response = client.post(reverse('actualizar_cantidad', args=[item_carrito.id]), {
            'cantidad': 0
        })
        
        # Verificar que se eliminó el item
        assert not ItemCarrito.objects.filter(id=item_carrito.id).exists()
    
    def test_aplicar_cupon_valido(self, usuario, carrito):
        # Crear un cupón válido
        cupon = Cupon.objects.create(
            codigo="VALID25",
            descuento=25,
            activo=True,
            fecha_inicio=timezone.now(),  # Agregar fecha_inicio
            fecha_expiracion=timezone.now() + timedelta(days=30)
        )

        # Mockear el método es_valido
        with mock.patch('pedidos.models.Cupon.es_valido', return_value=True):
            client = Client()
            client.force_login(usuario)

            response = client.post(reverse('aplicar_cupon'), {
                'codigo_cupon': 'VALID25'
            })

            # Verificar redirección
            assert response.status_code == 302

            # Verificar que se guardó el ID del cupón en la sesión
            assert 'cupon_id' in client.session
            assert client.session['cupon_id'] == cupon.id
    
    def test_aplicar_cupon_invalido(self, usuario, carrito):
        # Mockear Cupon.DoesNotExist
        with mock.patch('carrito.views.Cupon.objects.get', side_effect=Cupon.DoesNotExist):
            client = Client()
            client.force_login(usuario)
            
            # Intentar aplicar un cupón inválido
            response = client.post(reverse('aplicar_cupon'), {
                'codigo_cupon': 'INVALID'
            })
            
            # Verificar que no se guardó ningún cupón en la sesión
            assert 'cupon_id' not in client.session