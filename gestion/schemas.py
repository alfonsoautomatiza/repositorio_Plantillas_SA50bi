"""
Schemas y validación para template.json de plantillas Sage50BI.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from unidecode import unidecode


# === CONSTANTES DE CATEGORÍAS ===

CATEGORIAS = {
    (1, 999): {
        "nombre": "Personalizadas",
        "icono": "🔒",
        "descripcion": "Plantillas privadas por cliente",
    },
    (1000, 1999): {
        "nombre": "Informes y Listados",
        "icono": "📋",
        "descripcion": "Listados de clientes, proveedores, artículos...",
    },
    (2000, 2999): {
        "nombre": "Facturas y Documentos",
        "icono": "🧾",
        "descripcion": "Modelos de facturas, albaranes, pedidos...",
    },
    (3000, 3999): {
        "nombre": "Balances y Contabilidad",
        "icono": "📊",
        "descripcion": "Balances, cuentas de resultados, sumas y saldos...",
    },
    (4000, 4999): {
        "nombre": "Dashboard y Gráficos",
        "icono": "📈",
        "descripcion": "Cuadros de mando Streamlit, gráficos...",
    },
    (5000, 5999): {
        "nombre": "Reservado futuro",
        "icono": "🔮",
        "descripcion": "Reservado para futuras categorías",
    },
}


def get_categoria_por_id(template_id: int) -> dict:
    """Devuelve la categoría correspondiente a un ID de plantilla."""
    for (min_id, max_id), categoria in CATEGORIAS.items():
        if min_id <= template_id <= max_id:
            return {"rango": f"{min_id}-{max_id}", **categoria}
    return {
        "rango": "desconocido",
        "nombre": "Desconocida",
        "icono": "❓",
        "descripcion": "Categoría no definida",
    }


def es_plantilla_privada(template_id: int) -> bool:
    """Devuelve True si el ID corresponde a una plantilla privada (1-999)."""
    return 1 <= template_id <= 999


# === SCHEMA TEMPLATE.JSON ===

TEMPLATE_SCHEMA = {
    "required": [
        "id",
        "nombre",
        "slug",
        "version",
        "categoria",
        "descripcion",
        "tags",
        "gratuita",
        "tipo",
        "archivos",
        "fecha_creacion",
        "fecha_actualizacion",
    ],
    "optional": [
        "descripcion_larga",
        "media",
        "recomendaciones",
        "packs",
        "sage50bi",
        "youtube_seo",
        "open_graph",
        "changelog",
        "cliente",
    ],
}


@dataclass
class TemplateArchivo:
    """Representa un archivo de la plantilla."""

    nombre: str
    cifrado: bool = True
    hash_sha256: str = ""
    opcional: bool = False


@dataclass
class TemplateMedia:
    """Metadatos multimedia de la plantilla."""

    preview: str = "preview.png"
    video_youtube: str = ""
    video_miniatura: str = ""


@dataclass
class TemplateCategoria:
    """Categoría de la plantilla."""

    rango: str
    nombre: str
    icono: str = ""


@dataclass
class TemplateCliente:
    """Datos del cliente para plantillas privadas."""

    codigo: str
    clave_hash: str = ""


@dataclass
class TemplateYoutubeSEO:
    """Texto auto-generado para YouTube."""

    titulo: str = ""
    descripcion: str = ""
    tags_youtube: list = field(default_factory=list)


@dataclass
class TemplateOpenGraph:
    """Meta tags Open Graph para SEO."""

    title: str = ""
    description: str = ""
    image: str = "preview.png"
    type: str = "article"


@dataclass
class TemplateChangelog:
    """Entrada del changelog."""

    version: str
    fecha: str
    cambios: str


@dataclass
class Template:
    """Modelo completo de una plantilla Sage50BI."""

    id: int
    nombre: str
    slug: str
    version: str
    categoria: TemplateCategoria
    descripcion: str
    tags: list
    gratuita: bool
    tipo: str  # "publica" o "privada"
    archivos: dict  # {"sql": TemplateArchivo, "dashboard": TemplateArchivo}
    fecha_creacion: str
    fecha_actualizacion: str

    # Opcionales
    descripcion_larga: str = ""
    media: Optional[TemplateMedia] = None
    recomendaciones: list = field(default_factory=list)
    packs: list = field(default_factory=list)
    sage50bi: dict = field(
        default_factory=lambda: {"min_version": "1.0.0", "compatibilidad": ["sage50bi"]}
    )
    youtube_seo: Optional[TemplateYoutubeSEO] = None
    open_graph: Optional[TemplateOpenGraph] = None
    changelog: list = field(default_factory=list)
    cliente: Optional[TemplateCliente] = None  # Solo para privadas


# === VALIDACIÓN ===


class TemplateValidationError(Exception):
    """Error de validación de template.json."""

    pass


def validar_template_json(data: dict) -> list[str]:
    """
    Valida un diccionario de template.json.
    Devuelve lista de errores (vacía si es válido).
    """
    errores = []

    # Campos requeridos
    for campo in TEMPLATE_SCHEMA["required"]:
        if campo not in data:
            errores.append(f"Campo requerido faltante: {campo}")

    if errores:
        return errores  # Si faltan campos requeridos, no seguir validando

    # Validar ID
    if not isinstance(data["id"], int) or data["id"] < 1:
        errores.append(f"ID debe ser entero positivo, recibido: {data['id']}")

    # Validar slug
    slug_pattern = r"^[0-9]+-[a-z0-9-]+$"
    if not re.match(slug_pattern, data["slug"]):
        errores.append(f"Slug inválido: {data['slug']}. Formato: NNNN-nombre-en-minusculas")

    # Validar versión semántica
    version_pattern = r"^\d+\.\d+\.\d+$"
    if not re.match(version_pattern, data["version"]):
        errores.append(f"Versión inválida: {data['version']}. Formato: X.Y.Z")

    # Validar tipo
    if data["tipo"] not in ["publica", "privada"]:
        errores.append(f"Tipo debe ser 'publica' o 'privada', recibido: {data['tipo']}")

    # Validar coherencia ID vs tipo
    es_privada = es_plantilla_privada(data["id"])
    if es_privada and data["tipo"] != "privada":
        errores.append(f"ID {data['id']} es de rango privado (1-999) pero tipo es '{data['tipo']}'")
    if not es_privada and data["tipo"] == "privada":
        errores.append(f"ID {data['id']} es de rango público pero tipo es 'privada'")

    # Validar tags
    if not isinstance(data["tags"], list) or len(data["tags"]) == 0:
        errores.append("Tags debe ser lista no vacía")

    # Validar archivos
    if "archivos" in data:
        if "sql" not in data["archivos"]:
            errores.append("Archivos debe contener al menos 'sql'")

    # Validar cliente para privadas
    if data["tipo"] == "privada":
        if "cliente" not in data or not data["cliente"]:
            errores.append("Plantillas privadas requieren campo 'cliente'")
        elif "codigo" not in data["cliente"]:
            errores.append("Cliente debe tener campo 'codigo'")

    # Validar fechas
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    for campo_fecha in ["fecha_creacion", "fecha_actualizacion"]:
        if not re.match(date_pattern, data[campo_fecha]):
            errores.append(f"{campo_fecha} debe tener formato YYYY-MM-DD")

    return errores


def crear_template_json(
    id: int,
    nombre: str,
    descripcion: str,
    tags: list[str],
    tiene_dashboard: bool = True,
    video_youtube: str = "",
    cliente_codigo: str = "",
    cliente_clave_hash: str = "",
    recomendaciones: list[int] = None,
    packs: list[str] = None,
) -> dict:
    """
    Crea un template.json válido con valores por defecto inteligentes.
    """
    # Determinar tipo y categoría
    es_privada = es_plantilla_privada(id)
    tipo = "privada" if es_privada else "publica"
    categoria = get_categoria_por_id(id)

    # Generar slug
    slug_nombre = re.sub(r"[^a-z0-9]+", "-", unidecode(nombre.lower())).strip("-")
    slug = f"{id:04d}-{slug_nombre}"

    # Fecha actual
    hoy = datetime.now().strftime("%Y-%m-%d")

    # Archivos
    archivos = {
        "sql": {"nombre": "template.sql", "cifrado": True, "hash_sha256": "", "opcional": False}
    }
    if tiene_dashboard:
        archivos["dashboard"] = {
            "nombre": "dashboard.py",
            "cifrado": True,
            "hash_sha256": "",
            "opcional": True,
        }

    template = {
        "id": id,
        "nombre": nombre,
        "slug": slug,
        "version": "1.0.0",
        "categoria": {
            "rango": categoria["rango"],
            "nombre": categoria["nombre"],
            "icono": categoria["icono"],
        },
        "descripcion": descripcion,
        "descripcion_larga": "",
        "tags": tags,
        "gratuita": not es_privada,
        "tipo": tipo,
        "archivos": archivos,
        "media": {
            "preview": "preview.png",
            "video_youtube": video_youtube,
            "video_miniatura": f"https://img.youtube.com/vi/{video_youtube.split('v=')[-1]}/0.jpg"
            if "v=" in video_youtube
            else "",
        },
        "recomendaciones": recomendaciones or [],
        "packs": packs or [],
        "sage50bi": {"min_version": "1.0.0", "compatibilidad": ["sage50bi"]},
        "fecha_creacion": hoy,
        "fecha_actualizacion": hoy,
        "changelog": [{"version": "1.0.0", "fecha": hoy, "cambios": "Versión inicial"}],
    }

    # Añadir campos privados si aplica
    if es_privada:
        template["cliente"] = {"codigo": cliente_codigo, "clave_hash": cliente_clave_hash}
    else:
        # Generar YouTube SEO y Open Graph para públicas
        template["youtube_seo"] = {
            "titulo": f"{nombre} — Plantilla gratuita para Sage50BI",
            "descripcion": f"📊 Plantilla gratuita para Sage50BI de ALCA TIC.\n\n{descripcion}\n\n✅ Gratuita ✅ Actualización automática ✅ Sin registro\n\n🔗 Más plantillas: https://wertymsd.github.io/repositorio_Sage50bi/\n🏢 ALCA TIC: https://pedironline.com",
            "tags_youtube": ["sage50", "sage50bi", "plantillas sql"] + tags[:3],
        }
        template["open_graph"] = {
            "title": f"{nombre} — Plantilla gratuita Sage50BI",
            "description": descripcion[:160] if len(descripcion) > 160 else descripcion,
            "image": "preview.png",
            "type": "article",
        }

    return template


def cargar_template_json(path: Path) -> dict:
    """Carga y valida un template.json desde archivo."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errores = validar_template_json(data)
    if errores:
        raise TemplateValidationError(f"Template inválido en {path}:\n" + "\n".join(errores))

    return data


def guardar_template_json(data: dict, path: Path) -> None:
    """Guarda un template.json validándolo primero."""
    errores = validar_template_json(data)
    if errores:
        raise TemplateValidationError("Template inválido:\n" + "\n".join(errores))

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
