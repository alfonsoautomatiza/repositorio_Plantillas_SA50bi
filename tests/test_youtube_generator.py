"""Tests para gestion/youtube_generator.py"""

from gestion.youtube_generator import (
    generar_youtube_seo,
    generar_texto_copiable,
    generar_descripcion_por_categoria,
)


def test_generar_youtube_seo():
    seo = generar_youtube_seo(
        nombre="Listado de clientes",
        descripcion="Listado completo de clientes.",
        tags=["clientes", "listado"],
        categoria="Informes y Listados",
    )
    assert "Listado de clientes" in seo["titulo"]
    assert "Sage50BI" in seo["titulo"]
    assert "clientes" in seo["tags_youtube"]
    assert "sage50" in seo["tags_youtube"]


def test_generar_texto_copiable():
    texto = generar_texto_copiable(
        nombre="Test",
        descripcion="Desc",
        tags=["test"],
    )
    assert "COPIAR EN YOUTUBE" in texto
    assert "Test" in texto
    assert "TAGS" in texto


def test_descripcion_por_categoria():
    desc = generar_descripcion_por_categoria("Listado", "Clientes", "Informes y Listados")
    assert "Listado" in desc
    assert "Gratuita" in desc


def test_descripcion_categoria_desconocida():
    desc = generar_descripcion_por_categoria("Test", "Desc", "Categoría Rara")
    assert "Test" in desc
