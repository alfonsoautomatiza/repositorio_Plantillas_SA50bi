"""
Genera imagenes preview placeholder para plantillas que no tienen preview.png.
Uso: python scripts/generate_previews.py
"""

import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow no esta instalado. Ejecuta: pip install Pillow")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLICAS_DIR = REPO_ROOT / "publicas"

# Colores por rango de categoria
CATEGORY_COLORS = {
    1: (33, 150, 243),  # 1000-1999 Informes y Listados: Blue #2196F3
    2: (76, 175, 80),  # 2000-2999 Facturas y Documentos: Green #4CAF50
    3: (156, 39, 176),  # 3000-3999 Balances y Contabilidad: Purple #9C27B0
    4: (255, 152, 0),  # 4000-4999 Dashboard y Graficos: Orange #FF9800
}

WIDTH = 800
HEIGHT = 600
HEADER_HEIGHT = 80
FOOTER_HEIGHT = 50


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Intenta cargar Arial con fallback a la fuente por defecto."""
    font_names = []
    if bold:
        font_names.extend(
            [
                "arialbd.ttf",
                "Arial Bold.ttf",
                "ArialBD.ttf",
            ]
        )
    font_names.extend(
        [
            "arial.ttf",
            "Arial.ttf",
            "LiberationSans-Regular.ttf",
            "DejaVuSans.ttf",
        ]
    )

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue

    # Fallback: fuente por defecto de Pillow
    print(f"  [WARN] No se encontro TTF, usando fuente por defecto (tamano {size})")
    return ImageFont.load_default()


def _draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int):
    """Dibuja patron de grid sutil sobre el fondo."""
    grid_color = (230, 230, 230)
    spacing = 30
    for x in range(0, width, spacing):
        draw.line([(x, HEADER_HEIGHT), (x, height - FOOTER_HEIGHT)], fill=grid_color, width=1)
    for y in range(HEADER_HEIGHT, height - FOOTER_HEIGHT, spacing):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    width: int = WIDTH,
):
    """Dibuja texto centrado horizontalmente."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (width - text_w) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _truncate_text(text: str, max_chars: int) -> str:
    """Trunca texto con elipsis si excede max_chars."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def generate_preview(template_dir: Path) -> bool:
    """Genera preview.png para una plantilla si no existe. Devuelve True si se genero."""
    preview_path = template_dir / "preview.png"
    if preview_path.exists():
        print(f"  [SKIP] {template_dir.name} ya tiene preview.png")
        return False

    # Leer template.json
    template_json_path = template_dir / "template.json"
    if not template_json_path.exists():
        print(f"  [SKIP] {template_dir.name} no tiene template.json")
        return False

    with open(template_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    template_id = data.get("id", 0)
    nombre = data.get("nombre", "Sin nombre")
    version = data.get("version", "?.?.?")
    categoria = data.get("categoria", {})
    categoria_nombre = categoria.get("nombre", "Sin categoria")

    # Determinar color por rango
    rango_key = template_id // 1000
    color = CATEGORY_COLORS.get(rango_key, (100, 100, 100))
    lighter_color = tuple(min(c + 60, 255) for c in color)

    # Crear imagen
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # --- Header bar ---
    draw.rectangle([(0, 0), (WIDTH, HEADER_HEIGHT)], fill=color)

    # Nombre de la plantilla en el header
    header_font = _get_font(26, bold=True)
    display_name = _truncate_text(nombre, 42)
    _draw_centered_text(draw, display_name, 22, header_font, (255, 255, 255))

    # --- Grid pattern ---
    _draw_grid(draw, WIDTH, HEIGHT)

    # --- Centro: zona de informacion ---
    center_y_start = 160

    # Template ID
    id_font = _get_font(48, bold=True)
    _draw_centered_text(draw, f"#{template_id:04d}", center_y_start, id_font, color)

    # Categoria
    cat_font = _get_font(20)
    _draw_centered_text(draw, categoria_nombre, center_y_start + 75, cat_font, lighter_color)

    # Separador decorativo
    sep_y = center_y_start + 115
    sep_margin = 250
    draw.line(
        [(sep_margin, sep_y), (WIDTH - sep_margin, sep_y)],
        fill=color,
        width=2,
    )

    # Version
    ver_font = _get_font(16)
    _draw_centered_text(draw, f"v{version}", sep_y + 15, ver_font, (150, 150, 150))

    # Marca de agua "PREVIEW"
    watermark_font = _get_font(36, bold=True)
    _draw_centered_text(draw, "PREVIEW", sep_y + 55, watermark_font, (220, 220, 220))

    # --- Footer ---
    footer_y = HEIGHT - FOOTER_HEIGHT
    draw.rectangle([(0, footer_y), (WIDTH, HEIGHT)], fill=color)

    # Texto del footer
    footer_font = _get_font(16, bold=True)
    _draw_centered_text(draw, "Sage50BI", footer_y + 8, footer_font, (255, 255, 255))

    sub_font = _get_font(11)
    _draw_centered_text(
        draw, "ALCA TIC, S.L. | pedironline.com", footer_y + 30, sub_font, (220, 220, 220)
    )

    # Guardar
    img.save(preview_path, "PNG")
    print(f"  [OK]   {template_dir.name} -> preview.png ({preview_path.stat().st_size} bytes)")
    return True


def main():
    print("Generador de preview images para plantillas Sage50BI")
    print("=" * 55)

    if not PUBLICAS_DIR.exists():
        print(f"ERROR: No existe el directorio {PUBLICAS_DIR}")
        sys.exit(1)

    # Buscar todas las plantillas
    template_dirs = sorted(
        d for d in PUBLICAS_DIR.iterdir() if d.is_dir() and (d / "template.json").exists()
    )

    if not template_dirs:
        print("No se encontraron plantillas en publicas/")
        return

    print(f"Encontradas {len(template_dirs)} plantillas\n")

    generated = 0
    skipped = 0

    for td in template_dirs:
        if generate_preview(td):
            generated += 1
        else:
            skipped += 1

    print(f"\n{'=' * 55}")
    print(f"RESUMEN:")
    print(f"  Generadas: {generated}")
    print(f"  Omitidas (ya existian): {skipped}")
    print(f"  Total procesadas: {len(template_dirs)}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
