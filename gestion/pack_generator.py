"""
Gestión de Packs/Bundles de plantillas Sage50BI.
Los packs agrupan plantillas relacionadas para instalación conjunta.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


# === PACKS PREDEFINIDOS ===

PACKS_PREDEFINIDOS = {
    "pack-gestion-comercial": {
        "nombre": "Pack Gestión Comercial",
        "descripcion": "Todo lo que necesitas para gestionar clientes, facturas y albaranes en Sage50BI.",
        "icono": "📦",
        "categorias_incluidas": ["Informes y Listados", "Facturas y Documentos"],
    },
    "pack-contabilidad-completa": {
        "nombre": "Pack Contabilidad Completa",
        "descripcion": "Balances, sumas y saldos, cuenta de resultados y más para tu contabilidad.",
        "icono": "📊",
        "categorias_incluidas": ["Balances y Contabilidad"],
    },
    "pack-dashboards": {
        "nombre": "Pack Dashboards",
        "descripcion": "Cuadros de mando interactivos con Streamlit para visualizar tus datos.",
        "icono": "📈",
        "categorias_incluidas": ["Dashboard y Gráficos"],
    },
}


def crear_pack(
    pack_id: str,
    nombre: str,
    descripcion: str,
    plantillas: list[int],
    icono: str = "📦",
    preview: str = "",
) -> dict:
    """
    Crea un nuevo pack de plantillas.

    Args:
        pack_id: ID único del pack (ej: "pack-gestion-comercial")
        nombre: Nombre visible del pack
        descripcion: Descripción del pack
        plantillas: Lista de IDs de plantillas incluidas
        icono: Emoji del pack
        preview: Nombre del archivo preview (opcional)

    Returns:
        Diccionario con la definición del pack
    """
    if not pack_id.startswith("pack-"):
        pack_id = f"pack-{pack_id}"

    slug = pack_id.lower().replace(" ", "-")

    return {
        "id": pack_id,
        "nombre": nombre,
        "slug": slug,
        "descripcion": descripcion,
        "icono": icono,
        "plantillas": sorted(plantillas),
        "total_plantillas": len(plantillas),
        "preview": preview or f"{slug}.png",
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
        "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d"),
    }


def validar_pack(pack_data: dict, plantillas_existentes: set[int]) -> list[str]:
    """
    Valida un pack.

    Args:
        pack_data: Datos del pack
        plantillas_existentes: Set de IDs de plantillas que existen

    Returns:
        Lista de errores (vacía si es válido)
    """
    errores = []

    # Campos requeridos
    campos_requeridos = ["id", "nombre", "descripcion", "plantillas"]
    for campo in campos_requeridos:
        if campo not in pack_data:
            errores.append(f"Campo requerido faltante: {campo}")

    if errores:
        return errores

    # Validar ID
    if not pack_data["id"].startswith("pack-"):
        errores.append(f"ID de pack debe empezar con 'pack-': {pack_data['id']}")

    # Validar plantillas
    if not isinstance(pack_data["plantillas"], list):
        errores.append("Campo 'plantillas' debe ser una lista")
    elif len(pack_data["plantillas"]) < 2:
        errores.append("Un pack debe contener al menos 2 plantillas")
    else:
        # Verificar que las plantillas existen
        for pid in pack_data["plantillas"]:
            if pid not in plantillas_existentes:
                errores.append(f"Plantilla {pid} no existe")

    return errores


def guardar_pack(pack_data: dict, packs_dir: Path) -> Path:
    """
    Guarda un pack en el directorio de packs.

    Returns:
        Ruta al archivo guardado
    """
    packs_dir.mkdir(parents=True, exist_ok=True)

    pack_id = pack_data["id"]
    path = packs_dir / f"{pack_id}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack_data, f, ensure_ascii=False, indent=2)

    return path


def cargar_pack(path: Path) -> dict:
    """Carga un pack desde archivo."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_packs(packs_dir: Path) -> list[dict]:
    """
    Lista todos los packs disponibles.

    Returns:
        Lista de diccionarios con info básica de cada pack
    """
    packs = []

    if not packs_dir.exists():
        return packs

    for path in packs_dir.glob("pack-*.json"):
        try:
            pack = cargar_pack(path)
            packs.append(
                {
                    "id": pack["id"],
                    "nombre": pack["nombre"],
                    "descripcion": pack["descripcion"],
                    "icono": pack.get("icono", "📦"),
                    "total_plantillas": len(pack.get("plantillas", [])),
                    "plantillas": pack.get("plantillas", []),
                }
            )
        except Exception:
            continue

    return sorted(packs, key=lambda p: p["nombre"])


def actualizar_pack(pack_data: dict, plantilla_id: int, accion: str = "add") -> dict:
    """
    Añade o quita una plantilla de un pack.

    Args:
        pack_data: Datos del pack
        plantilla_id: ID de la plantilla
        accion: "add" para añadir, "remove" para quitar

    Returns:
        Pack actualizado
    """
    plantillas = set(pack_data.get("plantillas", []))

    if accion == "add":
        plantillas.add(plantilla_id)
    elif accion == "remove":
        plantillas.discard(plantilla_id)

    pack_data["plantillas"] = sorted(plantillas)
    pack_data["total_plantillas"] = len(plantillas)
    pack_data["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d")

    return pack_data


def obtener_packs_de_plantilla(plantilla_id: int, packs_dir: Path) -> list[str]:
    """
    Obtiene los IDs de packs que contienen una plantilla.

    Returns:
        Lista de IDs de packs
    """
    packs_ids = []

    for pack in listar_packs(packs_dir):
        if plantilla_id in pack["plantillas"]:
            packs_ids.append(pack["id"])

    return packs_ids


def generar_pack_para_manifest(pack_data: dict) -> dict:
    """
    Genera la entrada de pack para manifest-templates.json.
    """
    return {
        "id": pack_data["id"],
        "nombre": pack_data["nombre"],
        "plantillas": pack_data.get("plantillas", []),
        "total": len(pack_data.get("plantillas", [])),
    }


if __name__ == "__main__":
    # Test
    pack = crear_pack(
        pack_id="gestion-comercial",
        nombre="Pack Gestión Comercial",
        descripcion="Todo lo que necesitas para gestionar clientes y facturas.",
        plantillas=[1000, 1001, 2000, 2001],
        icono="📦",
    )
    print(json.dumps(pack, indent=2, ensure_ascii=False))
