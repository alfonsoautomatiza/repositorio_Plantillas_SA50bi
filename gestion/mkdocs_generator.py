"""
Generador de documentación MkDocs para Sage50BI.
Genera: paginas de plantillas, categorias, packs, privadas, RSS, Open Graph.
"""

import re
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape


def generar_slug(nombre: str, template_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")
    return f"{template_id:04d}-{slug}"


def generar_pagina_plantilla(template_data: dict) -> str:
    tid = template_data["id"]
    nombre = template_data["nombre"]
    version = template_data.get("version", "1.0.0")
    categoria = template_data.get("categoria", {})
    cat_nombre = categoria.get("nombre", "")
    cat_icono = categoria.get("icono", "📋")
    descripcion = template_data.get("descripcion", "")
    desc_larga = template_data.get("descripcion_larga", descripcion)
    tags = template_data.get("tags", [])
    media = template_data.get("media", {})
    changelog = template_data.get("changelog", [])
    archivos = template_data.get("archivos", {})
    recomendaciones_ids = template_data.get("recomendaciones", [])
    og = template_data.get("open_graph", {})
    yt_url = media.get("video_youtube", "")
    yt_thumb = media.get("video_miniatura", "")
    og_title = og.get("title", f"{nombre} — Plantilla Sage50BI")
    og_desc = og.get("description", descripcion[:160])

    lines = []
    lines.append("---")
    lines.append(f'title: "{og_title}"')
    lines.append(f'description: "{og_desc}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {cat_icono} {tid:04d} - {nombre}")
    lines.append("")
    if media.get("preview"):
        lines.append(f"![Preview]({media['preview']})")
        lines.append("")
    lines.append("## Descripción")
    lines.append("")
    lines.append(desc_larga if desc_larga else descripcion)
    lines.append("")
    if yt_url:
        lines.append("## Vídeo explicativo")
        lines.append("")
        if yt_thumb:
            lines.append(f"[![Vídeo]({yt_thumb})]({yt_url})")
        else:
            lines.append(f"[▶️ Ver en YouTube]({yt_url})")
        lines.append("")
    lines.append("## Detalles")
    lines.append("")
    lines.append("| Campo | Valor |")
    lines.append("|-------|-------|")
    lines.append(f"| Versión | {version} |")
    lines.append(f"| Categoría | {cat_icono} {cat_nombre} |")
    tipos = []
    if "sql" in archivos:
        tipos.append("SQL")
    if "dashboard" in archivos:
        tipos.append("Dashboard Streamlit")
    lines.append(f"| Incluye | {' + '.join(tipos)} |")
    lines.append(
        f"| Gratuito | {'✅ Sí' if template_data.get('gratuita') else '🔒 Personalizada'} |"
    )
    lines.append(f"| Actualizado | {template_data.get('fecha_actualizacion', '')} |")
    lines.append("")
    if tags:
        lines.append("## Tags")
        lines.append("")
        lines.append(" ".join(f"`{t}`" for t in tags))
        lines.append("")
    if recomendaciones_ids:
        lines.append("## Plantillas relacionadas")
        lines.append("")
        lines.append("| # | Nombre |")
        lines.append("|---|--------|")
        for rid in recomendaciones_ids:
            lines.append(f"| {rid:04d} | *Ver catálogo* |")
        lines.append("")
    if changelog:
        lines.append("## Historial de cambios")
        lines.append("")
        for entry in changelog[:5]:
            lines.append(f"### v{entry['version']} ({entry['fecha']})")
            lines.append(f"- {entry['cambios']}")
            lines.append("")
    return "\n".join(lines)


def generar_rss_feed(
    plantillas: list[dict], site_url: str = "https://wertymsd.github.io/repositorio_Sage50bi"
) -> str:
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss version="2.0">')
    lines.append("  <channel>")
    lines.append("    <title>Plantillas Sage50BI — Novedades</title>")
    lines.append(f"    <link>{site_url}/</link>")
    lines.append("    <description>Ultimas plantillas gratuitas para Sage50BI</description>")
    lines.append("    <language>es</language>")
    lines.append(f"    <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y')}</lastBuildDate>")
    publicas = sorted(
        [p for p in plantillas if p.get("tipo") == "publica"],
        key=lambda p: p.get("fecha_actualizacion", "2020-01-01"),
        reverse=True,
    )
    for p in publicas[:20]:
        tid = p["id"]
        nombre = p["nombre"]
        slug = generar_slug(nombre, tid)
        desc = p.get("descripcion", "")
        fecha = p.get("fecha_actualizacion", "")
        cat = p.get("categoria", {}).get("nombre", "")
        lines.append("    <item>")
        lines.append(f"      <title>{xml_escape(nombre)}</title>")
        lines.append(f"      <link>{site_url}/plantillas/{slug}/</link>")
        lines.append(f"      <description>{xml_escape(desc)}</description>")
        lines.append(f"      <pubDate>{fecha}</pubDate>")
        lines.append(f"      <category>{xml_escape(cat)}</category>")
        lines.append("    </item>")
    lines.append("  </channel>")
    lines.append("</rss>")
    return "\n".join(lines)


# === PÁGINA DE CATEGORÍA ===

# Mapa de slugs de categoría
CATEGORIAS_SLUGS = {
    "Informes y Listados": "informes-listados",
    "Facturas y Documentos": "facturas-documentos",
    "Balances y Contabilidad": "balances-contabilidad",
    "Dashboard y Gráficos": "dashboards-graficos",
    "Reservado futuro": "reservado-futuro",
    "Personalizadas": "personalizadas",
}


def generar_pagina_categoria(
    categoria_nombre: str, categoria_icono: str, plantillas: list[dict]
) -> str:
    """
    Genera la página de una categoría listando todas sus plantillas.

    Args:
        categoria_nombre: Nombre de la categoría
        categoria_icono: Emoji de la categoría
        plantillas: Lista de plantillas de esta categoría

    Returns:
        Markdown de la página de categoría
    """
    lines = []
    lines.append("---")
    lines.append(f'title: "{categoria_nombre} — Plantillas Sage50BI"')
    lines.append(f'description: "Catálogo de {categoria_nombre.lower()} para Sage50BI"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {categoria_icono} {categoria_nombre}")
    lines.append("")
    lines.append(f"Colección de plantillas de **{categoria_nombre}** para Sage50BI.")
    lines.append("")
    lines.append(f"**{len(plantillas)} plantillas disponibles**")
    lines.append("")

    if not plantillas:
        lines.append("*Aún no hay plantillas en esta categoría.*")
        lines.append("")
    else:
        # Cards de cada plantilla
        for p in sorted(plantillas, key=lambda x: x["id"]):
            tid = p["id"]
            nombre = p["nombre"]
            version = p.get("version", "1.0.0")
            desc = p.get("descripcion", "")
            tags = p.get("tags", [])
            media = p.get("media", {})
            slug = generar_slug(nombre, tid)

            lines.append(f"## {tid:04d} — {nombre}")
            lines.append("")
            if media.get("preview"):
                lines.append(
                    f"![Preview](../../publicas/{tid:04d}%20-%20{nombre}/{media['preview']})"
                )
                lines.append("")
            lines.append(desc)
            lines.append("")
            lines.append(
                f"**Versión:** {version} | **Tags:** {' '.join(f'`{t}`' for t in tags[:4])}"
            )
            lines.append("")
            lines.append(f"[📄 Ver detalle](../plantillas/{slug}.md)")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# === PÁGINA DE PACK ===


def generar_pagina_pack(pack_data: dict, plantillas_datos: list[dict]) -> str:
    """
    Genera la página de un pack con todas sus plantillas.

    Args:
        pack_data: Datos del pack (dict)
        plantillas_datos: Lista de dicts con datos de las plantillas del pack

    Returns:
        Markdown de la página del pack
    """
    pack_id = pack_data.get("id", "")
    nombre = pack_data.get("nombre", pack_id)
    descripcion = pack_data.get("descripcion", "")
    icono = pack_data.get("icono", "📦")
    plantillas_ids = pack_data.get("plantillas", [])

    lines = []
    lines.append("---")
    lines.append(f'title: "{nombre} — Pack Sage50BI"')
    lines.append(f'description: "{descripcion[:160]}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {icono} {nombre}")
    lines.append("")
    lines.append(descripcion)
    lines.append("")
    lines.append(f"**{len(plantillas_ids)} plantillas incluidas**")
    lines.append("")

    if plantillas_datos:
        lines.append("## Plantillas del pack")
        lines.append("")
        lines.append("| # | Nombre | Categoría | Versión | Descripción |")
        lines.append("|---|--------|-----------|---------|-------------|")
        for p in sorted(plantillas_datos, key=lambda x: x["id"]):
            tid = p["id"]
            pnombre = p["nombre"]
            cat = p.get("categoria", {}).get("icono", "📋")
            version = p.get("version", "1.0.0")
            desc = p.get("descripcion", "")[:60]
            if len(p.get("descripcion", "")) > 60:
                desc += "..."
            lines.append(f"| {tid:04d} | {pnombre} | {cat} | {version} | {desc} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Pack instalable directamente desde Sage50BI con un solo click.*")
    lines.append("")

    return "\n".join(lines)


# === PÁGINA PRIVADA (oculta de nav) ===


def generar_pagina_privada(template_data: dict) -> str:
    """
    Genera la página de una plantilla privada (NO aparece en navegación).
    Solo accesible conociendo la URL exacta.
    """
    tid = template_data["id"]
    nombre = template_data["nombre"]
    descripcion = template_data.get("descripcion", "")
    cliente = template_data.get("cliente", {})
    cliente_codigo = cliente.get("codigo", "")

    lines = []
    lines.append("---")
    lines.append(f'title: "Plantilla personalizada — Sage50BI"')
    lines.append(f'description: "Plantilla personalizada para cliente"')
    lines.append("hide:")
    lines.append("  - navigation")
    lines.append("  - toc")
    lines.append("---")
    lines.append("")
    lines.append(f"# 🔒 Plantilla Personalizada")
    lines.append("")
    lines.append(f"**{nombre}**")
    lines.append("")
    lines.append(descripcion)
    lines.append("")
    lines.append(f"Código de cliente: `{cliente_codigo}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Esta plantilla es privada y solo está disponible para el cliente asociado.*")
    lines.append("Instálala desde Sage50BI con tu código de licencia.")
    lines.append("")

    return "\n".join(lines)


# === PÁGINA INDEX (HOME) ===


def generar_pagina_index(plantillas: list[dict], packs: list[dict], stats: dict) -> str:
    """
    Genera la página principal (index.md) del site MkDocs.
    Catálogo visual con cards, packs destacados, y SEO fuerte.
    """
    total = stats.get("total_plantillas", 0)
    total_packs = stats.get("total_packs", 0)
    publicas = [p for p in plantillas if p.get("tipo") == "publica"]
    publicas_sorted = sorted(publicas, key=lambda p: p.get("fecha_actualizacion", ""), reverse=True)

    lines = []
    lines.append("---")
    lines.append('title: "Plantillas Gratuitas Sage50BI — ALCA TIC"')
    lines.append(
        'description: "Catálogo de plantillas SQL gratuitas para Sage50BI. Informes, balances, facturas y dashboards Streamlit."'
    )
    lines.append("---")
    lines.append("")
    lines.append("# 🏢 Plantillas Gratuitas para Sage50BI")
    lines.append("")
    lines.append(
        "Colección de **{total} plantillas SQL y dashboards Streamlit** gratuitas "
        "para [Sage50BI](https://pedironline.com) de ALCA TIC."
    )
    lines[-1] = lines[-1].format(total=total)
    lines.append("")
    lines.append("Cada plantilla incluye consultas SQL optimizadas, dashboards interactivos,")
    lines.append("actualización automática desde la aplicación y vídeos explicativos.")
    lines.append("")

    # Packs destacados
    if packs:
        lines.append("## 📦 Packs Destacados")
        lines.append("")
        for pack in packs:
            icono = pack.get("icono", "📦")
            nombre = pack.get("nombre", pack.get("id", ""))
            desc = pack.get("descripcion", "")
            total_p = pack.get("total_plantillas", len(pack.get("plantillas", [])))
            pack_slug = pack.get("slug", pack.get("id", ""))
            lines.append(f"### {icono} [{nombre}](packs/{pack_slug}.md)")
            lines.append("")
            lines.append(f"{desc} — **{total_p} plantillas**")
            lines.append("")
        lines.append("")

    # Novedades (últimas 6)
    if publicas_sorted:
        lines.append("## 🆕 Últimas Plantillas")
        lines.append("")
        lines.append("| # | Plantilla | Categoría | Versión | Descripción |")
        lines.append("|---|-----------|-----------|---------|-------------|")
        for p in publicas_sorted[:6]:
            tid = p["id"]
            nombre = p["nombre"]
            cat_icono = p.get("categoria", {}).get("icono", "📋")
            version = p.get("version", "1.0.0")
            desc = p.get("descripcion", "")[:60]
            if len(p.get("descripcion", "")) > 60:
                desc += "..."
            slug = generar_slug(nombre, tid)
            lines.append(
                f"| {tid:04d} | [{nombre}](plantillas/{slug}.md) | {cat_icono} | {version} | {desc} |"
            )
        lines.append("")

    # Categorías
    lines.append("## 📂 Categorías")
    lines.append("")
    lines.append("| Icono | Categoría | Rango |")
    lines.append("|-------|-----------|-------|")
    lines.append("| 📋 | [Informes y Listados](categorias/informes-listados.md) | 1000–1999 |")
    lines.append("| 🧾 | [Facturas y Documentos](categorias/facturas-documentos.md) | 2000–2999 |")
    lines.append(
        "| 📊 | [Balances y Contabilidad](categorias/balances-contabilidad.md) | 3000–3999 |"
    )
    lines.append("| 📈 | [Dashboard y Gráficos](categorias/dashboards-graficos.md) | 4000–4999 |")
    lines.append("")

    # Cómo usar
    lines.append("## 🚀 ¿Cómo usarlas?")
    lines.append("")
    lines.append("1. Instala **Sage50BI** de [ALCA TIC](https://pedironline.com)")
    lines.append("2. Las plantillas se **actualizan automáticamente** al iniciar la aplicación")
    lines.append("3. Explora el catálogo desde Sage50BI con búsqueda y recomendaciones")
    lines.append("4. ¡Listo!")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("🏫 Desarrollado por [ALCA TIC, S.L.](https://pedironline.com)")
    lines.append("")
    lines.append(f"*Última actualización: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")

    return "\n".join(lines)


# === CSS EXTRA ===


def generar_css_extra() -> str:
    """
    Genera el CSS extra para el site MkDocs Material.
    Incluye estilos para cards, badges, y diseño responsive.
    """
    return """/* === Sage50BI Template Catalog === */

/* Cards grid para catálogo */
.grid-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}

.grid-cards .card {
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 8px;
    padding: 1rem;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.grid-cards .card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

.grid-cards .card img {
    width: 100%;
    border-radius: 4px;
    margin-bottom: 0.5rem;
}

/* Badge tags */
.md-typeset .badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.25rem;
    margin-bottom: 0.25rem;
}

.badge-blue { background: #2196f3; color: white; }
.badge-green { background: #4caf50; color: white; }
.badge-purple { background: #9c27b0; color: white; }
.badge-orange { background: #ff9800; color: white; }

/* Preview images */
.template-preview {
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 8px;
    max-width: 100%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Pack card */
.pack-card {
    border: 2px solid var(--md-primary-fg-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    background: var(--md-primary-fg-color--lightest);
}

.pack-card h3 {
    margin-top: 0;
}

/* Hide private pages from search */
.md-nav__link[data-md-component="toc"][href*="privadas/"] {
    display: none;
}

/* Responsive */
@media (max-width: 768px) {
    .grid-cards {
        grid-template-columns: 1fr;
    }
}
"""


# === GENERACIÓN COMPLETA ===


def _agrupar_por_categoria(plantillas: list[dict]) -> dict[str, list[dict]]:
    """Agrupa las plantillas públicas por categoría."""
    por_categoria: dict[str, list[dict]] = {}
    for p in plantillas:
        if p.get("tipo") != "publica":
            continue
        cat = p.get("categoria", {}).get("nombre", "Sin categoría")
        if cat not in por_categoria:
            por_categoria[cat] = []
        por_categoria[cat].append(p)
    return por_categoria


def generar_todo(
    plantillas: list[dict],
    packs: list[dict],
    stats: dict,
    docs_dir: Path,
    packs_datos: list[dict] = None,
) -> dict[str, Path]:
    """
    Genera TODA la documentación MkDocs: index, categorías, packs, plantillas, privadas, RSS, CSS.

    Args:
        plantillas: Lista de dicts con datos de todas las plantillas
        packs: Lista de dicts resumen de packs (para index)
        stats: Estadísticas del repositorio
        docs_dir: Ruta al directorio docs/
        packs_datos: Lista de dicts completos de packs (opcional, para páginas detalladas)

    Returns:
        Dict {descripcion: Path} de archivos generados
    """
    generados = {}

    # Asegurar subdirectorios
    for subdir in ["plantillas", "categorias", "packs", "privadas", "css", "img"]:
        (docs_dir / subdir).mkdir(parents=True, exist_ok=True)

    # --- CSS ---
    css_path = docs_dir / "css" / "extra.css"
    css_path.write_text(generar_css_extra(), encoding="utf-8")
    generados["css"] = css_path

    # --- Index ---
    index_path = docs_dir / "index.md"
    index_path.write_text(generar_pagina_index(plantillas, packs, stats), encoding="utf-8")
    generados["index"] = index_path

    # --- Páginas de plantillas ---
    for p in plantillas:
        if p.get("tipo") == "publica":
            slug = generar_slug(p["nombre"], p["id"])
            page_path = docs_dir / "plantillas" / f"{slug}.md"
            page_path.write_text(generar_pagina_plantilla(p), encoding="utf-8")
            generados[f"plantilla-{p['id']}"] = page_path
        elif p.get("tipo") == "privada":
            cliente_codigo = p.get("cliente", {}).get("codigo", "").lower()
            if cliente_codigo:
                page_path = docs_dir / "privadas" / f"{cliente_codigo}.md"
                page_path.write_text(generar_pagina_privada(p), encoding="utf-8")
                generados[f"privada-{p['id']}"] = page_path

    # --- Páginas de categorías ---
    por_categoria = _agrupar_por_categoria(plantillas)
    cat_iconos = {
        "Informes y Listados": "📋",
        "Facturas y Documentos": "🧾",
        "Balances y Contabilidad": "📊",
        "Dashboard y Gráficos": "📈",
        "Reservado futuro": "🔮",
        "Personalizadas": "🔒",
    }
    for cat_nombre, cat_plantillas in por_categoria.items():
        cat_slug = CATEGORIAS_SLUGS.get(
            cat_nombre, re.sub(r"[^a-z0-9]+", "-", cat_nombre.lower()).strip("-")
        )
        icono = cat_iconos.get(cat_nombre, "📋")
        page_path = docs_dir / "categorias" / f"{cat_slug}.md"
        page_path.write_text(
            generar_pagina_categoria(cat_nombre, icono, cat_plantillas), encoding="utf-8"
        )
        generados[f"categoria-{cat_slug}"] = page_path

    # --- Páginas de packs ---
    packs_completos = packs_datos or packs
    for pack in packs_completos:
        pack_slug = pack.get("slug", pack.get("id", ""))
        plantillas_del_pack = [p for p in plantillas if p["id"] in pack.get("plantillas", [])]
        page_path = docs_dir / "packs" / f"{pack_slug}.md"
        page_path.write_text(generar_pagina_pack(pack, plantillas_del_pack), encoding="utf-8")
        generados[f"pack-{pack_slug}"] = page_path

    # --- RSS Feed ---
    rss_path = docs_dir / "feed.xml"
    rss_path.write_text(generar_rss_feed(plantillas), encoding="utf-8")
    generados["rss"] = rss_path

    return generados
