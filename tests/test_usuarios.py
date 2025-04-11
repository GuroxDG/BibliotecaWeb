# test_usuarios.py
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth import authenticate
from unittest.mock import patch, MagicMock
from usuarios.views import registro
from usuarios.forms import RegistroUsuarioForm

User = get_user_model()

class TestRegistroUsuario:
    
    @pytest.fixture
    def factory(self):
        return RequestFactory()
    
    @pytest.fixture
    def valid_user_data(self):
        return {
            'email': 'usuario_test@example.com',
            'password1': 'Contraseña123',
            'password2': 'Contraseña123',
            'nombre': 'Usuario Test',
        }
    
    def setup_request_messages(self, request):
        """Añade soporte para messages framework en el request"""
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request
    
    def test_get_registro_form(self, factory):
        """Verifica que se muestre el formulario de registro correctamente"""
        request = factory.get('/registro/')
        response = registro(request)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], RegistroUsuarioForm)
    
    @patch('usuarios.views.authenticate')
    @patch('usuarios.views.login')
    @patch('usuarios.views.messages')
    def test_registro_usuario_exitoso(self, mock_messages, mock_login, mock_authenticate, factory, valid_user_data):
        """Verifica que el registro de usuario sea exitoso"""
        request = factory.post('/registro/', valid_user_data)
        request = self.setup_request_messages(request)
        
        # Mock de usuario creado
        mock_user = MagicMock()
        
        # Mock del formulario
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = mock_user
        mock_form.cleaned_data = {
            'email': valid_user_data['email'],
            'password1': valid_user_data['password1'],
        }
        
        # Mock de authenticate
        mock_authenticate.return_value = mock_user
        
        with patch('usuarios.views.RegistroUsuarioForm', return_value=mock_form):
            response = registro(request)
        
        # Verificaciones
        mock_form.is_valid.assert_called_once()
        mock_form.save.assert_called_once()
        mock_authenticate.assert_called_once_with(
            email=valid_user_data['email'], 
            password=valid_user_data['password1']
        )
        mock_login.assert_called_once_with(request, mock_user)
        mock_messages.success.assert_called_once()
        assert response.status_code == 302  # Redirección
        assert response.url == 'lista_libros'
    
    def test_email_validacion(self, factory):
        """Verifica la validación del formato de email"""
        data = {
            'email': 'correo_invalido',  # Formato inválido
            'password1': 'Contraseña123',
            'password2': 'Contraseña123',
            'nombre': 'Usuario Test',
        }
        
        request = factory.post('/registro/', data)
        request = self.setup_request_messages(request)
        
        response = registro(request)
        
        # Debería mostrar el formulario con errores
        assert response.status_code == 200
        form = response.context['form']
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_password_minimo_caracteres(self, factory):
        """Verifica que la contraseña tenga al menos 8 caracteres"""
        data = {
            'email': 'usuario_test@example.com',
            'password1': 'corta',  # Menor a 8 caracteres
            'password2': 'corta',
            'nombre': 'Usuario Test',
        }
        
        request = factory.post('/registro/', data)
        request = self.setup_request_messages(request)
        
        response = registro(request)
        
        # Debería mostrar el formulario con errores
        assert response.status_code == 200
        form = response.context['form']
        assert not form.is_valid()
        assert 'password1' in form.errors

    @pytest.mark.django_db
    def test_creacion_satisfactoria_bd(self, factory, valid_user_data):
        """Verifica que el usuario se cree correctamente en la base de datos"""
        request = factory.post('/registro/', valid_user_data)
        request = self.setup_request_messages(request)
        
        # Suponemos que el modelo de usuario personalizado usa email como username
        with patch('usuarios.views.login') as mock_login:
            with patch('usuarios.views.messages.success') as mock_messages:
                response = registro(request)
        
        # Verificar que el usuario fue creado en la BD
        assert User.objects.filter(email=valid_user_data['email']).exists()