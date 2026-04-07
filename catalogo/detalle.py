"""
Vista detalle de plantilla del catálogo Sage50BI.

Componente Streamlit que muestra los detalles completos
de una plantilla con recomendaciones y opciones de instalación.
"""

try:
    import streamlit as st
except ImportError:
    st = None

import logging

try:
    from PIL import Image
except ImportError:
    Image = None

from .manifest_reader import ManifestReader
from .recomendaciones import recomendar_por_manifest
from .catalogo import _placeholder_image, _icono_estado
from .instalador import Instalador

logger = logging.getLogger(__name__)


def mostrar_detalle(
    reader: ManifestReader,
    template_id: int,
    destino_base: str = None,
) -> None:
    """
    Renderiza la vista detalle de una plantilla.

    Args:
        reader: Instancia de ManifestReader
        template_id: ID de la plantilla a mostrar
        destino_base: Directorio base para instalación
    """
    if st is None:
        return

    # Botón volver
    if st.button("← Volver al catálogo"):
        st.session_state.pagina = "catalogo"
        if "plantilla_detalle" in st.session_state:
            del st.session_state.plantilla_detalle
        st.rerun()

    # Obtener plantilla
    plantilla = reader.obtener_plantilla(template_id)
    if not plantilla:
        st.error(f"Plantilla {template_id} no encontrada")
        return

    nombre = plantilla.get("nombre", "Sin nombre")
    version = plantilla.get("version", "0.0.0")
    categoria = plantilla.get("categoria", "")
    descripcion = plantilla.get("descripcion", "")
    tags = plantilla.get("tags", [])
    preview_url = plantilla.get("preview_url", "")
    youtube_url = plantilla.get("youtube_url", "")

    # --- Preview grande ---
    st.markdown("---")
    col_img, col_meta = st.columns([1, 1])

    with col_img:
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

    with col_meta:
        # Metadata
        st.markdown(f"## {nombre}")
        st.markdown(f"**ID:** {template_id}")
        st.markdown(f"**Versión:** `{version}`")
        st.markdown(f"**Categoría:** {categoria}")

        # Descripción completa
        if descripcion:
            st.markdown("### Descripción")
            st.write(descripcion)

        # Tags
        if tags:
            chips = " ".join(f"`{tag}`" for tag in tags)
            st.markdown(f"**Tags:** {chips}")

    st.markdown("---")

    # --- YouTube ---
    if youtube_url:
        st.markdown(f"[▶️ Ver en YouTube]({youtube_url})")

    # --- Botón de instalación ---
    _mostrar_boton_instalacion(plantilla, destino_base)

    # --- Recomendaciones ---
    _mostrar_recomendaciones(reader, template_id)


def _mostrar_boton_instalacion(plantilla: dict, destino_base: str = None) -> None:
    """Muestra el botón de instalación/actualización."""
    if st is None:
        return

    pid = plantilla.get("id", 0)
    version = plantilla.get("version", "0.0.0")

    estado = "no_instalada"
    instalador = None
    if destino_base and "catalogo_instalador" in st.session_state:
        instalador: Instalador = st.session_state.catalogo_instalador
        estado = instalador.estado_instalacion(pid)

    if estado == "instalada":
        st.success(f"✅ Instalada v{version}")
        if instalador:
            if st.button(f"🔄 Actualizar a v{version}", key=f"actualizar_{pid}"):
                with st.spinner("Actualizando..."):
                    if instalador.actualizar(pid):
                        st.success("¡Plantilla actualizada!")
                        st.rerun()
                    else:
                        st.error("Error al actualizar la plantilla")

    elif estado == "actualizable":
        st.warning(f"🔄 Versión instalada desactualizada")
        if instalador:
            if st.button(f"⬆️ Actualizar a v{version}", key=f"actualizar_{pid}"):
                with st.spinner("Actualizando..."):
                    if instalador.actualizar(pid):
                        st.success("¡Plantilla actualizada!")
                        st.rerun()
                    else:
                        st.error("Error al actualizar la plantilla")

    else:
        if instalador and destino_base:
            if st.button(f"📥 Instalar", key=f"instalar_{pid}"):
                with st.spinner("Instalando..."):
                    if instalador.instalar(pid):
                        st.success("¡Plantilla instalada!")
                        st.rerun()
                    else:
                        st.error("Error al instalar la plantilla")
        else:
            st.info("📥 Disponible para instalar")


def _mostrar_recomendaciones(reader: ManifestReader, template_id: int) -> None:
    """Muestra la sección 'Quien vio esto también vio...'."""
    if st is None:
        return

    try:
        manifest = reader.cargar_manifest()
    except Exception:
        return

    recomendadas = recomendar_por_manifest(manifest, template_id, max_resultados=3)
    if not recomendadas:
        return

    st.markdown("---")
    st.markdown("### 👀 Quien vio esto también vio...")

    cols = st.columns(min(len(recomendadas), 3))
    for i, rec in enumerate(recomendadas):
        with cols[i]:
            rec_id = rec.get("id", 0)
            rec_nombre = rec.get("nombre", "Sin nombre")
            rec_cat = rec.get("categoria", "")
            rec_version = rec.get("version", "0.0.0")
            rec_tags = rec.get("tags", [])

            st.markdown(f"**{rec_nombre}**")
            st.caption(f"ID: {rec_id} | v{rec_version}")
            st.markdown(f":blue-badge[{rec_cat}]")

            if rec_tags:
                chips = " ".join(f"`{tag}`" for tag in rec_tags[:4])
                st.markdown(chips, unsafe_allow_html=True)

            if st.button("Ver detalle", key=f"rec_detalle_{rec_id}"):
                st.session_state.plantilla_detalle = rec_id
                st.session_state.pagina = "detalle"
                st.rerun()
