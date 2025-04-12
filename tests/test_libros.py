import pytest
from decimal import Decimal
from django.db import models
from libros.models import Categoria, Autor, Libro

@pytest.mark.django_db
class TestCategoriaModel:
    def test_crear_categoria(self):
        categoria = Categoria.objects.create(
            nombre="Ciencia Ficción",
            descripcion="Libros de ciencia ficción y fantasía"
        )
        assert categoria.nombre == "Ciencia Ficción"
        assert categoria.descripcion == "Libros de ciencia ficción y fantasía"
    
    def test_str_representation(self):
        categoria = Categoria.objects.create(nombre="Historia")
        assert str(categoria) == "Historia"
        
    def test_categoria_sin_descripcion(self):
        categoria = Categoria.objects.create(nombre="Poesía")
        assert categoria.descripcion is None

@pytest.mark.django_db
class TestAutorModel:
    def test_crear_autor(self):
        autor = Autor.objects.create(
            nombre="Gabriel García Márquez",
            biografia="Escritor colombiano, premio Nobel de Literatura"
        )
        assert autor.nombre == "Gabriel García Márquez"
        assert autor.biografia == "Escritor colombiano, premio Nobel de Literatura"
    
    def test_str_representation(self):
        autor = Autor.objects.create(nombre="J.K. Rowling")
        assert str(autor) == "J.K. Rowling"
        
    def test_autor_sin_biografia(self):
        autor = Autor.objects.create(nombre="Jane Austen")
        assert autor.biografia is None

@pytest.mark.django_db
class TestLibroModel:
    @pytest.fixture
    def autor_fixture(self):
        return Autor.objects.create(nombre="Ernest Hemingway")
    
    @pytest.fixture
    def categoria_fixture(self):
        return Categoria.objects.create(nombre="Novela")
    
    def test_crear_libro(self, autor_fixture, categoria_fixture):
        libro = Libro.objects.create(
            titulo="El viejo y el mar",
            autor=autor_fixture,
            descripcion="Historia de un pescador cubano",
            precio=Decimal('19.99'),
            stock=10,
            formato="fisico"
        )
        libro.categorias.add(categoria_fixture)
        
        assert libro.titulo == "El viejo y el mar"
        assert libro.autor.nombre == "Ernest Hemingway"
        assert libro.precio == Decimal('19.99')
        assert libro.stock == 10
        assert libro.formato == "fisico"
        assert libro.categorias.count() == 1
        assert libro.categorias.first().nombre == "Novela"
    
    def test_disponible_con_stock(self, autor_fixture):
        libro = Libro.objects.create(
            titulo="Libro con stock",
            autor=autor_fixture,
            descripcion="Libro disponible",
            precio=Decimal('29.99'),
            stock=5,
            formato="fisico"
        )
        assert libro.disponible() is True
    
    def test_no_disponible_sin_stock(self, autor_fixture):
        libro = Libro.objects.create(
            titulo="Libro sin stock",
            autor=autor_fixture,
            descripcion="Libro agotado",
            precio=Decimal('15.99'),
            stock=0,
            formato="digital"
        )
        assert libro.disponible() is False
    
    def test_str_representation(self, autor_fixture):
        libro = Libro.objects.create(
            titulo="1984",
            autor=autor_fixture,
            descripcion="Novela distópica",
            precio=Decimal('24.99'),
            stock=8,
            formato="fisico"
        )
        assert str(libro) == "1984"