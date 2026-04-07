"""
Genera los assets de release para Sage50BI.

Este script es auto-contenido (sin dependencias de gestion/) porque
se ejecuta en el repo público via GitHub Actions.

Genera:
  - manifest-tienda.json: catálogo listo para la tienda Sage50BI
  - plantillas.csv: CSV separado por ; para sistemas externos
  - release-notes.md: notas de versión en Markdown

Uso:
    python scripts/generate_release_assets.py

Variables de entorno:
    RELEASE_VERSION: versión explícita (workflow_dispatch)
    GITHUB_REF_TAG: tag del push (ej: v1.0.0)
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB_REPO = "wertyMSD/repositorio_Sage50bi"
GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"
RELEASES_BASE_URL = f"https://github.com/{GITHUB_REPO}/releases/download"

CATEGORIAS = {
    (1, 999): {"nombre": "Personalizadas", "icono": "🔒"},
    (1000, 1999): {"nombre": "Informes y Listados", "icono": "📋"},
    (2000, 2999): {"nombre": "Facturas y Documentos", "icono": "🧾"},
    (3000, 3999): {"nombre": "Balances y Contabilidad", "icono": "📊"},
    (4000, 4999): {"nombre": "Dashboard y Gráficos", "icono": "📈"},
    (5000, 5999): {"nombre": "Reservado futuro", "icono": "🔮"},
}

ORDEN_CATEGORIAS = [
    "Informes y Listados",
    "Facturas y Documentos",
    "Balances y Contabilidad",
    "Dashboard y Gráficos",
]


def get_categoria_por_id(template_id: int) -> dict:
    for (min_id, max_id), cat_data in CATEGORIAS.items():
        if min_id <= template_id <= max_id:
            return {"rango": f"{min_id}-{max_id}", **cat_data}
    return {"rango": "desconocido", "nombre": "Desconocida", "icono": "❓"}


def get_icono_por_nombre(nombre: str) -> str:
    for (_, _), cat_data in CATEGORIAS.items():
        if cat_data["nombre"] == nombre:
            return cat_data["icono"]
    return "📋"


def descripcion_corta(desc: str, max_len: int = 80) -> str:
    if len(desc) <= max_len:
        return desc
    return desc[: max_len - 1].rstrip() + "…"


def cargar_plantillas_publicas() -> list[dict]:
    plantillas = []
    publicas_dir = REPO_ROOT / "publicas"
    if not publicas_dir.exists():
        return plantillas
    for carpeta in sorted(publicas_dir.iterdir()):
        if not carpeta.is_dir():
            continue
        tj = carpeta / "template.json"
        if not tj.exists():
            continue
        with open(tj, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("tipo") != "publica":
            continue
        plantillas.append(data)
    return plantillas


def cargar_packs() -> list[dict]:
    packs = []
    packs_dir = REPO_ROOT / "packs"
    if not packs_dir.exists():
        return packs
    for pf in sorted(packs_dir.glob("pack-*.json")):
        with open(pf, "r", encoding="utf-8") as f:
            packs.append(json.load(f))
    return packs


def preview_url_github(t: dict) -> str:
    nombre_carpeta = f"{t['id']:04d} - {t['nombre']}"
    return f"{GITHUB_BASE_URL}/publicas/{quote(nombre_carpeta)}/preview.png"


def generar_manifest_tienda(plantillas: list[dict], packs: list[dict]) -> dict:
    pt = []
    for p in plantillas:
        cat = p.get("categoria", {})
        cat_nombre = cat.get("nombre", "") if isinstance(cat, dict) else str(cat)
        icono = (
            cat.get("icono", get_icono_por_nombre(cat_nombre))
            if isinstance(cat, dict)
            else get_icono_por_nombre(cat_nombre)
        )
        desc = p.get("descripcion", "")
        media = p.get("media", {})
        s50bi = p.get("sage50bi", {})

        pt.append(
            {
                "id": p["id"],
                "nombre": p["nombre"],
                "slug": p.get("slug", ""),
                "version": p.get("version", "1.0.0"),
                "tipo": "publica",
                "gratuita": p.get("gratuita", True),
                "categoria": cat_nombre,
                "categoria_icono": icono,
                "descripcion": desc,
                "descripcion_corta": descripcion_corta(desc),
                "tags": p.get("tags", []),
                "preview_url": preview_url_github(p),
                "youtube_url": media.get("video_youtube", "") if media else "",
                "sage50bi_min_version": s50bi.get("min_version", "1.0.0"),
                "fecha_actualizacion": p.get("fecha_actualizacion", ""),
                "archivos": p.get("archivos", {}),
            }
        )

    pkt = []
    for pack in packs:
        pkt.append(
            {
                "id": pack.get("id", ""),
                "nombre": pack.get("nombre", ""),
                "slug": pack.get("slug", ""),
                "descripcion": pack.get("descripcion", ""),
                "icono": pack.get("icono", "📦"),
                "plantillas": pack.get("plantillas", []),
                "total": len(pack.get("plantillas", [])),
            }
        )

    return {
        "version_manifest": "1.0.0",
        "fecha_generacion": datetime.now().isoformat() + "Z",
        "total_plantillas": len(pt),
        "total_packs": len(pkt),
        "plantillas": pt,
        "packs": pkt,
    }


def generar_csv(plantillas: list[dict], output: Path) -> None:
    cols = [
        "ID",
        "Nombre",
        "Versión",
        "Categoría",
        "Categoría Icono",
        "Descripción",
        "Tags",
        "Gratuita",
        "Tipo",
        "URL Preview",
        "YouTube",
        "Fecha Actualización",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(cols)
        for p in plantillas:
            cat_nombre = p.get("categoria", "")
            icono = p.get("categoria_icono", "")
            if not icono:
                icono = get_icono_por_nombre(cat_nombre) if isinstance(cat_nombre, str) else ""
            if isinstance(cat_nombre, dict):
                cat_nombre = cat_nombre.get("nombre", "")
            tags = p.get("tags", [])
            tags_str = "|".join(tags) if isinstance(tags, list) else str(tags)
            gratuita = p.get("gratuita", True)
            gratuita = "Sí" if gratuita else "No"
            w.writerow(
                [
                    p.get("id", ""),
                    p.get("nombre", ""),
                    p.get("version", ""),
                    cat_nombre,
                    icono,
                    p.get("descripcion", ""),
                    tags_str,
                    gratuita,
                    p.get("tipo", "publica"),
                    p.get("preview_url", ""),
                    p.get("youtube_url", ""),
                    p.get("fecha_actualizacion", ""),
                ]
            )


def generar_notas(plantillas: list[dict], packs: list[dict], version: str) -> str:
    hoy = datetime.now().strftime("%Y-%m-%d")
    lineas = [
        f"## Sage50BI — Catálogo de Plantillas v{version}",
        "",
        f"**Fecha:** {hoy} | **Total:** {len(plantillas)} plantillas, {len(packs)} packs",
        "",
        "### 📊 Resumen por categoría",
        "",
        "| Categoría | Plantillas |",
        "|-----------|-----------|",
    ]

    conteo: dict[str, int] = {}
    for p in plantillas:
        cat = p.get("categoria", "")
        cn = cat.get("nombre", "") if isinstance(cat, dict) else str(cat)
        conteo[cn] = conteo.get(cn, 0) + 1
    for cn in ORDEN_CATEGORIAS:
        if cn in conteo:
            lineas.append(f"| {get_icono_por_nombre(cn)} {cn} | {conteo[cn]} |")
    lineas.append("")

    lineas += ["### 📋 Detalle de plantillas", ""]
    for cn in ORDEN_CATEGORIAS:
        pcs = [
            p
            for p in plantillas
            if (
                p.get("categoria", {}).get("nombre", "")
                if isinstance(p.get("categoria"), dict)
                else str(p.get("categoria", ""))
            )
            == cn
        ]
        if not pcs:
            continue
        lineas += [
            f"#### {get_icono_por_nombre(cn)} {cn}",
            "",
            "| ID | Nombre | Versión | Descripción |",
            "|----|--------|---------|-------------|",
        ]
        for p in sorted(pcs, key=lambda x: x.get("id", 0)):
            lineas.append(
                f"| {p.get('id', '')} | {p.get('nombre', '')} | "
                f"{p.get('version', '')} | {descripcion_corta(p.get('descripcion', ''), 60)} |"
            )
        lineas.append("")

    if packs:
        lineas += [
            "### 📦 Packs disponibles",
            "",
            "| Pack | Plantillas | Descripción |",
            "|------|-----------|-------------|",
        ]
        for pack in packs:
            lineas.append(
                f"| {pack.get('nombre', '')} | {len(pack.get('plantillas', []))} | "
                f"{descripcion_corta(pack.get('descripcion', ''), 60)} |"
            )
        lineas.append("")

    lineas += [
        "### 🔗 Descarga via API",
        "",
        "```bash",
        f"# Descargar manifest de la tienda",
        f"curl -L -o manifest-tienda.json {RELEASES_BASE_URL}/v{version}/manifest-tienda.json",
        "",
        f"# Descargar CSV de plantillas",
        f"curl -L -o plantillas.csv {RELEASES_BASE_URL}/v{version}/plantillas.csv",
        "```",
        "",
    ]
    return "\n".join(lineas)


def get_version() -> str:
    """Determina la versión desde env vars o tag."""
    explicit = os.environ.get("RELEASE_VERSION", "").strip()
    if explicit:
        return explicit.lstrip("v")
    ref_tag = os.environ.get("GITHUB_REF_TAG", "").strip()
    if ref_tag:
        return ref_tag.lstrip("v")
    return "1.0.0"


def main():
    version = get_version()
    print(f"Generando assets para release v{version}...")

    plantillas = cargar_plantillas_publicas()
    packs = cargar_packs()
    print(f"  Plantillas: {len(plantillas)}")
    print(f"  Packs: {len(packs)}")

    # Generar manifest-tienda.json
    manifest = generar_manifest_tienda(plantillas, packs)
    manifest_path = REPO_ROOT / "manifest-tienda.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  [OK] manifest-tienda.json ({manifest_path.stat().st_size} bytes)")

    # Generar plantillas.csv
    csv_path = REPO_ROOT / "plantillas.csv"
    generar_csv(manifest["plantillas"], csv_path)
    print(f"  [OK] plantillas.csv ({csv_path.stat().st_size} bytes)")

    # Generar release-notes.md
    notas = generar_notas(plantillas, packs, version)
    notas_path = REPO_ROOT / "release-notes.md"
    with open(notas_path, "w", encoding="utf-8") as f:
        f.write(notas)
    print(f"  [OK] release-notes.md ({notas_path.stat().st_size} bytes)")

    print(f"\nAssets generados correctamente para v{version}.")


if __name__ == "__main__":
    main()
