"""Tests para gestion/pack_generator.py"""

import json
from pathlib import Path

from gestion.pack_generator import (
    crear_pack,
    validar_pack,
    guardar_pack,
    cargar_pack,
    listar_packs,
    actualizar_pack,
    obtener_packs_de_plantilla,
)


def test_crear_pack():
    pack = crear_pack(
        pack_id="gestion-comercial",
        nombre="Pack Gestión Comercial",
        descripcion="Todo para gestionar.",
        plantillas=[1000, 1001, 2000],
    )
    assert pack["id"] == "pack-gestion-comercial"  # Auto-prefijo
    assert pack["total_plantillas"] == 3
    assert pack["plantillas"] == [1000, 1001, 2000]  # Sorted


def test_crear_pack_sin_prefijo():
    pack = crear_pack("test", "Test", "Desc", [1000])
    assert pack["id"] == "pack-test"


def test_validar_pack_ok():
    pack = crear_pack("test", "Test", "Desc", [1000, 2000])
    errores = validar_pack(pack, {1000, 2000})
    assert errores == []


def test_validar_pack_sin_id():
    errores = validar_pack({"nombre": "X"}, set())
    assert any("requerido" in e.lower() for e in errores)


def test_validar_pack_menos_2_plantillas():
    pack = crear_pack("test", "Test", "Desc", [1000])
    errores = validar_pack(pack, {1000})
    assert any("al menos 2" in e for e in errores)


def test_validar_pack_plantilla_inexistente():
    pack = crear_pack("test", "Test", "Desc", [1000, 9999])
    errores = validar_pack(pack, {1000})
    assert any("9999" in e for e in errores)


def test_guardar_cargar_pack(tmp_path):
    pack = crear_pack("test-save", "Test Save", "Desc", [1000, 2000])
    path = guardar_pack(pack, tmp_path)
    assert path.exists()

    loaded = cargar_pack(path)
    assert loaded["id"] == "pack-test-save"
    assert loaded["nombre"] == "Test Save"


def test_listar_packs(tmp_path):
    guardar_pack(crear_pack("a", "Pack A", "Desc A", [1000, 2000]), tmp_path)
    guardar_pack(crear_pack("b", "Pack B", "Desc B", [3000, 4000]), tmp_path)

    packs = listar_packs(tmp_path)
    assert len(packs) == 2
    nombres = [p["nombre"] for p in packs]
    assert "Pack A" in nombres
    assert "Pack B" in nombres


def test_listar_packs_vacio(tmp_path):
    assert listar_packs(tmp_path) == []


def test_actualizar_add():
    pack = crear_pack("test", "Test", "Desc", [1000])
    result = actualizar_pack(pack, 2000, "add")
    assert 2000 in result["plantillas"]


def test_actualizar_remove():
    pack = crear_pack("test", "Test", "Desc", [1000, 2000])
    result = actualizar_pack(pack, 1000, "remove")
    assert 1000 not in result["plantillas"]
    assert 2000 in result["plantillas"]


def test_obtener_packs_de_plantilla(tmp_path):
    guardar_pack(crear_pack("a", "Pack A", "Desc", [1000, 2000]), tmp_path)
    guardar_pack(crear_pack("b", "Pack B", "Desc", [1000, 3000]), tmp_path)

    packs = obtener_packs_de_plantilla(1000, tmp_path)
    assert len(packs) == 2

    packs = obtener_packs_de_plantilla(2000, tmp_path)
    assert len(packs) == 1
