"""
Catálogo de Plantillas Sage50BI

Módulo Streamlit independiente para explorar, buscar e instalar plantillas.
Importable sin Streamlit para testing.

Módulos:
- manifest_reader: Lectura remota de manifest-templates.json
- recomendaciones: Motor de recomendaciones por tags y categoría
- instalador: Instalación y actualización de plantillas
- catalogo: Página principal del catálogo (UI Streamlit)
- detalle: Vista detalle de plantilla (UI Streamlit)
"""

from .manifest_reader import ManifestReader
from .recomendaciones import recomendar_por_tags, recomendar_por_manifest, recomendar_por_categoria
from .instalador import Instalador

__version__ = "1.0.0"
__all__ = [
    "ManifestReader",
    "Instalador",
    "recomendar_por_tags",
    "recomendar_por_manifest",
    "recomendar_por_categoria",
]

# URL por defecto del manifest remoto
DEFAULT_MANIFEST_URL = "https://wertymsd.github.io/repositorio_Sage50bi/manifest-templates.json"
