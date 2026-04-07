"""
Repositorio de Plantillas Sage50BI — Entry Point

Uso:
    python main.py          → Abre la GUI de gestión
    python main.py --cli    → Modo CLI (ver subcomandos)
    python main.py --help   → Ayuda
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def main():
    """Entry point principal."""
    if len(sys.argv) > 1:
        _modo_cli(sys.argv[1:])
    else:
        _modo_gui()


def _modo_gui():
    """Abre la GUI PySimpleGUI."""
    try:
        from gestion.gestion import main as gui_main

        gui_main()
    except ImportError as e:
        print(f"Error al cargar la GUI: {e}")
        print("Instala las dependencias: pip install -r requirements.txt")
        sys.exit(1)


def _modo_cli(args: list[str]):
    """Modo línea de comandos."""
    if not args or args[0] in ("--help", "-h", "help"):
        _mostrar_ayuda()
        return

    comando = args[0]

    if comando == "regenerar":
        _cli_regenerar()
    elif comando == "stats":
        _cli_stats()
    elif comando == "listar":
        _cli_listar()
    elif comando == "verificar":
        _cli_verificar()
    else:
        print(f"Comando desconocido: {comando}")
        _mostrar_ayuda()


def _mostrar_ayuda():
    print("""
Repositorio de Plantillas Sage50BI - CLI

Uso:
    python main.py              Abre la GUI de gestión
    python main.py stats        Muestra estadísticas del repositorio
    python main.py listar       Lista todas las plantillas
    python main.py regenerar    Regenera toda la documentación
    python main.py verificar    Verifica integridad del repositorio
    python main.py help         Muestra esta ayuda
""")


def _cli_stats():
    from gestion.gestor import Gestor

    gestor = Gestor(REPO_ROOT)
    stats = gestor.obtener_estadisticas()

    print(f"=== Estadísticas del Repositorio ===")
    print(f"  Plantillas públicas: {stats['publicas']}")
    print(f"  Plantillas privadas: {stats['privadas']}")
    print(f"  Total:               {stats['total_plantillas']}")
    print(f"  Packs:               {stats['total_packs']}")
    print(f"  Por categoría:")
    for cat, count in stats.get("por_categoria", {}).items():
        print(f"    - {cat}: {count}")


def _cli_listar():
    from gestion.gestor import Gestor

    gestor = Gestor(REPO_ROOT)
    plantillas = gestor.listar_plantillas()

    if not plantillas:
        print("No hay plantillas.")
        return

    print(f"{'ID':>6} {'Nombre':<40} {'Versión':<8} {'Tipo':<10} {'Categoría'}")
    print("-" * 90)
    for p in plantillas:
        print(f"{p['id']:>6} {p['nombre']:<40} {p['version']:<8} {p['tipo']:<10} {p['categoria']}")


def _cli_regenerar():
    from gestion.gestor import Gestor
    from gestion.readme_generator import generar_y_guardar_readme
    from gestion.mkdocs_generator import generar_todo
    from gestion.manifest_generator import generar_y_guardar_manifest
    from gestion.pack_generator import listar_packs

    gestor = Gestor(REPO_ROOT)
    plantillas = gestor._obtener_plantillas_existentes()
    packs = listar_packs(gestor.dir_packs)
    stats = gestor.obtener_estadisticas()
    plantillas_list = list(plantillas.values())

    print("Regenerando README.md...")
    generar_y_guardar_readme(REPO_ROOT, plantillas_list, packs, stats)

    print("Regenerando docs MkDocs...")
    generar_todo(plantillas_list, packs, stats, REPO_ROOT / "docs", packs_datos=packs)

    print("Regenerando manifest...")
    generar_y_guardar_manifest(REPO_ROOT, plantillas_list, packs)

    print("Documentación regenerada correctamente.")


def _cli_verificar():
    from gestion.gestor import Gestor
    from gestion.cifrado import verificar_cifrado_roundtrip

    gestor = Gestor(REPO_ROOT)
    plantillas = gestor._obtener_plantillas_existentes()

    print(f"Verificando {len(plantillas)} plantillas...")
    errores = []

    for tid, data in plantillas.items():
        # Verificar que los archivos existen
        if data["tipo"] == "publica":
            carpeta = gestor.dir_publicas / f"{tid:04d} - {data['nombre']}"
        else:
            cliente = data.get("cliente", {}).get("codigo", "")
            carpeta = gestor.dir_privadas / cliente

        if not carpeta.exists():
            errores.append(f"{tid:04d}: Carpeta no encontrada: {carpeta}")
            continue

        template_json = carpeta / "template.json"
        if not template_json.exists():
            errores.append(f"{tid:04d}: template.json no encontrado")
            continue

        sql = carpeta / "template.sql"
        if not sql.exists():
            errores.append(f"{tid:04d}: template.sql no encontrado")

    if errores:
        print(f"Errores encontrados ({len(errores)}):")
        for e in errores:
            print(f"  [X] {e}")
    else:
        print("Todas las plantillas verificadas correctamente.")


if __name__ == "__main__":
    main()
