"""Tests para gestion/schemas.py"""

import json
import tempfile
from pathlib import Path

from gestion.schemas import (
    crear_template_json,
    validar_template_json,
    cargar_template_json,
    guardar_template_json,
    get_categoria_por_id,
    es_plantilla_privada,
    CATEGORIAS,
    TemplateValidationError,
)


# === get_categoria_por_id ===


def test_categoria_publica_1000():
    cat = get_categoria_por_id(1000)
    assert cat["nombre"] == "Informes y Listados"
    assert cat["icono"] == "📋"


def test_categoria_publica_2000():
    cat = get_categoria_por_id(2000)
    assert cat["nombre"] == "Facturas y Documentos"


def test_categoria_publica_3000():
    cat = get_categoria_por_id(3000)
    assert cat["nombre"] == "Balances y Contabilidad"


def test_categoria_publica_4000():
    cat = get_categoria_por_id(4000)
    assert cat["nombre"] == "Dashboard y Gráficos"


def test_categoria_privada():
    cat = get_categoria_por_id(42)
    assert cat["nombre"] == "Personalizadas"


def test_categoria_desconocida():
    cat = get_categoria_por_id(9999)
    assert cat["nombre"] == "Desconocida"


# === es_plantilla_privada ===


def test_es_privada():
    assert es_plantilla_privada(1) is True
    assert es_plantilla_privada(999) is True
    assert es_plantilla_privada(500) is True


def test_no_es_privada():
    assert es_plantilla_privada(1000) is False
    assert es_plantilla_privada(0) is False
    assert es_plantilla_privada(2000) is False


# === crear_template_json ===


def test_crear_publica():
    t = crear_template_json(
        id=1000,
        nombre="Listado de clientes ESPAÑA",
        descripcion="Listado completo de clientes.",
        tags=["clientes", "listado"],
        video_youtube="https://youtube.com/watch?v=abc123",
    )
    assert t["id"] == 1000
    assert t["nombre"] == "Listado de clientes ESPAÑA"
    assert t["tipo"] == "publica"
    assert t["gratuita"] is True
    assert t["version"] == "1.0.0"
    assert "youtube_seo" in t
    assert "open_graph" in t
    assert t["slug"].startswith("1000-")
    assert len(t["tags"]) == 2
    assert "sql" in t["archivos"]


def test_crear_privada():
    t = crear_template_json(
        id=42,
        nombre="Informe Ferretería López",
        descripcion="Informe personalizado.",
        tags=["privada", "ferreteria"],
        cliente_codigo="CLI-00123",
        cliente_clave_hash="abc123hash",
    )
    assert t["id"] == 42
    assert t["tipo"] == "privada"
    assert t["gratuita"] is False
    assert t["cliente"]["codigo"] == "CLI-00123"
    assert "youtube_seo" not in t  # Privadas no tienen YouTube


def test_crear_sin_dashboard():
    t = crear_template_json(
        id=1001,
        nombre="Balance",
        descripcion="Balance de situación.",
        tags=["balance"],
        tiene_dashboard=False,
    )
    assert "sql" in t["archivos"]
    assert "dashboard" not in t["archivos"]


def test_crear_con_dashboard():
    t = crear_template_json(
        id=1002,
        nombre="Dashboard ventas",
        descripcion="Dashboard de ventas.",
        tags=["ventas", "dashboard"],
        tiene_dashboard=True,
    )
    assert "dashboard" in t["archivos"]


# === validar_template_json ===


def test_validar_publica_ok():
    t = crear_template_json(id=1000, nombre="Test", descripcion="Desc", tags=["test"])
    errores = validar_template_json(t)
    assert errores == []


def test_validar_campo_faltante():
    errores = validar_template_json({})
    assert len(errores) > 0
    assert any("requerido" in e for e in errores)


def test_validar_id_negativo():
    t = crear_template_json(id=1000, nombre="Test", descripcion="Desc", tags=["test"])
    t["id"] = -1
    errores = validar_template_json(t)
    assert any("ID" in e for e in errores)


def test_validar_tipo_incoherente():
    t = crear_template_json(id=1000, nombre="Test", descripcion="Desc", tags=["test"])
    t["tipo"] = "privada"
    errores = validar_template_json(t)
    assert any("rango" in e for e in errores)


def test_validar_privada_sin_cliente():
    t = crear_template_json(
        id=42,
        nombre="Test",
        descripcion="Desc",
        tags=["test"],
        cliente_codigo="CLI-00123",
        cliente_clave_hash="hash",
    )
    errores = validar_template_json(t)
    assert errores == []


# === guardar/cargar template.json ===


def test_guardar_y_cargar(tmp_path):
    t = crear_template_json(id=1000, nombre="Test Carga", descripcion="Desc", tags=["test"])
    path = tmp_path / "template.json"
    guardar_template_json(t, path)

    assert path.exists()
    loaded = cargar_template_json(path)
    assert loaded["id"] == 1000
    assert loaded["nombre"] == "Test Carga"


def test_guardar_invalido_lanza_error(tmp_path):
    t = crear_template_json(id=1000, nombre="Test", descripcion="Desc", tags=["test"])
    # Hacer el template invalido: tipo vacio
    t["tipo"] = ""
    path = tmp_path / "template.json"
    try:
        guardar_template_json(t, path)
        assert False, "Debería lanzar TemplateValidationError"
    except TemplateValidationError:
        pass  # OK
