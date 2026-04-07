"""
Generador de manifest-templates.json para Sage50BI.
El manifest es el fichero público que la app descarga para saber qué plantillas hay.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


def generar_manifest(
    plantillas: list[dict],
    packs: list[dict],
    clientes_privados: list[dict] = None,
    version_manifest: str = "1.0.0",
    github_user: str = "wertyMSD",
    repo_name: str = "repositorio_Sage50bi",
) -> dict:
    """
    Genera el manifest-templates.json completo.

    Args:
        plantillas: Lista de dicts con datos de plantillas
        packs: Lista de dicts con datos de packs
        clientes_privados: Lista de dicts {codigo, plantillas_ids}
        version_manifest: Versión del manifest
        github_user: Usuario de GitHub
        repo_name: Nombre del repo

    Returns:
        Dict con el manifest completo
    """
    from urllib.parse import quote

    base_url = f"https://raw.githubusercontent.com/{github_user}/{repo_name}/main"

    # Plantillas públicas
    plantillas_manifest = []
    for p in plantillas:
        if p.get("tipo") != "publica":
            continue

        # URL base de la carpeta de la plantilla
        nombre_carpeta = f"{p['id']:04d} - {p['nombre']}"
        url_carpeta = f"{base_url}/publicas/{quote(nombre_carpeta)}/"

        # Archivos
        archivos = {}
        if "archivos" in p:
            for key, arch in p["archivos"].items():
                archivos[key] = {
                    "nombre": arch.get("nombre", ""),
                    "hash_sha256": arch.get("hash_sha256", ""),
                    "opcional": arch.get("opcional", False),
                }

        # Media
        media = p.get("media", {})

        entry = {
            "id": p["id"],
            "nombre": p["nombre"],
            "version": p.get("version", "1.0.0"),
            "tipo": "publica",
            "categoria": p.get("categoria", {}).get("nombre", ""),
            "url_base": url_carpeta,
            "archivos": archivos,
            "preview_url": f"{url_carpeta}{media.get('preview', 'preview.png')}" if media else "",
            "youtube_url": media.get("video_youtube", "") if media else "",
            "recomendaciones": p.get("recomendaciones", []),
            "descripcion": p.get("descripcion", ""),
            "tags": p.get("tags", []),
        }
        plantillas_manifest.append(entry)

    # Packs
    packs_manifest = []
    for pack in packs:
        packs_manifest.append(
            {
                "id": pack.get("id", ""),
                "nombre": pack.get("nombre", ""),
                "descripcion": pack.get("descripcion", ""),
                "icono": pack.get("icono", "📦"),
                "plantillas": pack.get("plantillas", []),
                "total": len(pack.get("plantillas", [])),
            }
        )

    # Clientes privados
    clientes = clientes_privados or []

    manifest = {
        "version_manifest": version_manifest,
        "fecha_generacion": datetime.now().isoformat() + "Z",
        "total_plantillas": len(plantillas_manifest),
        "total_packs": len(packs_manifest),
        "plantillas": plantillas_manifest,
        "packs": packs_manifest,
        "clientes_privados": clientes,
    }

    return manifest


def generar_y_guardar_manifest(
    repo_root: Path,
    plantillas: list[dict],
    packs: list[dict],
    clientes_privados: list[dict] = None,
    version_manifest: str = "1.0.0",
) -> Path:
    """
    Genera y guarda el manifest-templates.json.

    Returns:
        Ruta al archivo guardado
    """
    manifest = generar_manifest(plantillas, packs, clientes_privados, version_manifest)

    manifest_path = repo_root / "manifest-templates.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest_path


def cargar_manifest(repo_root: Path) -> Optional[dict]:
    """Carga el manifest existente si existe."""
    manifest_path = repo_root / "manifest-templates.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def bump_manifest_version(manifest: dict) -> dict:
    """Incrementa la versión PATCH del manifest."""
    from .version_manager import bump_version, BumpType

    version = manifest.get("version_manifest", "1.0.0")
    manifest["version_manifest"] = bump_version(version, BumpType.PATCH)
    manifest["fecha_generacion"] = datetime.now().isoformat() + "Z"
    return manifest
