"""Tests para gestion/version_manager.py"""

from gestion.version_manager import (
    Version,
    BumpType,
    bump_version,
    comparar_versiones,
    version_es_mayor,
    sugerir_bump_type,
    crear_changelog_entry,
    actualizar_template_version,
)


# === Version ===


def test_parse():
    v = Version.from_string("1.2.3")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


def test_str():
    v = Version(1, 2, 3)
    assert str(v) == "1.2.3"


def test_parse_invalido():
    try:
        Version.from_string("1.2")
        assert False
    except ValueError:
        pass


def test_igualdad():
    assert Version(1, 0, 0) == Version(1, 0, 0)


def test_comparacion():
    assert Version(1, 0, 0) < Version(1, 0, 1)
    assert Version(1, 1, 0) < Version(2, 0, 0)
    assert Version(2, 0, 0) > Version(1, 9, 9)


# === Bump ===


def test_bump_patch():
    assert bump_version("1.0.0", BumpType.PATCH) == "1.0.1"


def test_bump_minor():
    assert bump_version("1.0.0", BumpType.MINOR) == "1.1.0"


def test_bump_major():
    assert bump_version("1.0.0", BumpType.MAJOR) == "2.0.0"


def test_bump_minor_resetea_patch():
    assert bump_version("1.2.5", BumpType.MINOR) == "1.3.0"


def test_bump_major_resetea():
    assert bump_version("3.7.9", BumpType.MAJOR) == "4.0.0"


# === Comparar ===


def test_comparar():
    assert comparar_versiones("1.0.0", "1.0.1") == -1
    assert comparar_versiones("1.0.1", "1.0.0") == 1
    assert comparar_versiones("1.0.0", "1.0.0") == 0


def test_es_mayor():
    assert version_es_mayor("1.0.1", "1.0.0") is True
    assert version_es_mayor("1.0.0", "1.0.1") is False


# === Sugerir bump ===


def test_sugerir_major():
    assert sugerir_bump_type("breaking change en API") == BumpType.MAJOR


def test_sugerir_minor():
    assert sugerir_bump_type("nuevo filtro de búsqueda") == BumpType.MINOR


def test_sugerir_patch():
    assert sugerir_bump_type("fix error en SQL") == BumpType.PATCH


# === Changelog ===


def test_crear_changelog():
    entry = crear_changelog_entry("1.0.1", "Fix menor")
    assert entry["version"] == "1.0.1"
    assert entry["cambios"] == "Fix menor"
    assert "fecha" in entry


def test_actualizar_template():
    template = {
        "version": "1.0.0",
        "fecha_actualizacion": "2026-01-01",
        "changelog": [],
    }
    result = actualizar_template_version(template, BumpType.PATCH, "Fix SQL")
    assert result["version"] == "1.0.1"
    assert len(result["changelog"]) == 1
    assert result["changelog"][0]["version"] == "1.0.1"
