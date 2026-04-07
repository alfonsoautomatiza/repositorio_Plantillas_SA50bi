"""
GUI de Gestión de Plantillas Sage50BI — PySimpleGUI.

Wizard paso a paso para crear, actualizar y publicar plantillas.
Sigue el diseño definido en PRD sección 12.
"""

import webbrowser
from pathlib import Path
from typing import Optional

try:
    import PySimpleGUI as sg
except ImportError:
    import FreeSimpleGUI as sg  # Fallback a fork libre (misma API)

from .gestor import Gestor, GestorError
from .schemas import CATEGORIAS, get_categoria_por_id, es_plantilla_privada
from .version_manager import BumpType, bump_version
from .mkdocs_generator import generar_todo
from .manifest_generator import generar_manifest, generar_y_guardar_manifest
from .readme_generator import generar_y_guardar_readme
from .youtube_generator import generar_texto_copiable, copiar_al_portapapeles
from .pack_generator import (
    crear_pack,
    validar_pack,
    guardar_pack,
    cargar_pack,
    listar_packs,
    actualizar_pack as pack_actualizar,
    obtener_packs_de_plantilla,
)

# === THEME ===
sg.theme("SystemDefaultForReal")

# === CONSTANTES ===
REPO_ROOT = Path(__file__).resolve().parent.parent
ICONO_APP = "🏢"
TITULO_APP = "Gestión de Plantillas Sage50BI"


# ============================================================
# HELPERS
# ============================================================


def _popup_error(mensaje: str):
    sg.popup_error(mensaje, title="Error", keep_on_top=True)


def _popup_ok(mensaje: str):
    sg.popup_ok(mensaje, title="OK", keep_on_top=True)


def _popup_progreso(titulo: str) -> sg.Window:
    """Abre una ventana de progreso y la devuelve para actualizarla."""
    layout = [
        [sg.Text(titulo, key="-MSG-")],
        [sg.ProgressBar(100, orientation="h", size=(40, 20), key="-BAR-")],
    ]
    win = sg.Window("Progreso", layout, keep_on_top=True, finalize=True, modal=True)
    return win


def _actualizar_progreso(win: sg.Window, msg: str, pct: int):
    win["-MSG-"].update(msg)
    win["-BAR-"].update_bar(pct)
    win.refresh()


def _cerrar_progreso(win: sg.Window):
    win.close()


def _get_gestor() -> Gestor:
    return Gestor(REPO_ROOT)


def _obtener_packs_nombres(gestor: Gestor) -> dict[str, str]:
    """Devuelve {pack_id: nombre} para combos."""
    packs = listar_packs(gestor.dir_packs)
    return {
        p["id"]: f"{p.get('icono', '')} {p['nombre']} ({p['total_plantillas']} plantillas)"
        for p in packs
    }


def _obtener_plantillas_nombres(gestor: Gestor, solo_publicas: bool = True) -> dict[int, str]:
    """Devuelve {id: 'NNNN - Nombre'} para combos."""
    plantillas = gestor.listar_plantillas(solo_publicas=solo_publicas)
    return {p["id"]: f"{p['id']:04d} - {p['nombre']}" for p in plantillas}


# ============================================================
# VENTANA PRINCIPAL
# ============================================================


def _ventana_principal(gestor: Gestor) -> str:
    """
    Pantalla principal con los 8 botones de acción.
    Returns: evento pulsado
    """
    stats = gestor.obtener_estadisticas()

    layout = [
        [sg.Text(f"{ICONO_APP} {TITULO_APP}", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [
            sg.Button(
                "Nueva\nPlantilla", key="-NUEVA-", size=(14, 3), button_color=("white", "#2196f3")
            ),
            sg.Button(
                "Actualizar\nPlantilla",
                key="-ACTUALIZAR-",
                size=(14, 3),
                button_color=("white", "#ff9800"),
            ),
            sg.Button(
                "Privada\nCliente", key="-PRIVADA-", size=(14, 3), button_color=("white", "#9c27b0")
            ),
            sg.Button(
                "Pack\n/Bundle", key="-PACK-", size=(14, 3), button_color=("white", "#4caf50")
            ),
        ],
        [
            sg.Button(
                "Regenerar\nDocs", key="-REGEN-", size=(14, 3), button_color=("white", "#607d8b")
            ),
            sg.Button(
                "Publicar\nGitHub",
                key="-PUBLICAR-",
                size=(14, 3),
                button_color=("white", "#e91e63"),
            ),
            sg.Button(
                "YouTube\nTexto", key="-YOUTUBE-", size=(14, 3), button_color=("white", "#f44336")
            ),
            sg.Button("Salir", key="-SALIR-", size=(14, 3), button_color=("white", "#9e9e9e")),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Text(
                f"Plantillas: {stats['publicas']} públicas | {stats['privadas']} privadas | Packs: {stats['total_packs']}"
            ),
        ],
        [sg.Text(f"Manifest: v1.0.0 | Última actualización: {stats['ultima_actualizacion']}")],
    ]

    window = sg.Window(TITULO_APP, layout, finalize=True, element_justification="center")

    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "-SALIR-"):
            window.close()
            return "SALIR"
        if event.startswith("-"):
            window.close()
            return event


# ============================================================
# WIZARD: NUEVA PLANTILLA PUBLICA (7 pasos)
# ============================================================


def _wizard_nueva_publica(gestor: Gestor):
    """Wizard de 7 pasos para crear una plantilla pública."""

    datos: dict = {}
    paso = 1
    total_pasos = 7

    # Auto-sugerir siguiente ID en categoría 1000-1999
    siguiente_id = gestor.siguiente_id_publico(1000)

    while paso <= total_pasos:
        if paso == 1:
            # --- PASO 1: Datos básicos ---
            # Categorías disponibles para sugerir ID
            cat_opciones = [
                f"{v['icono']} {v['nombre']} ({min_v}-{max_v})"
                for (min_v, max_v), v in CATEGORIAS.items()
                if min_v >= 1000
            ]

            layout = [
                [
                    sg.Text(
                        f"NUEVA PLANTILLA PUBLICA - Paso 1/{total_pasos}",
                        font=("Helvetica", 14, "bold"),
                    )
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("Numero:"),
                    sg.Input(default_text=str(siguiente_id), key="-ID-", size=(10, 1)),
                    sg.Text("(auto-sugerido)"),
                ],
                [sg.Text("Nombre:"), sg.Input(key="-NOMBRE-", size=(50, 1))],
                [sg.Text("Descripcion:"), sg.Input(key="-DESC-", size=(80, 1))],
                [sg.Text("Tags (separados por coma):"), sg.Input(key="-TAGS-", size=(80, 1))],
                [
                    sg.Text("Recomendaciones (IDs separados por coma):"),
                    sg.Input(key="-RECOMEND-", size=(40, 1)),
                ],
                [sg.HorizontalSeparator()],
                [sg.Button("Cancelar"), sg.Button("Siguiente >", key="-SIGUIENTE-")],
            ]

            window = sg.Window("Nueva Plantilla Publica", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event != "-SIGUIENTE-":
                return

            # Validar
            try:
                datos["id"] = int(values["-ID-"])
                datos["nombre"] = values["-NOMBRE-"].strip()
                datos["descripcion"] = values["-DESC-"].strip()
                datos["tags"] = [t.strip() for t in values["-TAGS-"].split(",") if t.strip()]
                datos["recomendaciones"] = [
                    int(r.strip()) for r in values["-RECOMEND-"].split(",") if r.strip()
                ]
            except ValueError as e:
                _popup_error(f"Dato invalido: {e}")
                continue

            if not datos["nombre"] or not datos["descripcion"]:
                _popup_error("Nombre y descripcion son obligatorios.")
                continue

            if datos["id"] < 1000:
                _popup_error("ID debe ser >= 1000 para plantillas publicas.")
                continue

            paso = 2

        elif paso == 2:
            # --- PASO 2: Archivos ---
            layout = [
                [
                    sg.Text(
                        f"NUEVA PLANTILLA PUBLICA - Paso 2/{total_pasos}",
                        font=("Helvetica", 14, "bold"),
                    )
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("SQL principal (obligatorio):"),
                    sg.Input(key="-SQL-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("SQL Files", "*.sql"),)),
                ],
                [
                    sg.Text("Dashboard .py (opcional):"),
                    sg.Input(key="-DASH-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("Python Files", "*.py"),)),
                ],
                [
                    sg.Text(""),
                    sg.Text("Los archivos se copiaran a privado_mantenimiento/", text_color="gray"),
                ],
                [
                    sg.Text(""),
                    sg.Text(
                        "Solo SELECT - se validara que no haya CREATE VIEW/ALTER",
                        text_color="orange",
                    ),
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Publica", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 1
                continue
            if event != "-SIGUIENTE-":
                return

            if not values["-SQL-"] or not Path(values["-SQL-"]).exists():
                _popup_error("El archivo SQL es obligatorio y debe existir.")
                continue

            datos["sql_path"] = Path(values["-SQL-"])
            datos["dashboard_path"] = Path(values["-DASH-"]) if values["-DASH-"] else None
            paso = 3

        elif paso == 3:
            # --- PASO 3: Multimedia ---
            layout = [
                [
                    sg.Text(
                        f"NUEVA PLANTILLA PUBLICA - Paso 3/{total_pasos}",
                        font=("Helvetica", 14, "bold"),
                    )
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("Preview (PNG):"),
                    sg.Input(key="-PREVIEW-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("Images", "*.png *.jpg *.jpeg"),)),
                ],
                [sg.Text("YouTube URL:"), sg.Input(key="-YOUTUBE-", size=(80, 1))],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Publica", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 2
                continue
            if event != "-SIGUIENTE-":
                return

            datos["preview_path"] = Path(values["-PREVIEW-"]) if values["-PREVIEW-"] else None
            datos["video_youtube"] = values["-YOUTUBE-"].strip()
            paso = 4

        elif paso == 4:
            # --- PASO 4: Packs ---
            packs_nombres = _obtener_packs_nombres(gestor)
            pack_items = list(packs_nombres.values())

            layout = [
                [
                    sg.Text(
                        f"NUEVA PLANTILLA PUBLICA - Paso 4/{total_pasos}",
                        font=("Helvetica", 14, "bold"),
                    )
                ],
                [sg.HorizontalSeparator()],
                [sg.Text("Asignar a packs:")],
                [
                    sg.Listbox(
                        values=pack_items,
                        key="-PACKS-",
                        size=(70, min(8, max(3, len(pack_items)))),
                        select_mode="multiple",
                    )
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Publica", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 3
                continue
            if event != "-SIGUIENTE-":
                return

            # Resolver pack IDs desde los seleccionados
            selected_packs = values.get("-PACKS-", [])
            id_to_pack = {v: k for k, v in packs_nombres.items()}
            datos["packs"] = [id_to_pack[s] for s in selected_packs if s in id_to_pack]
            paso = 5

        elif paso == 5:
            # --- PASO 5: YouTube SEO (auto-generado) ---
            texto_yt = generar_texto_copiable(
                nombre=datos["nombre"],
                descripcion=datos["descripcion"],
                tags=datos["tags"],
                categoria=get_categoria_por_id(datos["id"])["nombre"],
            )

            layout = [
                [
                    sg.Text(
                        f"NUEVA PLANTILLA PUBLICA - Paso 5/{total_pasos}",
                        font=("Helvetica", 14, "bold"),
                    )
                ],
                [sg.HorizontalSeparator()],
                [sg.Text("Texto YouTube (auto-generado):")],
                [sg.Multiline(default_text=texto_yt, key="-YTTEXT-", size=(80, 15))],
                [sg.Button("Copiar al portapapeles", key="-COPIAR-")],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Publica", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 4
                continue
            if event == "-COPIAR-":
                copiar_al_portapapeles(values["-YTTEXT-"])
                _popup_ok("Texto copiado al portapapeles.")
                # No avanzar paso, reabrir
                continue
            if event != "-SIGUIENTE-":
                return

            paso = 6

        elif paso == 6:
            # --- PASO 6: Confirmación ---
            tiene_dash = datos.get("dashboard_path") and datos["dashboard_path"].exists()
            tiene_preview = datos.get("preview_path") and datos["preview_path"].exists()
            cat = get_categoria_por_id(datos["id"])

            resumen = f"""Se creara:
  - publicas/{datos["id"]:04d} - {datos["nombre"]}/
  - privado_mantenimiento/{datos["id"]:04d} - {datos["nombre"]}/
  - docs/plantillas/{datos["id"]:04d}-xxx.md

Archivos:
  - template.sql (cifrado con libwertyconfig)
  - {"dashboard.py (cifrado)" if tiene_dash else "(sin dashboard)"}
  - {"preview.png" if tiene_preview else "(sin preview)"}
  - template.json

Categoria: {cat["icono"]} {cat["nombre"]}
Tags: {", ".join(datos["tags"])}
Packs: {", ".join(datos["packs"]) if datos["packs"] else "ninguno"}
Recomendaciones: {", ".join(str(r) for r in datos["recomendaciones"]) if datos["recomendaciones"] else "ninguna"}
Version inicial: 1.0.0"""

            layout = [
                [sg.Text("CONFIRMAR NUEVA PLANTILLA", font=("Helvetica", 14, "bold"))],
                [sg.HorizontalSeparator()],
                [sg.Multiline(default_text=resumen, size=(70, 15), disabled=True)],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("CREAR", key="-CONFIRMAR-", button_color=("white", "#4caf50")),
                ],
            ]

            window = sg.Window("Confirmar", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 5
                continue
            if event != "-CONFIRMAR-":
                return

            paso = 7

        elif paso == 7:
            # --- PASO 7: Ejecución ---
            win_progreso = _popup_progreso("Creando plantilla...")
            checks = []

            def progress(msg: str, pct: int):
                _actualizar_progreso(win_progreso, msg, pct)

            try:
                resultado = gestor.crear_plantilla_publica(
                    template_id=datos["id"],
                    nombre=datos["nombre"],
                    descripcion=datos["descripcion"],
                    tags=datos["tags"],
                    sql_path=datos["sql_path"],
                    dashboard_path=datos.get("dashboard_path"),
                    preview_path=datos.get("preview_path"),
                    video_youtube=datos.get("video_youtube", ""),
                    recomendaciones=datos.get("recomendaciones", []),
                    packs=datos.get("packs", []),
                    on_progress=progress,
                )
                checks.append("Plantilla creada")

                # Regenerar README
                _actualizar_progreso(win_progreso, "Regenerando README.md...", 70)
                plantillas = gestor._obtener_plantillas_existentes()
                packs_list = listar_packs(gestor.dir_packs)
                stats = gestor.obtener_estadisticas()
                generar_y_guardar_readme(REPO_ROOT, list(plantillas.values()), packs_list, stats)
                checks.append("README.md actualizado")

                # Regenerar docs MkDocs
                _actualizar_progreso(win_progreso, "Regenerando docs MkDocs...", 80)
                generar_todo(
                    list(plantillas.values()),
                    packs_list,
                    stats,
                    REPO_ROOT / "docs",
                    packs_datos=packs_list,
                )
                checks.append("Docs MkDocs regenerados")

                # Regenerar manifest
                _actualizar_progreso(win_progreso, "Regenerando manifest...", 90)
                generar_y_guardar_manifest(
                    REPO_ROOT, list(plantillas.values()), packs_list, version_manifest="1.0.0"
                )
                checks.append("Manifest actualizado")

                _actualizar_progreso(win_progreso, "Completado!", 100)

            except (GestorError, Exception) as e:
                _cerrar_progreso(win_progreso)
                _popup_error(f"Error al crear plantilla:\n{e}")
                return

            _cerrar_progreso(win_progreso)

            resultado_texto = "\n".join(f"  [OK] {c}" for c in checks)
            resultado_texto += f"\n\n  PLANTILLA {datos['id']:04d} CREADA CON EXITO!"

            layout = [
                [sg.Text("RESULTADO", font=("Helvetica", 14, "bold"))],
                [sg.Multiline(default_text=resultado_texto, size=(60, 10), disabled=True)],
                [sg.Button("Cerrar", key="-CERRAR-"), sg.Button("Abrir carpeta", key="-ABRIR-")],
            ]

            window = sg.Window("Resultado", layout, finalize=True, modal=True)
            event, _ = window.read()
            window.close()

            if event == "-ABRIR-":
                carpeta = REPO_ROOT / "publicas" / f"{datos['id']:04d} - {datos['nombre']}"
                if carpeta.exists():
                    webbrowser.open(str(carpeta))

            return  # Fin del wizard


# ============================================================
# WIZARD: ACTUALIZAR PLANTILLA
# ============================================================


def _wizard_actualizar(gestor: Gestor):
    """Wizard para actualizar una plantilla existente."""

    plantillas = _obtener_plantillas_nombres(gestor, solo_publicas=True)
    if not plantillas:
        _popup_error("No hay plantillas publicas para actualizar.")
        return

    # Paso 1: Seleccionar plantilla
    layout = [
        [sg.Text("ACTUALIZAR PLANTILLA", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Seleccionar plantilla:")],
        [sg.Combo(list(plantillas.values()), key="-PLANTILLA-", size=(60, 1), readonly=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("Tipo de cambio:")],
        [
            sg.Radio("Patch (fix menor)", "BUMP", key="-PATCH-", default=True),
            sg.Radio("Minor (nuevo feature)", "BUMP", key="-MINOR-"),
            sg.Radio("Major (incompatible)", "BUMP", key="-MAJOR-"),
        ],
        [sg.Text("Descripcion del cambio:"), sg.Input(key="-CAMBIO-", size=(60, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.Text("Nuevo SQL (opcional):"),
            sg.Input(key="-SQL-", size=(50, 1)),
            sg.FileBrowse(file_types=(("SQL", "*.sql"),)),
        ],
        [
            sg.Text("Nuevo Dashboard (opcional):"),
            sg.Input(key="-DASH-", size=(50, 1)),
            sg.FileBrowse(file_types=(("Python", "*.py"),)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button("Cancelar"),
            sg.Button("Actualizar", key="-CONFIRMAR-", button_color=("white", "#ff9800")),
        ],
    ]

    window = sg.Window("Actualizar Plantilla", layout, finalize=True, modal=True)
    event, values = window.read()
    window.close()

    if event != "-CONFIRMAR-":
        return

    # Resolver ID
    val_to_id = {v: k for k, v in plantillas.items()}
    if values["-PLANTILLA-"] not in val_to_id:
        _popup_error("Selecciona una plantilla.")
        return

    tid = val_to_id[values["-PLANTILLA-"]]

    # Resolver bump type
    if values["-MINOR-"]:
        bump = BumpType.MINOR
    elif values["-MAJOR-"]:
        bump = BumpType.MAJOR
    else:
        bump = BumpType.PATCH

    cambio_desc = values["-CAMBIO-"].strip()
    if not cambio_desc:
        _popup_error("La descripcion del cambio es obligatoria.")
        return

    nuevo_sql = Path(values["-SQL-"]) if values["-SQL-"] else None
    nuevo_dash = Path(values["-DASH-"]) if values["-DASH-"] else None

    if not nuevo_sql and not nuevo_dash:
        _popup_error("Debes proporcionar al menos un archivo nuevo para actualizar.")
        return

    # Ejecutar
    win = _popup_progreso("Actualizando plantilla...")
    try:
        gestor.actualizar_plantilla(
            template_id=tid,
            bump_type=bump,
            descripcion_cambios=cambio_desc,
            nuevo_sql_path=nuevo_sql,
            nuevo_dashboard_path=nuevo_dash,
            on_progress=lambda msg, pct: _actualizar_progreso(win, msg, pct),
        )

        # Regenerar docs
        _actualizar_progreso(win, "Regenerando documentacion...", 80)
        plantillas_all = gestor._obtener_plantillas_existentes()
        packs_list = listar_packs(gestor.dir_packs)
        stats = gestor.obtener_estadisticas()
        generar_y_guardar_readme(REPO_ROOT, list(plantillas_all.values()), packs_list, stats)
        generar_todo(
            list(plantillas_all.values()),
            packs_list,
            stats,
            REPO_ROOT / "docs",
            packs_datos=packs_list,
        )
        generar_y_guardar_manifest(REPO_ROOT, list(plantillas_all.values()), packs_list)

        _actualizar_progreso(win, "Completado!", 100)
    except (GestorError, Exception) as e:
        _cerrar_progreso(win)
        _popup_error(f"Error al actualizar:\n{e}")
        return

    _cerrar_progreso(win)
    _popup_ok(f"Plantilla {tid:04d} actualizada correctamente.")


# ============================================================
# WIZARD: PLANTILLA PRIVADA (5 pasos)
# ============================================================


def _wizard_privada(gestor: Gestor):
    """Wizard de 5 pasos para crear una plantilla privada de cliente."""

    datos: dict = {}
    paso = 1

    while paso <= 5:
        if paso == 1:
            # Datos del cliente
            siguiente_id = gestor.siguiente_id_privado()
            plantillas_pub = _obtener_plantillas_nombres(gestor, solo_publicas=True)
            base_options = ["(Ninguna)"] + list(plantillas_pub.values())

            layout = [
                [sg.Text("NUEVA PLANTILLA PRIVADA - Paso 1/5", font=("Helvetica", 14, "bold"))],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("Codigo cliente:"),
                    sg.Input(key="-CLIENTE-", size=(20, 1)),
                    sg.Text("Formato: CLI-XXXXX", text_color="gray"),
                ],
                [
                    sg.Text("Clave licencia:"),
                    sg.Input(key="-LICENCIA-", size=(40, 1), password_char="*"),
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("ID plantilla:"),
                    sg.Input(default_text=str(siguiente_id), key="-ID-", size=(10, 1)),
                ],
                [
                    sg.Text("Partir de plantilla publica?"),
                    sg.Combo(
                        base_options, default_value=base_options[0], key="-BASE-", readonly=True
                    ),
                ],
                [sg.Text("Nombre:"), sg.Input(key="-NOMBRE-", size=(60, 1))],
                [sg.Text("Descripcion:"), sg.Input(key="-DESC-", size=(60, 1))],
                [sg.HorizontalSeparator()],
                [sg.Button("Cancelar"), sg.Button("Siguiente >", key="-SIGUIENTE-")],
            ]

            window = sg.Window("Nueva Plantilla Privada", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event != "-SIGUIENTE-":
                return

            try:
                datos["cliente_codigo"] = values["-CLIENTE-"].strip()
                datos["cliente_licencia"] = values["-LICENCIA-"].strip()
                datos["id"] = int(values["-ID-"])
                datos["nombre"] = values["-NOMBRE-"].strip()
                datos["descripcion"] = values["-DESC-"].strip()
            except ValueError as e:
                _popup_error(f"Dato invalido: {e}")
                continue

            if not datos["cliente_codigo"] or not datos["cliente_licencia"]:
                _popup_error("Codigo y licencia del cliente son obligatorios.")
                continue

            paso = 2

        elif paso == 2:
            # Archivos
            layout = [
                [sg.Text("NUEVA PLANTILLA PRIVADA - Paso 2/5", font=("Helvetica", 14, "bold"))],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("SQL principal:"),
                    sg.Input(key="-SQL-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("SQL", "*.sql"),)),
                ],
                [
                    sg.Text("Dashboard (opcional):"),
                    sg.Input(key="-DASH-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("Python", "*.py"),)),
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Privada", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 1
                continue
            if event != "-SIGUIENTE-":
                return

            if not values["-SQL-"] or not Path(values["-SQL-"]).exists():
                _popup_error("El archivo SQL es obligatorio.")
                continue

            datos["sql_path"] = Path(values["-SQL-"])
            datos["dashboard_path"] = Path(values["-DASH-"]) if values["-DASH-"] else None
            datos["preview_path"] = None
            datos["tags"] = ["privada", datos["cliente_codigo"].lower()]
            paso = 3

        elif paso == 3:
            # Preview
            layout = [
                [sg.Text("NUEVA PLANTILLA PRIVADA - Paso 3/5", font=("Helvetica", 14, "bold"))],
                [sg.HorizontalSeparator()],
                [
                    sg.Text("Preview (PNG, opcional):"),
                    sg.Input(key="-PREVIEW-", size=(60, 1)),
                    sg.FileBrowse(file_types=(("Images", "*.png *.jpg"),)),
                ],
                [sg.HorizontalSeparator()],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("Siguiente >", key="-SIGUIENTE-"),
                ],
            ]

            window = sg.Window("Nueva Plantilla Privada", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 2
                continue
            if event != "-SIGUIENTE-":
                return

            datos["preview_path"] = Path(values["-PREVIEW-"]) if values["-PREVIEW-"] else None
            paso = 4

        elif paso == 4:
            # Confirmación
            resumen = f"""Plantilla privada para: {datos["cliente_codigo"]}
ID: {datos["id"]:04d}
Nombre: {datos["nombre"]}
SQL: {datos["sql_path"].name}
Dashboard: {datos["dashboard_path"].name if datos.get("dashboard_path") else "(sin dashboard)"}
Preview: {"Si" if datos.get("preview_path") else "No"}

El SQL se cifrara con la clave de licencia del cliente."""

            layout = [
                [sg.Text("CONFIRMAR PLANTILLA PRIVADA", font=("Helvetica", 14, "bold"))],
                [sg.Multiline(default_text=resumen, size=(60, 10), disabled=True)],
                [
                    sg.Button("< Anterior", key="-ANTERIOR-"),
                    sg.Button("Cancelar"),
                    sg.Button("CREAR", key="-CONFIRMAR-", button_color=("white", "#9c27b0")),
                ],
            ]

            window = sg.Window("Confirmar", layout, finalize=True, modal=True)
            event, values = window.read()
            window.close()

            if event == "-ANTERIOR-":
                paso = 3
                continue
            if event != "-CONFIRMAR-":
                return

            paso = 5

        elif paso == 5:
            # Ejecución
            win = _popup_progreso("Creando plantilla privada...")
            try:
                gestor.crear_plantilla_privada(
                    template_id=datos["id"],
                    nombre=datos["nombre"],
                    descripcion=datos["descripcion"],
                    tags=datos["tags"],
                    cliente_codigo=datos["cliente_codigo"],
                    cliente_licencia=datos["cliente_licencia"],
                    sql_path=datos["sql_path"],
                    dashboard_path=datos.get("dashboard_path"),
                    preview_path=datos.get("preview_path"),
                    on_progress=lambda msg, pct: _actualizar_progreso(win, msg, pct),
                )

                # Regenerar manifest y docs
                _actualizar_progreso(win, "Regenerando docs...", 80)
                plantillas_all = gestor._obtener_plantillas_existentes()
                packs_list = listar_packs(gestor.dir_packs)
                stats = gestor.obtener_estadisticas()
                generar_y_guardar_readme(
                    REPO_ROOT, list(plantillas_all.values()), packs_list, stats
                )
                generar_todo(
                    list(plantillas_all.values()),
                    packs_list,
                    stats,
                    REPO_ROOT / "docs",
                    packs_datos=packs_list,
                )
                generar_y_guardar_manifest(REPO_ROOT, list(plantillas_all.values()), packs_list)

                _actualizar_progreso(win, "Completado!", 100)
            except (GestorError, Exception) as e:
                _cerrar_progreso(win)
                _popup_error(f"Error al crear plantilla privada:\n{e}")
                return

            _cerrar_progreso(win)
            _popup_ok(f"Plantilla privada {datos['id']:04d} para {datos['cliente_codigo']} creada.")
            return


# ============================================================
# WIZARD: PACKS
# ============================================================


def _wizard_pack(gestor: Gestor):
    """Wizard para crear/editar packs."""

    plantillas_disponibles = _obtener_plantillas_nombres(gestor, solo_publicas=True)
    packs_existentes = listar_packs(gestor.dir_packs)

    # Opciones: crear nuevo o editar existente
    opciones = ["[Crear pack nuevo]"] + [
        f"{p.get('icono', '')} {p['nombre']} ({p['total_plantillas']} plantillas)"
        for p in packs_existentes
    ]

    layout = [
        [sg.Text("GESTION DE PACKS", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [
            sg.Text("Accion:"),
            sg.Combo(
                opciones, default_value=opciones[0], key="-ACCION-", readonly=True, size=(50, 1)
            ),
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("ID del pack:"), sg.Input(key="-PACKID-", size=(30, 1))],
        [sg.Text("Nombre:"), sg.Input(key="-NOMBRE-", size=(50, 1))],
        [sg.Text("Descripcion:"), sg.Input(key="-DESC-", size=(60, 1))],
        [
            sg.Text("Icono:"),
            sg.Combo(
                ["package", "box", "chart", "file", "gear"],
                default_value="package",
                key="-ICONO-",
                size=(10, 1),
            ),
        ],
        [sg.HorizontalSeparator()],
        [sg.Text("Plantillas incluidas (seleccionar):")],
        [
            sg.Listbox(
                values=list(plantillas_disponibles.values()),
                key="-PLANTILLAS-",
                size=(70, min(10, max(3, len(plantillas_disponibles)))),
                select_mode="multiple",
            )
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button("Cancelar"),
            sg.Button("Guardar Pack", key="-GUARDAR-", button_color=("white", "#4caf50")),
        ],
    ]

    window = sg.Window("Gestion de Packs", layout, finalize=True, modal=True)
    event, values = window.read()
    window.close()

    if event != "-GUARDAR-":
        return

    # Resolver plantillas seleccionadas
    val_to_id = {v: k for k, v in plantillas_disponibles.items()}
    seleccionadas = [val_to_id[s] for s in values.get("-PLANTILLAS-", []) if s in val_to_id]

    if len(seleccionadas) < 2:
        _popup_error("Un pack debe contener al menos 2 plantillas.")
        return

    pack_id = values["-PACKID-"].strip()
    nombre = values["-NOMBRE-"].strip()
    descripcion = values["-DESC-"].strip()
    icono = values["-ICONO-"]

    if not pack_id or not nombre:
        _popup_error("ID y nombre son obligatorios.")
        return

    # Validar
    pack_data = crear_pack(pack_id, nombre, descripcion, seleccionadas, icono)
    existentes = set(gestor._obtener_plantillas_existentes().keys())
    errores = validar_pack(pack_data, existentes)

    if errores:
        _popup_error("Pack invalido:\n" + "\n".join(errores))
        return

    guardar_pack(pack_data, gestor.dir_packs)
    _popup_ok(f"Pack '{nombre}' guardado con {len(seleccionadas)} plantillas.")


# ============================================================
# DIALOGO: REGENERAR DOCS
# ============================================================


def _dialogo_regenerar(gestor: Gestor):
    """Dialogo para regenerar toda la documentacion."""

    layout = [
        [sg.Text("REGENERAR DOCUMENTACION", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Checkbox("README.md", key="-README-", default=True)],
        [sg.Checkbox("MkDocs (docs/ + Open Graph)", key="-MKDOCS-", default=True)],
        [sg.Checkbox("RSS feed (feed.xml)", key="-RSS-", default=True)],
        [sg.Checkbox("manifest-templates.json", key="-MANIFEST-", default=True)],
        [sg.HorizontalSeparator()],
        [
            sg.Text(
                "Se regeneraran todos los archivos desde los template.json existentes.",
                text_color="gray",
            )
        ],
        [
            sg.Button("Cancelar"),
            sg.Button("Regenerar", key="-REGEN-", button_color=("white", "#607d8b")),
        ],
    ]

    window = sg.Window("Regenerar Docs", layout, finalize=True, modal=True)
    event, values = window.read()
    window.close()

    if event != "-REGEN-":
        return

    plantillas = gestor._obtener_plantillas_existentes()
    packs_list = listar_packs(gestor.dir_packs)
    stats = gestor.obtener_estadisticas()
    plantillas_list = list(plantillas.values())

    win = _popup_progreso("Regenerando documentacion...")

    try:
        if values["-README-"]:
            _actualizar_progreso(win, "Generando README.md...", 20)
            generar_y_guardar_readme(REPO_ROOT, plantillas_list, packs_list, stats)

        if values["-MKDOCS-"] or values["-RSS-"]:
            _actualizar_progreso(win, "Generando docs MkDocs...", 50)
            generar_todo(
                plantillas_list, packs_list, stats, REPO_ROOT / "docs", packs_datos=packs_list
            )

        if values["-MANIFEST-"]:
            _actualizar_progreso(win, "Generando manifest...", 80)
            generar_y_guardar_manifest(REPO_ROOT, plantillas_list, packs_list)

        _actualizar_progreso(win, "Completado!", 100)
    except Exception as e:
        _cerrar_progreso(win)
        _popup_error(f"Error al regenerar:\n{e}")
        return

    _cerrar_progreso(win)
    _popup_ok("Documentacion regenerada correctamente.")


# ============================================================
# DIALOGO: PUBLICAR EN GITHUB
# ============================================================


def _dialogo_publicar(gestor: Gestor):
    """Dialogo para publicar cambios en GitHub."""

    import subprocess

    # Verificar que es un repo git
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        cambios = [l for l in result.stdout.strip().split("\n") if l.strip()]
    except Exception:
        _popup_error(
            "No se pudo ejecutar git. Verifica que git esta instalado y el repo esta inicializado."
        )
        return

    if not cambios:
        _popup_ok("No hay cambios pendientes para publicar.")
        return

    cambios_texto = "\n".join(cambios[:30])
    if len(cambios) > 30:
        cambios_texto += f"\n... y {len(cambios) - 30} archivos mas."

    layout = [
        [sg.Text("PUBLICAR EN GITHUB", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text(f"Cambios pendientes ({len(cambios)} archivos):")],
        [sg.Multiline(default_text=cambios_texto, size=(70, 12), disabled=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("Commit message:")],
        [sg.Input(key="-MSG-", size=(70, 1), default_text="feat: actualizar plantillas")],
        [sg.HorizontalSeparator()],
        [sg.Text("privado_mantenimiento/ esta en .gitignore (no se sube)", text_color="orange")],
        [
            sg.Button("Cancelar"),
            sg.Button("PUBLICAR", key="-PUB-", button_color=("white", "#e91e63")),
        ],
    ]

    window = sg.Window("Publicar en GitHub", layout, finalize=True, modal=True)
    event, values = window.read()
    window.close()

    if event != "-PUB-":
        return

    msg = values["-MSG-"].strip()
    if not msg:
        _popup_error("El commit message es obligatorio.")
        return

    win = _popup_progreso("Publicando...")

    try:
        _actualizar_progreso(win, "git add ...", 20)
        subprocess.run(["git", "add", "."], cwd=str(REPO_ROOT), check=True, capture_output=True)

        _actualizar_progreso(win, "git commit ...", 50)
        subprocess.run(
            ["git", "commit", "-m", msg], cwd=str(REPO_ROOT), check=True, capture_output=True
        )

        _actualizar_progreso(win, "git push ...", 80)
        subprocess.run(["git", "push"], cwd=str(REPO_ROOT), check=True, capture_output=True)

        _actualizar_progreso(win, "Completado!", 100)
    except subprocess.CalledProcessError as e:
        _cerrar_progreso(win)
        stderr = e.stderr.decode() if e.stderr else str(e)
        _popup_error(f"Error al publicar:\n{stderr}")
        return

    _cerrar_progreso(win)
    _popup_ok(f"Publicado con exito.\n\nCommit: {msg}")


# ============================================================
# DIALOGO: YOUTUBE TEXTO
# ============================================================


def _dialogo_youtube(gestor: Gestor):
    """Genera texto YouTube para una plantilla existente."""

    plantillas = _obtener_plantillas_nombres(gestor, solo_publicas=True)
    if not plantillas:
        _popup_error("No hay plantillas publicas.")
        return

    layout = [
        [sg.Text("TEXTO YOUTUBE", font=("Helvetica", 14, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Seleccionar plantilla:")],
        [sg.Combo(list(plantillas.values()), key="-PLANTILLA-", size=(60, 1), readonly=True)],
        [sg.HorizontalSeparator()],
        [sg.Multiline(key="-RESULTADO-", size=(80, 15), disabled=True)],
        [
            sg.Button("Generar", key="-GENERAR-"),
            sg.Button("Copiar al portapapeles", key="-COPIAR-"),
        ],
        [sg.Button("Cerrar")],
    ]

    window = sg.Window("YouTube Texto", layout, finalize=True, modal=True)
    texto_generado = ""

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Cerrar"):
            break

        if event == "-GENERAR-":
            val_to_id = {v: k for k, v in plantillas.items()}
            if values["-PLANTILLA-"] not in val_to_id:
                _popup_error("Selecciona una plantilla.")
                continue

            tid = val_to_id[values["-PLANTILLA-"]]
            p = gestor._obtener_plantillas_existentes()[tid]
            cat = p.get("categoria", {}).get("nombre", "")

            texto_generado = generar_texto_copiable(
                nombre=p["nombre"],
                descripcion=p.get("descripcion", ""),
                tags=p.get("tags", []),
                categoria=cat,
            )
            window["-RESULTADO-"].update(texto_generado, disabled=False)

        if event == "-COPIAR-" and texto_generado:
            if copiar_al_portapapeles(texto_generado):
                _popup_ok("Texto copiado al portapapeles.")
            else:
                _popup_error("No se pudo copiar al portapapeles.")

    window.close()


# ============================================================
# BUCLE PRINCIPAL
# ============================================================


def main():
    """Entry point de la GUI de gestion."""
    gestor = _get_gestor()

    while True:
        evento = _ventana_principal(gestor)

        if evento == "SALIR":
            break
        elif evento == "-NUEVA-":
            _wizard_nueva_publica(gestor)
        elif evento == "-ACTUALIZAR-":
            _wizard_actualizar(gestor)
        elif evento == "-PRIVADA-":
            _wizard_privada(gestor)
        elif evento == "-PACK-":
            _wizard_pack(gestor)
        elif evento == "-REGEN-":
            _dialogo_regenerar(gestor)
        elif evento == "-PUBLICAR-":
            _dialogo_publicar(gestor)
        elif evento == "-YOUTUBE-":
            _dialogo_youtube(gestor)

    sg.popup_ok("Hasta luego!", title=TITULO_APP)


if __name__ == "__main__":
    main()
