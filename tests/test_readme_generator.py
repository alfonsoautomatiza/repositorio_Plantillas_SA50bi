"""Tests para gestion/readme_generator.py"""

from pathlib import Path

from gestion.readme_generator import generar_readme, generar_y_guardar_readme
from gestion.schemas import crear_template_json
from gestion.pack_generator import crear_pack


def _plantilla_ejemplo(**kwargs):
    defaults = dict(
        id=1000, nombre="Test Plantilla", descripcion="Descripción de test.", tags=["test"]
    )
    defaults.update(kwargs)
    return crear_template_json(**defaults)


def test_generar_readme_vacio():
    md = generar_readme(
        [], [], {"total_plantillas": 0, "total_packs": 0, "version_manifest": "1.0.0"}
    )
    assert "# " in md
    assert "Plantillas Gratuitas" in md
    assert "0 plantillas" in md


def test_generar_readme_con_plantillas():
    p1 = _plantilla_ejemplo(id=1000, nombre="Clientes")
    p2 = _plantilla_ejemplo(id=2000, nombre="Facturas")
    md = generar_readme(
        [p1, p2], [], {"total_plantillas": 2, "total_packs": 0, "version_manifest": "1.0.0"}
    )
    assert "Clientes" in md
    assert "Facturas" in md
    assert "Informes y Listados" in md
    assert "Facturas y Documentos" in md


def test_generar_readme_con_packs():
    pack = crear_pack("test", "Pack Test", "Descripción pack.", [1000, 2000])
    md = generar_readme(
        [], [pack], {"total_plantillas": 0, "total_packs": 1, "version_manifest": "1.0.0"}
    )
    assert "Pack Test" in md


def test_generar_y_guardar(tmp_path):
    readme_path = generar_y_guardar_readme(
        tmp_path, [], [], {"total_plantillas": 0, "total_packs": 0, "version_manifest": "1.0.0"}
    )
    assert readme_path.exists()
    assert readme_path.name == "README.md"
    content = readme_path.read_text(encoding="utf-8")
    assert "Plantillas Gratuitas" in content
