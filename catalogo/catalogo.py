"""
Página principal del catálogo de plantillas Sage50BI.

Componente Streamlit que muestra el catálogo con búsqueda,
filtros por categoría, packs y tarjetas de plantillas.
"""

try:
    import streamlit as st
except ImportError:
    st = None

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

from gestion.schemas import CATEGORIAS

from .manifest_reader import ManifestReader
from .instalador import Instalador
from . import DEFAULT_MANIFEST_URL

logger = logging.getLogger(__name__)

# Categorías para el filtro (excluir "Personalizadas" y "Reservado futuro" del selector)
CATEGORIAS_FILTRO = ["Todas"] + [
    cat["nombre"]
    for (min_id, max_id), cat in CATEGORIAS.items()
    if cat["nombre"] not in ("Personalizadas", "Reservado futuro")
]


def _placeholder_image(nombre: str, categoria: str) -> Image.Image:
    """Genera una imagen placeholder para plantillas sin preview."""
    if Image is None:
        return None
    img = Image.new("RGB", (400, 300), color=(30, 30, 50))
    draw = ImageDraw.Draw(img)

    # Rectángulo de categoría
    draw.rectangle([10, 10, 390, 60], fill=(60, 60, 90))
    texto_cat = categoria[:40] if categoria else "Sin categoría"
    draw.text((20, 25), texto_cat, fill=(200, 200, 220))

    # Nombre de la plantilla
    texto_nombre = nombre[:35] if nombre else "Sin nombre"
    draw.text((20, 130), texto_nombre, fill=(255, 255, 255))

    # Marca de agua
    draw.text((20, 260), "Sage50BI", fill=(100, 100, 140))
    return img


def _badge_color(estado: str) -> str:
    """Devuelve el color del badge según el estado de instalación."""
    colores = {
        "no_instalada": "gray",
        "actualizable": "orange",
        "instalada": "green",
    }
    return colores.get(estado, "gray")


def _icono_estado(estado: str) -> str:
    """Devuelve el icono del estado de instalación."""
    iconos = {
        "no_instalada": "⬇️",
        "actualizable": "🔄",
        "instalada": "✅",
    }
    return iconos.get(estado, "❓")


def mostrar_catalogo(
    manifest_url: str = DEFAULT_MANIFEST_URL,
    destino_base: str = None,
    cache_dir: str = None,
) -> None:
    """
    Renderiza la página completa del catálogo.

    Args:
        manifest_url: URL o ruta al manifest-templates.json
        destino_base: Directorio base para instalación de plantillas
        cache_dir: Directorio para caché del manifest
    """
    if st is None:
        return

    # Inicializar reader e instalador
    if "catalogo_reader" not in st.session_state:
        st.session_state.catalogo_reader = ManifestReader(manifest_url, cache_dir)
    if destino_base and "catalogo_instalador" not in st.session_state:
        st.session_state.catalogo_instalador = Instalador(
            st.session_state.catalogo_reader, destino_base
        )

    reader: ManifestReader = st.session_state.catalogo_reader

    # Header con botón de refresh
    col_header, col_refresh = st.columns([6, 1])
    with col_header:
        st.title("📋 Catálogo de Plantillas Sage50BI")
    with col_refresh:
        if st.button("🔄", help="Actualizar catálogo"):
            reader._manifest = None
            st.rerun()

    # Barra de búsqueda
    busqueda = st.text_input(
        "🔍 Buscar plantillas",
        placeholder="Buscar por nombre, tag o descripción...",
        key="catalogo_busqueda",
    )

    # Filtro de categoría
    col_filtro, col_nov = st.columns([3, 2])
    with col_filtro:
        categoria_sel = st.selectbox(
            "📁 Categoría",
            options=CATEGORIAS_FILTRO,
            key="catalogo_categoria",
        )
    with col_nov:
        mostrar_novedades = st.checkbox("🆕 Solo novedades (últimos 30 días)", value=False)

    # Obtener plantillas
    try:
        if busqueda:
            plantillas = reader.buscar(busqueda)
        else:
            plantillas = reader.obtener_plantillas()

        # Filtrar por categoría
        if categoria_sel != "Todas":
            plantillas = [p for p in plantillas if p.get("categoria") == categoria_sel]

        # Filtrar novedades
        if mostrar_novedades:
            novedades_ids = {p["id"] for p in reader.obtener_novedades(30)}
            plantillas = [p for p in plantillas if p.get("id") in novedades_ids]

    except Exception as e:
        st.error(f"Error cargando catálogo: {e}")
        return

    # --- Sección de Packs ---
    _mostrar_packs(reader)

    # --- Separar públicas y privadas ---
    publicas = [p for p in plantillas if not str(p.get("id", "")).startswith("CLI-")]
    privadas = [p for p in plantillas if str(p.get("id", "")).startswith("CLI-")]

    # --- Tarjetas de plantillas públicas ---
    st.subheader(f"📑 Plantillas ({len(publicas)})")
    _mostrar_tarjetas(publicas, reader)

    # --- Plantillas privadas ---
    if privadas:
        with st.expander(f"🔒 Plantillas Privadas ({len(privadas)})", expanded=False):
            _mostrar_tarjetas(privadas, reader)

    # --- Barra de estado ---
    try:
        manifest = reader.cargar_manifest()
        fecha = manifest.get("fecha_generacion", "Desconocida")
        total = manifest.get("total_plantillas", len(plantillas))
        st.caption(f"Última actualización: {fecha} | {total} plantillas")
    except Exception:
        st.caption(f"{len(plantillas)} plantillas mostradas")


def _mostrar_packs(reader: ManifestReader) -> None:
    """Muestra la sección de packs disponibles."""
    if st is None:
        return

    packs = reader.obtener_packs()
    if not packs:
        return

    with st.expander(f"📦 Packs Disponibles ({len(packs)})", expanded=False):
        cols = st.columns(min(len(packs), 3))
        for i, pack in enumerate(packs):
            with cols[i % len(cols)]:
                icono = pack.get("icono", "📦")
                st.markdown(f"### {icono} {pack.get('nombre', 'Pack')}")
                st.caption(pack.get("descripcion", ""))
                st.info(f"📝 {pack.get('total', len(pack.get('plantillas', [])))} plantillas")

                if "catalogo_instalador" in st.session_state:
                    if st.button(
                        f"📥 Instalar todo",
                        key=f"pack_{pack.get('id', i)}",
                    ):
                        instalador: Instalador = st.session_state.catalogo_instalador
                        resultados = instalador.instalar_pack(pack.get("id", ""))
                        exitosas = sum(resultados)
                        st.success(f"✅ {exitosas}/{len(resultados)} plantillas instaladas")


def _mostrar_tarjetas(plantillas: list, reader: ManifestReader) -> None:
    """Muestra la cuadrícula de tarjetas de plantillas."""
    if st is None:
        return

    if not plantillas:
        st.info("No se encontraron plantillas con los filtros actuales.")
        return

    # Grid de 3 columnas
    for fila in range(0, len(plantillas), 3):
        cols = st.columns(3)
        for col_idx in range(3):
            idx = fila + col_idx
            if idx >= len(plantillas):
                break
            with cols[col_idx]:
                _mostrar_tarjeta(plantillas[idx], reader)


def _mostrar_tarjeta(plantilla: dict, reader: ManifestReader) -> None:
    """Muestra una tarjeta individual de plantilla."""
    if st is None:
        return

    pid = plantilla.get("id", 0)
    nombre = plantilla.get("nombre", "Sin nombre")
    categoria = plantilla.get("categoria", "")
    version = plantilla.get("version", "0.0.0")
    tags = plantilla.get("tags", [])
    descripcion = plantilla.get("descripcion", "")
    preview_url = plantilla.get("preview_url", "")

    # Preview image
    if preview_url:
        try:
            st.image(preview_url, use_container_width=True)
        except Exception:
            img = _placeholder_image(nombre, categoria)
            if img:
                st.image(img, use_container_width=True)
    else:
        img = _placeholder_image(nombre, categoria)
        if img:
            st.image(img, use_container_width=True)

    # Nombre
    st.markdown(f"**{nombre}**")

    # ID y versión
    st.caption(f"ID: {pid} | v{version}")

    # Badge de categoría
    st.markdown(f":blue-badge[{categoria}]")

    # Tags como chips
    if tags:
        chips = " ".join(f"`{tag}`" for tag in tags[:5])
        st.markdown(chips, unsafe_allow_html=True)

    # Descripción truncada
    if descripcion:
        desc_corta = descripcion[:100] + "..." if len(descripcion) > 100 else descripcion
        st.caption(desc_corta)

    # Estado de instalación
    estado = "no_instalada"
    if "catalogo_instalador" in st.session_state:
        instalador: Instalador = st.session_state.catalogo_instalador
        estado = instalador.estado_instalacion(pid)

    icono = _icono_estado(estado)
    color = _badge_color(estado)
    etiquetas = {
        "no_instalada": "Nueva",
        "actualizable": "Actualizable",
        "instalada": f"Instalada v{version}",
    }
    st.markdown(f":{color}-badge[{icono} {etiquetas.get(estado, 'Desconocido')}]")

    # Botón ver detalle
    if st.button("👁 Ver detalle", key=f"detalle_{pid}"):
        st.session_state.plantilla_detalle = pid
        st.session_state.pagina = "detalle"
        st.rerun()
