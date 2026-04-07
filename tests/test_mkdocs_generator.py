"""Tests para gestion/mkdocs_generator.py"""

from pathlib import Path

from gestion.mkdocs_generator import (
    generar_slug,
    generar_pagina_plantilla,
    generar_pagina_categoria,
    generar_pagina_pack,
    generar_pagina_privada,
    generar_pagina_index,
    generar_css_extra,
    generar_rss_feed,
    generar_todo,
)
from gestion.schemas import crear_template_json
from gestion.pack_generator import crear_pack


def _plantilla(**kwargs):
    defaults = dict(id=1000, nombre="Test Plantilla", descripcion="Desc test.", tags=["test"])
    defaults.update(kwargs)
    return crear_template_json(**defaults)


def test_generar_slug():
    # unidecode convierte Ñ → n, ó → o antes de sanitizar
    assert generar_slug("Listado de clientes ESPAÑA", 1000) == "1000-listado-de-clientes-espana"
    assert generar_slug("Balance de situación", 3000) == "3000-balance-de-situacion"


def test_pagina_plantilla():
    p = _plantilla()
    md = generar_pagina_plantilla(p)
    assert "1000" in md
    assert "Test Plantilla" in md
    assert "Descripcion" in md or "Desc" in md


def test_pagina_categoria():
    p = _plantilla()
    md = generar_pagina_categoria("Informes y Listados", "📋", [p])
    assert "Informes y Listados" in md
    assert "Test Plantilla" in md
    assert "1 plantillas" in md


def test_pagina_categoria_vacia():
    md = generar_pagina_categoria("Test", "📋", [])
    assert "no hay plantillas" in md.lower() or "Aun" in md


def test_pagina_pack():
    pack = crear_pack("test", "Pack Test", "Desc", [1000, 2000])
    p1 = _plantilla(id=1000, nombre="A")
    p2 = _plantilla(id=2000, nombre="B")
    md = generar_pagina_pack(pack, [p1, p2])
    assert "Pack Test" in md
    assert "2 plantillas" in md


def test_pagina_privada():
    p = crear_template_json(
        id=42,
        nombre="Privada Test",
        descripcion="Desc",
        tags=["test"],
        cliente_codigo="CLI-00123",
        cliente_clave_hash="hash123",
    )
    md = generar_pagina_privada(p)
    assert "CLI-00123" in md
    assert "privada" in md.lower()


def test_pagina_index():
    p = _plantilla()
    pack = crear_pack("test", "Pack Test", "Desc", [1000])
    md = generar_pagina_index([p], [pack], {"total_plantillas": 1, "total_packs": 1})
    assert "Plantillas Gratuitas" in md
    assert "Pack Test" in md
    assert "Test Plantilla" in md


def test_css_extra():
    css = generar_css_extra()
    assert ".grid-cards" in css
    assert ".badge" in css
    assert "@media" in css


def test_rss_feed():
    p = _plantilla()
    rss = generar_rss_feed([p])
    assert "<?xml" in rss
    assert "<rss" in rss
    assert "Test Plantilla" in rss


def test_generar_todo(tmp_path):
    p1 = _plantilla(id=1000, nombre="Clientes")
    p2 = _plantilla(id=2000, nombre="Facturas")
    pack = crear_pack("test", "Pack Test", "Desc", [1000, 2000])
    stats = {"total_plantillas": 2, "total_packs": 1}

    generados = generar_todo(
        plantillas=[p1, p2],
        packs=[pack],
        stats=stats,
        docs_dir=tmp_path,
        packs_datos=[pack],
    )

    assert "css" in generados
    assert "index" in generados
    assert "rss" in generados
    assert generados["css"].exists()
    assert generados["index"].exists()
    assert generados["rss"].exists()

    # Verificar contenido del RSS
    rss_content = generados["rss"].read_text(encoding="utf-8")
    assert "Clientes" in rss_content
