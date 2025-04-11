# test_libros.py
import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from unittest.mock import patch, MagicMock
from libros.views import lista_libros, detalle_libro
from libros.models import Libro, Categoria, Autor

User = get_user_model()

class TestLibrosViews:
    
    @pytest.fixture
    def factory(self):
        return RequestFactory()
    
    @pytest.fixture
    def usuario(self):
        user = MagicMock(spec=User)
        user.is_authenticated = True
        return user
    
    @pytest.fixture
    def categoria(self):
        return MagicMock(spec=Categoria)
    
    @pytest.fixture
    def autor(self):
        autor_mock = MagicMock(spec=Autor)
        autor_mock.nombre = "Autor Test"
        return autor_mock
    
    @pytest.fixture
    def libro(self, autor):
        libro_mock = MagicMock(spec=Libro)
        libro_mock.id = 1
        libro_mock.titulo = "Libro Test"
        libro_mock.autor = autor
        libro_mock.precio = 19.99
        libro_mock.stock = 10
        libro_mock.formato = "Físico"
        libro_mock.categorias.all.return_value = []
        return libro_mock
    
    @patch('libros.views.Categoria.objects.all')
    @patch('libros.views.Libro.objects.all')
    def test_lista_libros_sin_filtros(self, mock_libros_all, mock_categorias_all, factory, usuario):
        """Verifica que la lista de libros se muestre correctamente sin filtros"""
        # Configurar mocks
        libros_mock = MagicMock()
        mock_libros_all.return_value = libros_mock
        
        categorias_mock = MagicMock()
        mock_categorias_all.return_value = categorias_mock
        
        # Crear request
        request = factory.get('/libros/')
        request.user = usuario
        
        # Ejecutar vista
        response = lista_libros(request)
        
        # Verificaciones
        assert response.status_code == 200
        assert 'libros' in response.context
        assert 'categorias' in response.context
        assert response.context['libros'] == libros_mock
        assert response.context['categorias'] == categorias_mock
    
    @patch('libros.views.Categoria.objects.all')
    @patch('libros.views.Libro.objects.all')
    def test_lista_libros_con_filtros(self, mock_libros_all, mock_categorias_all, factory, usuario):
        """Verifica que los filtros de búsqueda funcionen correctamente"""
        # Configurar mocks
        libros_mock = MagicMock()
        libros_filtrados_mock = MagicMock()
        libros_mock.filter.return_value = libros_filtrados_mock
        mock_libros_all.return_value = libros_mock
        
        mock_categorias_all.return_value = MagicMock()
        
        # Crear request con parámetros de filtrado
        request = factory.get('/libros/?categoria=1&formato=Físico&busqueda=Python')
        request.user = usuario
        
        # Ejecutar vista
        response = lista_libros(request)
        
        # Verificaciones
        assert response.status_code == 200
        assert 'libros' in response.context
        libros_mock.filter.assert_called()
    
    @patch('libros.views.get_object_or_404')
    def test_detalle_libro_visualizacion(self, mock_get_object, factory, usuario, libro):
        """Verifica que se muestren correctamente los detalles del libro (título, autor, precio, stock y formato)"""
        # Configurar mocks
        mock_get_object.return_value = libro
        
        # Crear request
        request = factory.get(f'/libros/{libro.id}/')
        request.user = usuario
        
        # Mock para libros relacionados
        with patch.object(Libro.objects, 'filter') as mock_filter:
            mock_filter.return_value.exclude.return_value.distinct.return_value.__getitem__.return_value = []
            
            # Ejecutar vista
            response = detalle_libro(request, libro.id)
        
        # Verificaciones
        assert response.status_code == 200
        assert 'libro' in response.context
        assert response.context['libro'] == libro
        assert response.context['libro'].titulo == "Libro Test"
        assert response.context['libro'].autor.nombre == "Autor Test"
        assert response.context['libro'].precio == 19.99
        assert response.context['libro'].stock == 10
        assert response.context['libro'].formato == "Físico"
    
    @patch('libros.views.get_object_or_404')
    def test_detalle_libro_no_existente(self, mock_get_object, factory, usuario):
        """Verifica que se maneje correctamente cuando se solicita un libro que no existe"""
        # Configurar mock para simular libro no encontrado
        mock_get_object.side_effect = Http404("Libro no encontrado")
        
        # Crear request
        request = factory.get('/libros/999/')
        request.user = usuario
        
        # Ejecutar vista y verificar que lanza Http404
        with pytest.raises(Http404):
            detalle_libro(request, 999)