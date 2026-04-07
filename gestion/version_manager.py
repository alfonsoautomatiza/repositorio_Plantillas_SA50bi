"""
Gestión de versiones semánticas para plantillas Sage50BI.
Reutiliza el modelo partial/full de libwertyupdate.py.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class BumpType(Enum):
    """Tipo de incremento de versión."""

    PATCH = "patch"  # Fix menor: 1.0.0 → 1.0.1
    MINOR = "minor"  # Nueva funcionalidad: 1.0.0 → 1.1.0
    MAJOR = "major"  # Cambio incompatible: 1.0.0 → 2.0.0


@dataclass
class Version:
    """Representa una versión semántica."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "Version") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "Version") -> bool:
        return self == other or self > other

    @classmethod
    def from_string(cls, version_str: str) -> "Version":
        """Parsea una versión desde string 'X.Y.Z'."""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str.strip())
        if not match:
            raise ValueError(f"Versión inválida: {version_str}. Formato esperado: X.Y.Z")
        return cls(major=int(match.group(1)), minor=int(match.group(2)), patch=int(match.group(3)))

    def bump(self, bump_type: BumpType) -> "Version":
        """Devuelve una nueva versión incrementada."""
        if bump_type == BumpType.MAJOR:
            return Version(self.major + 1, 0, 0)
        elif bump_type == BumpType.MINOR:
            return Version(self.major, self.minor + 1, 0)
        else:  # PATCH
            return Version(self.major, self.minor, self.patch + 1)


def parse_version(version_str: str) -> Version:
    """Parsea una versión desde string."""
    return Version.from_string(version_str)


def bump_version(version_str: str, bump_type: BumpType) -> str:
    """
    Incrementa una versión.

    Args:
        version_str: Versión actual (ej: "1.0.0")
        bump_type: Tipo de incremento

    Returns:
        Nueva versión como string
    """
    version = Version.from_string(version_str)
    new_version = version.bump(bump_type)
    return str(new_version)


def comparar_versiones(v1: str, v2: str) -> int:
    """
    Compara dos versiones.

    Returns:
        -1 si v1 < v2
         0 si v1 == v2
         1 si v1 > v2
    """
    ver1 = Version.from_string(v1)
    ver2 = Version.from_string(v2)

    if ver1 < ver2:
        return -1
    elif ver1 > ver2:
        return 1
    return 0


def version_es_mayor(nueva: str, actual: str) -> bool:
    """Devuelve True si la nueva versión es mayor que la actual."""
    return comparar_versiones(nueva, actual) > 0


def sugerir_bump_type(descripcion_cambio: str) -> BumpType:
    """
    Sugiere el tipo de bump basado en la descripción del cambio.

    Keywords que sugieren cada tipo:
    - MAJOR: "breaking", "incompatible", "rediseño", "redesign"
    - MINOR: "nuevo", "new", "añadir", "add", "feature", "funcionalidad"
    - PATCH: "fix", "corregir", "bug", "error", "ajuste", "mejora menor"
    """
    desc_lower = descripcion_cambio.lower()

    # MAJOR keywords
    major_keywords = ["breaking", "incompatible", "rediseño", "redesign", "major"]
    if any(kw in desc_lower for kw in major_keywords):
        return BumpType.MAJOR

    # MINOR keywords
    minor_keywords = ["nuevo", "new", "añadir", "add", "feature", "funcionalidad", "soporte"]
    if any(kw in desc_lower for kw in minor_keywords):
        return BumpType.MINOR

    # Default: PATCH
    return BumpType.PATCH


@dataclass
class ChangelogEntry:
    """Entrada del changelog."""

    version: str
    fecha: str
    cambios: str

    def to_dict(self) -> dict:
        return {"version": self.version, "fecha": self.fecha, "cambios": self.cambios}

    @classmethod
    def from_dict(cls, data: dict) -> "ChangelogEntry":
        return cls(version=data["version"], fecha=data["fecha"], cambios=data["cambios"])


def crear_changelog_entry(version: str, cambios: str, fecha: Optional[str] = None) -> dict:
    """
    Crea una entrada de changelog.

    Args:
        version: Nueva versión
        cambios: Descripción de los cambios
        fecha: Fecha (default: hoy)

    Returns:
        Diccionario con la entrada del changelog
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    return ChangelogEntry(version=version, fecha=fecha, cambios=cambios).to_dict()


def actualizar_template_version(
    template_data: dict, bump_type: BumpType, descripcion_cambios: str
) -> dict:
    """
    Actualiza la versión de un template y añade entrada al changelog.

    Args:
        template_data: Diccionario del template.json
        bump_type: Tipo de incremento
        descripcion_cambios: Descripción de los cambios para el changelog

    Returns:
        Template actualizado (modifica in-place y devuelve)
    """
    # Bump version
    version_actual = template_data["version"]
    version_nueva = bump_version(version_actual, bump_type)
    template_data["version"] = version_nueva

    # Actualizar fecha
    hoy = datetime.now().strftime("%Y-%m-%d")
    template_data["fecha_actualizacion"] = hoy

    # Añadir al changelog
    nueva_entrada = crear_changelog_entry(version_nueva, descripcion_cambios, hoy)

    if "changelog" not in template_data:
        template_data["changelog"] = []

    # Insertar al principio (más reciente primero)
    template_data["changelog"].insert(0, nueva_entrada)

    return template_data


def obtener_ultima_version_changelog(template_data: dict) -> Optional[str]:
    """Obtiene la última versión del changelog."""
    changelog = template_data.get("changelog", [])
    if changelog:
        return changelog[0].get("version")
    return template_data.get("version")


# === VERSIÓN DEL MANIFEST ===


def bump_manifest_version(manifest_data: dict, bump_type: BumpType = BumpType.PATCH) -> dict:
    """
    Incrementa la versión del manifest global.

    Args:
        manifest_data: Diccionario del manifest-templates.json
        bump_type: Tipo de incremento (default: PATCH)

    Returns:
        Manifest actualizado
    """
    version_actual = manifest_data.get("version_manifest", "1.0.0")
    version_nueva = bump_version(version_actual, bump_type)

    manifest_data["version_manifest"] = version_nueva
    manifest_data["fecha_generacion"] = datetime.now().isoformat() + "Z"

    return manifest_data


if __name__ == "__main__":
    # Tests rápidos
    print("=== Tests de Version Manager ===")

    # Test parsing
    v = Version.from_string("1.2.3")
    print(f"Parsed: {v}")

    # Test bump
    print(f"Bump PATCH: {v.bump(BumpType.PATCH)}")
    print(f"Bump MINOR: {v.bump(BumpType.MINOR)}")
    print(f"Bump MAJOR: {v.bump(BumpType.MAJOR)}")

    # Test comparación
    print(f"1.0.0 < 1.0.1: {Version.from_string('1.0.0') < Version.from_string('1.0.1')}")
    print(f"2.0.0 > 1.9.9: {Version.from_string('2.0.0') > Version.from_string('1.9.9')}")

    # Test sugerencia
    print(f"Sugerencia 'nuevo filtro': {sugerir_bump_type('nuevo filtro')}")
    print(f"Sugerencia 'fix error SQL': {sugerir_bump_type('fix error SQL')}")
    print(f"Sugerencia 'breaking change': {sugerir_bump_type('breaking change')}")
