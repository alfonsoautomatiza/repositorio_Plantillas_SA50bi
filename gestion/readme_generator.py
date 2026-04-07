"""
Generador de README.md auto-generado para el repositorio de plantillas Sage50BI.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


def generar_readme(
    plantillas: list[dict],
    packs: list[dict],
    stats: dict,
) -> str:
    """
    Genera el README.md completo a partir de las plantillas existentes.

    Args:
        plantillas: Lista de dicts con datos de plantillas
        packs: Lista de dicts con datos de packs
        stats: Estadísticas del repositorio

    Returns:
        String con el README.md completo
    """
    total = stats.get("total_plantillas", 0)
    total_packs = stats.get("total_packs", 0)
    manifest_version = stats.get("version_manifest", "1.0.0")

    # Separar públicas por categoría
    publicas = [p for p in plantillas if p.get("tipo") == "publica"]
    privadas = [p for p in plantillas if p.get("tipo") == "privada"]

    # Ordenar por ID
    publicas.sort(key=lambda p: p["id"])

    # Agrupar por categoría
    por_categoria = {}
    for p in publicas:
        cat = p.get("categoria", {}).get("nombre", "Sin categoría")
        icono = p.get("categoria", {}).get("icono", "📋")
        if cat not in por_categoria:
            por_categoria[cat] = {"icono": icono, "plantillas": []}
        por_categoria[cat]["plantillas"].append(p)

    # === CONSTRUIR README ===

    lines = []

    # Header
    lines.append("# 🏢 Plantillas Gratuitas para Sage50BI — ALCA TIC")
    lines.append("")
    lines.append(
        f"[![Plantillas](https://img.shields.io/badge/Plantillas-{total}-blue)](https://wertymsd.github.io/repositorio_Sage50bi/)"
    )
    lines.append(
        f"[![Packs](https://img.shields.io/badge/Packs-{total_packs}-purple)](https://wertymsd.github.io/repositorio_Sage50bi/packs/)"
    )
    lines.append(f"[![Versión](https://img.shields.io/badge/Manifest-{manifest_version}-green)]()")
    lines.append("[![Gratis](https://img.shields.io/badge/Gratuitas-100%25-success)]()")
    lines.append(
        "[![Sage50BI](https://img.shields.io/badge/Sage50BI-Compatible-orange)](https://pedironline.com)"
    )
    lines.append("")

    # Advertencia
    lines.append("> ⚠️ **Este archivo se genera automáticamente.** No editar manualmente.")
    lines.append("> Para modificar, use el tool de gestión: `python gestion/gestion.py`")
    lines.append("")

    # Intro SEO
    lines.append("## ¿Qué son estas plantillas?")
    lines.append("")
    lines.append(f"Colección de **{total} plantillas SQL y dashboards Streamlit** gratuitas para")
    lines.append(
        "[Sage50BI](https://pedironline.com), la solución de Business Intelligence para Sage50 de ALCA TIC."
    )
    lines.append("")
    lines.append("Cada plantilla incluye:")
    lines.append("- 📊 Consultas SQL optimizadas para Sage50")
    lines.append("- 🐍 Dashboards interactivos con Streamlit")
    lines.append("- 🎥 Vídeos explicativos en YouTube")
    lines.append("- 🔄 Actualización automática desde la aplicación")
    lines.append("- 📦 Packs temáticos para instalar varias a la vez")
    lines.append("")

    # SEO extra para IA
    lines.append("### ¿Para quién son?")
    lines.append("")
    lines.append(
        "- **Gestores administrativos** que usan Sage50 y necesitan informes personalizados"
    )
    lines.append("- **Contables** que quieren automatizar listados, balances y facturas")
    lines.append("- **Empresas** que buscan dashboards de sus datos de Sage50 sin programar")
    lines.append("- **Consultores SAP/Sage** que necesitan plantillas listas para usar")
    lines.append("")

    # Packs
    if packs:
        lines.append("## 📦 Packs Destacados")
        lines.append("")
        lines.append("| Pack | Plantillas | Descripción |")
        lines.append("|------|-----------|-------------|")
        for pack in packs:
            icono = pack.get("icono", "📦")
            nombre = pack.get("nombre", pack.get("id", ""))
            total_p = pack.get("total_plantillas", len(pack.get("plantillas", [])))
            desc = pack.get("descripcion", "")
            lines.append(f"| {icono} {nombre} | {total_p} | {desc} |")
        lines.append("")

    # Catálogo por categoría
    lines.append("## 📋 Catálogo de Plantillas")
    lines.append("")

    for cat_nombre, cat_data in por_categoria.items():
        icono = cat_data["icono"]
        lines.append(f"### {icono} {cat_nombre}")
        lines.append("")
        lines.append("| # | Plantilla | Versión | Descripción | Tags | YouTube |")
        lines.append("|---|-----------|---------|-------------|------|---------|")

        for p in cat_data["plantillas"]:
            pid = p["id"]
            nombre = p["nombre"]
            version = p.get("version", "1.0.0")
            desc = p.get("descripcion", "")[:80]
            if len(p.get("descripcion", "")) > 80:
                desc += "..."
            tags = " ".join(f"`{t}`" for t in p.get("tags", [])[:3])

            youtube = ""
            media = p.get("media", {})
            yt_url = media.get("video_youtube", "")
            if yt_url:
                youtube = f"[▶️]({yt_url})"

            lines.append(f"| {pid} | {nombre} | {version} | {desc} | {tags} | {youtube} |")

        lines.append("")

    # Categorías
    lines.append("## 📂 Categorías")
    lines.append("")
    lines.append("| Rango | Categoría | Descripción |")
    lines.append("|-------|-----------|-------------|")
    lines.append("| 🔒 1–999 | Personalizadas | Plantillas privadas por cliente |")
    lines.append(
        "| 📋 1000–1999 | Informes y Listados | Listados de clientes, proveedores, artículos... |"
    )
    lines.append(
        "| 🧾 2000–2999 | Facturas y Documentos | Modelos de facturas, albaranes, pedidos... |"
    )
    lines.append(
        "| 📊 3000–3999 | Balances y Contabilidad | Balances, cuentas de resultados, sumas y saldos... |"
    )
    lines.append(
        "| 📈 4000–4999 | Dashboard y Gráficos | Cuadros de mando Streamlit, gráficos... |"
    )
    lines.append("| 🔮 5000–5999 | Reservado futuro | — |")
    lines.append("")

    # Cómo usar
    lines.append("## 🚀 ¿Cómo usarlas?")
    lines.append("")
    lines.append("1. Instala **Sage50BI** de [ALCA TIC](https://pedironline.com)")
    lines.append("2. Las plantillas se **actualizan automáticamente** al iniciar la aplicación")
    lines.append("3. Explora el catálogo desde Sage50BI con búsqueda y recomendaciones")
    lines.append("4. ¡Listo!")
    lines.append("")
    lines.append("### También puedes:")
    lines.append(
        "- 📖 Ver el [catálogo web completo](https://wertymsd.github.io/repositorio_Sage50bi/)"
    )
    lines.append(
        "- 📡 Suscribirte al [RSS de novedades](https://wertymsd.github.io/repositorio_Sage50bi/feed.xml)"
    )
    lines.append("- 🎥 Ver los [vídeos en YouTube](https://youtube.com/)")
    lines.append("")

    # Enlaces
    lines.append("## 🔗 Enlaces")
    lines.append("")
    lines.append("- 🏢 [ALCA TIC — pedironline.com](https://pedironline.com)")
    lines.append("- 📖 [Catálogo web](https://wertymsd.github.io/repositorio_Sage50bi/)")
    lines.append("- 📡 [RSS Novedades](https://wertymsd.github.io/repositorio_Sage50bi/feed.xml)")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("© 2026 ALCA TIC, S.L. — Plantillas gratuitas para usuarios de Sage50BI.")
    lines.append("")
    lines.append(f"*Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


def generar_y_guardar_readme(
    repo_root: Path, plantillas: list[dict], packs: list[dict], stats: dict
) -> Path:
    """
    Genera y guarda el README.md.

    Returns:
        Ruta al archivo guardado
    """
    contenido = generar_readme(plantillas, packs, stats)

    readme_path = repo_root / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    return readme_path
