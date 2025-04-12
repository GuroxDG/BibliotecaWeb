# usuarios/tests/test_forms.py
import pytest
from django.test import RequestFactory
from usuarios.forms import RegistroUsuarioForm
from usuarios.models import Usuario

@pytest.mark.django_db
class TestRegistroUsuarioForm:
    def test_form_valido(self):
        # Prueba que el formulario es válido con datos correctos
        form_data = {
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'password1': 'contraseña_segura123',
            'password2': 'contraseña_segura123',
        }
        form = RegistroUsuarioForm(data=form_data)
        assert form.is_valid()
    
    def test_email_duplicado(self):
        # Prueba que el formulario valida emails duplicados
        Usuario.objects.create_user(
            username="usuario_existente",
            email="existente@example.com",
            password="password123"
        )
        
        form_data = {
            'username': 'nuevousuario',
            'email': 'existente@example.com',  # Email duplicado
            'password1': 'contraseña_segura123',
            'password2': 'contraseña_segura123',
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_passwords_diferentes(self):
        # Prueba que el formulario valida que las contraseñas coincidan
        form_data = {
            'username': 'nuevousuario',
            'email': 'nuevo@example.com',
            'password1': 'contraseña1',
            'password2': 'contraseña2',  # Diferente de password1
        }
        form = RegistroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors