"""
Generador de texto SEO para YouTube.
Auto-genera título, descripción y tags optimizados para cada plantilla.
"""

from typing import Optional
import pyperclip


def generar_youtube_seo(
    nombre: str,
    descripcion: str,
    tags: list[str],
    video_youtube: str = "",
    categoria: str = "",
) -> dict:
    """
    Genera el bloque youtube_seo para template.json.

    Args:
        nombre: Nombre de la plantilla
        descripcion: Descripción corta
        tags: Lista de tags
        video_youtube: URL del video (opcional)
        categoria: Nombre de la categoría

    Returns:
        Diccionario con titulo, descripcion y tags_youtube
    """
    # Título optimizado
    titulo = f"{nombre} — Plantilla gratuita para Sage50BI"

    # Descripción expandida
    descripcion_youtube = f"""📊 Plantilla gratuita para Sage50BI de ALCA TIC.

{descripcion}

✅ Gratuita ✅ Actualización automática ✅ Sin registro

🔗 Más plantillas: https://wertymsd.github.io/repositorio_Sage50bi/
🔗 RSS Novedades: https://wertymsd.github.io/repositorio_Sage50bi/feed.xml
🏢 ALCA TIC: https://pedironline.com"""

    # Tags base + específicos
    tags_base = ["sage50", "sage50bi", "plantillas sql", "informes contables", "erp"]
    tags_youtube = tags_base + [t.lower() for t in tags[:5]]

    # Añadir categoría como tag si existe
    if categoria:
        tags_youtube.append(categoria.lower())

    # Deduplicar
    tags_youtube = list(dict.fromkeys(tags_youtube))

    return {"titulo": titulo, "descripcion": descripcion_youtube, "tags_youtube": tags_youtube}


def generar_texto_copiable(
    nombre: str, descripcion: str, tags: list[str], categoria: str = "", url_plantilla: str = ""
) -> str:
    """
    Genera el texto formateado listo para copiar-pegar en YouTube.

    Returns:
        String con título, descripción y tags formateados
    """
    youtube_seo = generar_youtube_seo(nombre, descripcion, tags, categoria=categoria)

    # Formatear tags para YouTube (separados por coma)
    tags_str = ", ".join(youtube_seo["tags_youtube"])

    # Hashtags para descripción
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in youtube_seo["tags_youtube"][:8])

    texto = f"""━━━ COPIAR EN YOUTUBE ━━━

TÍTULO:
{youtube_seo["titulo"]}

DESCRIPCIÓN:
{youtube_seo["descripcion"]}

{hashtags}

TAGS (copiar todo):
{tags_str}

━━━━━━━━━━━━━━━━━━━━━━━━"""

    return texto


def copiar_al_portapapeles(texto: str) -> bool:
    """
    Copia el texto al portapapeles.

    Returns:
        True si se copió exitosamente, False si falló
    """
    try:
        pyperclip.copy(texto)
        return True
    except Exception:
        return False


def generar_y_copiar(
    nombre: str, descripcion: str, tags: list[str], categoria: str = ""
) -> tuple[str, bool]:
    """
    Genera el texto YouTube y lo copia al portapapeles.

    Returns:
        Tupla (texto_generado, copiado_exitosamente)
    """
    texto = generar_texto_copiable(nombre, descripcion, tags, categoria)
    copiado = copiar_al_portapapeles(texto)
    return texto, copiado


# === TEMPLATES DE DESCRIPCIÓN POR CATEGORÍA ===

TEMPLATES_DESCRIPCION = {
    "Informes y Listados": """📋 {nombre}

{descripcion}

Este informe de Sage50BI te permite obtener un listado completo con filtros 
personalizables y exportación a Excel.

✅ Gratuita ✅ Actualización automática ✅ Sin registro""",
    "Facturas y Documentos": """🧾 {nombre}

{descripcion}

Modelo de documento optimizado para Sage50BI con formato profesional 
y totales automáticos.

✅ Gratuita ✅ Actualización automática ✅ Sin registro""",
    "Balances y Contabilidad": """📊 {nombre}

{descripcion}

Informe contable para Sage50BI con desglose por cuentas, períodos 
y comparativas.

✅ Gratuita ✅ Actualización automática ✅ Sin registro""",
    "Dashboard y Gráficos": """📈 {nombre}

{descripcion}

Cuadro de mando interactivo con Streamlit para Sage50BI. Visualiza 
tus datos en tiempo real con gráficos dinámicos.

✅ Gratuita ✅ Actualización automática ✅ Sin registro""",
}


def generar_descripcion_por_categoria(nombre: str, descripcion: str, categoria: str) -> str:
    """
    Genera una descripción expandida basada en la categoría.
    """
    template = TEMPLATES_DESCRIPCION.get(categoria)
    if template:
        return template.format(nombre=nombre, descripcion=descripcion)

    # Fallback genérico
    return f"""📊 {nombre}

{descripcion}

Plantilla gratuita para Sage50BI de ALCA TIC.

✅ Gratuita ✅ Actualización automática ✅ Sin registro"""


if __name__ == "__main__":
    # Test
    texto = generar_texto_copiable(
        nombre="Listado de clientes ESPAÑA",
        descripcion="Listado completo de clientes con filtros por provincia, forma de pago y fecha de alta.",
        tags=["clientes", "listado", "españa", "informes"],
        categoria="Informes y Listados",
    )
    print(texto)
