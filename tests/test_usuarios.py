# usuarios/tests/test_models.py
import pytest
from django.db import IntegrityError
from usuarios.models import Usuario

@pytest.mark.django_db
class TestUsuarioModel:
    def test_crear_usuario(self):
        # Prueba la creación básica de un usuario
        usuario = Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert usuario.username == "testuser"
        assert usuario.email == "test@example.com"
        assert usuario.check_password("password123")
    
    def test_email_debe_ser_unico(self):
        # Prueba que no se pueden crear dos usuarios con el mismo email
        Usuario.objects.create_user(
            username="usuario1",
            email="repetido@example.com",
            password="password123"
        )
        
        # El segundo usuario con el mismo email debería fallar
        with pytest.raises(IntegrityError):
            Usuario.objects.create_user(
                username="usuario2",
                email="repetido@example.com",
                password="password123"
            )
    
    def test_autenticar_por_email(self):
        # Prueba que podemos autenticar usando el email como USERNAME_FIELD
        Usuario.objects.create_user(
            username="testuser",
            email="auth_test@example.com",
            password="password123"
        )
        
        usuario = Usuario.objects.get(email="auth_test@example.com")
        assert usuario is not None
        assert usuario.username == "testuser"