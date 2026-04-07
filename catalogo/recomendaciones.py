"""
Motor de recomendaciones para el catálogo Sage50BI.

Genera recomendaciones basadas en tags compartidos, categoría
y recomendaciones manuales definidas en template.json.
"""

from typing import Optional


def recomendar_por_tags(
    plantilla_actual: dict,
    todas_plantillas: list[dict],
    max_resultados: int = 3,
) -> list[dict]:
    """
    Recomienda plantillas por solapamiento de tags.

    Calcula cuántos tags tiene en común cada plantilla con la actual
    y devuelve las que más coinciden.

    Args:
        plantilla_actual: Plantilla de referencia
        todas_plantillas: Lista completa de plantillas
        max_resultados: Máximo de resultados a devolver

    Returns:
        Lista de plantillas recomendadas, ordenadas por coincidencias
    """
    tags_actual = set(plantilla_actual.get("tags", []))
    if not tags_actual:
        return []

    puntuaciones = []
    for p in todas_plantillas:
        if p.get("id") == plantilla_actual.get("id"):
            continue
        tags_p = set(p.get("tags", []))
        coincidencias = len(tags_actual & tags_p)
        if coincidencias > 0:
            puntuaciones.append((coincidencias, p))

    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in puntuaciones[:max_resultados]]


def recomendar_por_manifest(
    manifest: dict,
    plantilla_id: int,
    max_resultados: int = 3,
) -> list[dict]:
    """
    Obtiene recomendaciones manuales + automáticas combinadas.

    Las recomendaciones manuales del campo 'recomendaciones' de la plantilla
    tienen prioridad. Las automáticas por tags rellenan los huecos restantes.

    Args:
        manifest: Manifest completo con plantillas y packs
        plantilla_id: ID de la plantilla de referencia
        max_resultados: Máximo de resultados a devolver

    Returns:
        Lista de plantillas recomendadas (manuales primero, luego automáticas)
    """
    plantillas = manifest.get("plantillas", [])

    # Buscar plantilla actual
    plantilla_actual: Optional[dict] = None
    for p in plantillas:
        if p.get("id") == plantilla_id:
            plantilla_actual = p
            break

    if not plantilla_actual:
        return []

    # Recomendaciones manuales (IDs referenciados en el campo 'recomendaciones')
    ids_manual = plantilla_actual.get("recomendaciones", [])
    recomendaciones_manuales = []
    ids_manual_set = set()
    for p in plantillas:
        if p.get("id") in ids_manual and p.get("id") != plantilla_id:
            recomendaciones_manuales.append(p)
            ids_manual_set.add(p.get("id"))

    # Si ya tenemos suficientes manuales, devolver
    if len(recomendaciones_manuales) >= max_resultados:
        return recomendaciones_manuales[:max_resultados]

    # Rellenar con recomendaciones automáticas por tags
    restantes = max_resultados - len(recomendaciones_manuales)
    auto = recomendar_por_tags(plantilla_actual, plantillas, restantes + len(ids_manual_set))

    # Filtrar las que ya están en manuales
    auto_filtradas = [p for p in auto if p.get("id") not in ids_manual_set]

    return recomendaciones_manuales + auto_filtradas[:restantes]


def recomendar_por_categoria(
    plantilla_actual: dict,
    todas_plantillas: list[dict],
    max_resultados: int = 3,
) -> list[dict]:
    """
    Recomienda plantillas de la misma categoría.

    Excluye la plantilla actual de los resultados.

    Args:
        plantilla_actual: Plantilla de referencia
        todas_plantillas: Lista completa de plantillas
        max_resultados: Máximo de resultados a devolver

    Returns:
        Lista de plantillas de la misma categoría
    """
    categoria = plantilla_actual.get("categoria", "")
    if not categoria:
        return []

    resultados = [
        p
        for p in todas_plantillas
        if p.get("categoria") == categoria and p.get("id") != plantilla_actual.get("id")
    ]
    return resultados[:max_resultados]
