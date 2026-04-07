"""
Gestión de Plantillas Sage50BI

Módulos:
- schemas: Validación y creación de template.json
- cifrado: Cifrado/descifrado de archivos con Fernet
- sql_validator: Validación de SQL (solo SELECT permitido)
- version_manager: Gestión de versiones semánticas
- gestor: Lógica de negocio principal
- gestion: GUI PySimpleGUI
- readme_generator: Generador de README.md
- mkdocs_generator: Generador de docs/ MkDocs
- manifest_generator: Generador de manifest-templates.json
- youtube_generator: Auto-generador de texto YouTube
- pack_generator: Gestión de packs/bundles
"""

from .schemas import (
    crear_template_json,
    validar_template_json,
    cargar_template_json,
    guardar_template_json,
    get_categoria_por_id,
    es_plantilla_privada,
    CATEGORIAS,
    TemplateValidationError,
)

from .cifrado import (
    cifrar_archivo_publico,
    descifrar_archivo_publico,
    cifrar_archivo_privado,
    descifrar_archivo_privado,
    hash_licencia,
    verificar_integridad,
    verificar_cifrado_roundtrip,
    CifradoError,
)

from .sql_validator import (
    validar_sql,
    validar_archivo_sql,
    es_sql_valido,
    validar_y_lanzar,
    SQLValidationError,
)

__version__ = "1.0.0"
__all__ = [
    # Schemas
    "crear_template_json",
    "validar_template_json",
    "cargar_template_json",
    "guardar_template_json",
    "get_categoria_por_id",
    "es_plantilla_privada",
    "CATEGORIAS",
    "TemplateValidationError",
    # Cifrado
    "cifrar_archivo_publico",
    "descifrar_archivo_publico",
    "cifrar_archivo_privado",
    "descifrar_archivo_privado",
    "hash_licencia",
    "verificar_integridad",
    "verificar_cifrado_roundtrip",
    "CifradoError",
    # SQL
    "validar_sql",
    "validar_archivo_sql",
    "es_sql_valido",
    "validar_y_lanzar",
    "SQLValidationError",
]
