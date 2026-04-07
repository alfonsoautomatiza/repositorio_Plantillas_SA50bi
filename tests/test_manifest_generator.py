"""Tests para gestion/manifest_generator.py"""

import json
from pathlib import Path

from gestion.manifest_generator import (
    generar_manifest,
    generar_y_guardar_manifest,
    cargar_manifest,
    bump_manifest_version,
)
from gestion.schemas import crear_template_json
from gestion.pack_generator import crear_pack


def _plantilla(**kwargs):
    defaults = dict(id=1000, nombre="Test", descripcion="Desc", tags=["test"])
    defaults.update(kwargs)
    return crear_template_json(**defaults)


def test_generar_manifest_vacio():
    m = generar_manifest([], [])
    assert m["total_plantillas"] == 0
    assert m["total_packs"] == 0
    assert m["plantillas"] == []
    assert "version_manifest" in m


def test_generar_manifest_con_plantillas():
    p = _plantilla()
    m = generar_manifest([p], [])
    assert m["total_plantillas"] == 1
    assert m["plantillas"][0]["id"] == 1000
    assert "url_base" in m["plantillas"][0]


def test_generar_manifest_con_packs():
    pack = crear_pack("test", "Pack Test", "Desc", [1000])
    m = generar_manifest([], [pack])
    assert m["total_packs"] == 1
    assert m["packs"][0]["id"] == "pack-test"


def test_generar_manifest_solo_publicas():
    """Las plantillas privadas no deben aparecer en el manifest."""
    pub = _plantilla(id=1000, nombre="Publica")
    priv = crear_template_json(
        id=42,
        nombre="Privada",
        descripcion="Desc",
        tags=["test"],
        cliente_codigo="CLI-00123",
        cliente_clave_hash="hash",
    )
    m = generar_manifest([pub, priv], [])
    assert m["total_plantillas"] == 1  # Solo la pública


def test_guardar_cargar_manifest(tmp_path):
    m = generar_manifest([], [], version_manifest="1.0.0")
    path = generar_y_guardar_manifest(tmp_path, [], [], version_manifest="1.0.0")
    assert path.exists()
    assert path.name == "manifest-templates.json"

    loaded = cargar_manifest(tmp_path)
    assert loaded is not None
    assert loaded["version_manifest"] == "1.0.0"


def test_cargar_manifest_inexistente(tmp_path):
    assert cargar_manifest(tmp_path) is None


def test_bump_manifest():
    m = {"version_manifest": "1.0.0", "fecha_generacion": "2026-01-01T00:00:00Z"}
    result = bump_manifest_version(m)
    assert result["version_manifest"] == "1.0.1"
