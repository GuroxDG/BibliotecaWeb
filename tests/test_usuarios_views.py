# usuarios/tests/test_views.py
import pytest
from django.urls import reverse
from django.test import Client, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth import get_user_model
from unittest import mock
from usuarios.views import registro
from usuarios.forms import RegistroUsuarioForm

Usuario = get_user_model()

@pytest.mark.django_db
class TestRegistroView:
    def setup_method(self):
        self.client = Client()
        self.factory = RequestFactory()
        
    def test_get_registro_view(self):
        # Prueba que la vista muestra el formulario correctamente
        response = self.client.get(reverse('registro'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], RegistroUsuarioForm)
    
    def test_post_registro_valido(self):
        # Prueba que la vista registra un usuario correctamente
        data = {
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'password1': 'contraseña_segura123',
            'password2': 'contraseña_segura123',
        }
        
        # Simular request POST
        request = self.factory.post(reverse('registro'), data=data)
        request.session = {}
        
        # Configurar messages para evitar errores
        setattr(request, '_messages', FallbackStorage(request))
        
        # Mockear el authenticate y login
        with mock.patch('usuarios.views.authenticate') as mock_authenticate:
            with mock.patch('usuarios.views.login') as mock_login:
                with mock.patch('usuarios.views.redirect') as mock_redirect:
                    # Configura los mocks
                    mock_user = mock.MagicMock()
                    mock_authenticate.return_value = mock_user
                    mock_redirect.return_value = "redirect_response"
                    
                    # Ejecutar vista
                    response = registro(request)
                    
                    # Verificar redirección y mensaje
                    mock_authenticate.assert_called_once_with(
                        email='nuevo@example.com', 
                        password='contraseña_segura123'
                    )
                    mock_login.assert_called_once_with(request, mock_user)
                    mock_redirect.assert_called_once_with('lista_libros')
                    assert response == "redirect_response"
    
    def test_post_registro_invalid(self):
        # Prueba que la vista maneja datos inválidos correctamente
        data = {
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'password1': 'contraseña1',
            'password2': 'contraseña2',  # No coincide con password1
        }
        
        response = self.client.post(reverse('registro'), data=data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()