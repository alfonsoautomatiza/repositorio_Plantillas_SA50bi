"""
Genera imagenes Open Graph (1200x630) para cada plantilla de Sage50BI.
Usadas por Twitter/Facebook/LinkedIn al compartir enlaces.

Uso: python scripts/generate_og_images.py
"""

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow no esta instalado. Ejecuta: pip install Pillow")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLICAS_DIR = REPO_ROOT / "publicas"
DOCS_IMG_DIR = REPO_ROOT / "docs" / "img"

# Dimensiones OG estandar
WIDTH = 1200
HEIGHT = 630

# Gradientes por rango de categoria (color_inicio, color_fin)
CATEGORY_GRADIENTS = {
    1: ((21, 101, 192), (33, 150, 243)),  # 1000-1999: Blue (#1565C0 -> #2196F3)
    2: ((46, 125, 50), (76, 175, 80)),  # 2000-2999: Green (#2E7D32 -> #4CAF50)
    3: ((106, 27, 154), (156, 39, 176)),  # 3000-3999: Purple (#6A1B9A -> #9C27B0)
    4: ((230, 81, 0), (255, 152, 0)),  # 4000-4999: Orange (#E65100 -> #FF9800)
}

# Nombres de categoria para badges
CATEGORY_NAMES = {
    1: "Informes y Listados",
    2: "Facturas y Documentos",
    3: "Balances y Contabilidad",
    4: "Dashboard y Graficos",
}


def _interpolate_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Interpola entre dos colores RGB. t=0 -> c1, t=1 -> c2."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _draw_gradient(img: Image.Image, c1: tuple, c2: tuple):
    """Dibuja un gradiente horizontal de c1 (izquierda) a c2 (derecha)."""
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        t = x / max(WIDTH - 1, 1)
        color = _interpolate_color(c1, c2, t)
        draw.line([(x, 0), (x, HEIGHT)], fill=color)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga Arial con fallback a fuente por defecto."""
    font_names = []
    if bold:
        font_names.extend(["arialbd.ttf", "Arial Bold.ttf", "ArialBD.ttf"])
    font_names.extend(["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"])

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue

    print(f"  [WARN] No se encontro TTF, usando fuente por defecto (tamano {size})")
    return ImageFont.load_default()


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, bbox: tuple, radius: int, fill: tuple):
    """Dibuja un rectangulo con bordes redondeados."""
    x0, y0, x1, y1 = bbox
    draw.rectangle([(x0 + radius, y0), (x1 - radius, y1)], fill=fill)
    draw.rectangle([(x0, y0 + radius), (x1, y1 - radius)], fill=fill)
    draw.pieslice([(x0, y0), (x0 + 2 * radius, y0 + 2 * radius)], 180, 270, fill=fill)
    draw.pieslice([(x1 - 2 * radius, y0), (x1, y0 + 2 * radius)], 270, 360, fill=fill)
    draw.pieslice([(x0, y1 - 2 * radius), (x0 + 2 * radius, y1)], 90, 180, fill=fill)
    draw.pieslice([(x1 - 2 * radius, y1 - 2 * radius), (x1, y1)], 0, 90, fill=fill)


def _truncate_text(text: str, max_chars: int) -> str:
    """Trunca texto con elipsis si excede max_chars."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def generate_og_image(data: dict, output_path: Path) -> bool:
    """Genera una imagen OG 1200x630 para una plantilla."""
    template_id = data.get("id", 0)
    nombre = data.get("nombre", "Sin nombre")
    version = data.get("version", "1.0.0")
    categoria = data.get("categoria", {})
    cat_nombre = categoria.get("nombre", "")
    tags = data.get("tags", [])

    # Gradiente por rango
    rango_key = template_id // 1000
    gradient = CATEGORY_GRADIENTS.get(rango_key, ((50, 50, 80), (80, 80, 120)))
    c_start, c_end = gradient

    # Color aclarado para badges
    badge_color = _interpolate_color(c_start, (255, 255, 255), 0.25)

    # Crear imagen con gradiente
    img = Image.new("RGB", (WIDTH, HEIGHT))
    _draw_gradient(img, c_start, c_end)
    draw = ImageDraw.Draw(img)

    # --- Overlay oscuro semitransparente para legibilidad ---
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(0, 0, 0, 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- ZONA IZQUIERDA (x: 60-720) ---
    left_margin = 60

    # ID de plantilla grande
    id_font = _get_font(28, bold=True)
    draw.text((left_margin, 60), f"#{template_id:04d}", font=id_font, fill=(255, 255, 255))

    # Nombre de la plantilla (hasta 2 lineas)
    name_font = _get_font(38, bold=True)
    max_chars_line = 28
    display_name = _truncate_text(nombre, 56)

    if len(display_name) > max_chars_line:
        # Intentar cortar en espacio
        words = display_name.split(" ")
        line1, line2 = "", ""
        for word in words:
            test = f"{line1} {word}".strip()
            if len(test) <= max_chars_line:
                line1 = test
            else:
                line2 = f"{line2} {word}".strip()
        if not line2:
            line1 = display_name[:max_chars_line]
            line2 = display_name[max_chars_line:]
    else:
        line1 = display_name
        line2 = ""

    draw.text((left_margin, 100), line1, font=name_font, fill=(255, 255, 255))
    if line2:
        draw.text((left_margin, 148), line2, font=name_font, fill=(255, 255, 255))
        badge_y = 200
    else:
        badge_y = 155

    # Badge de categoria
    if cat_nombre:
        cat_font = _get_font(16)
        cat_text = f"  {cat_nombre}  "
        bbox = draw.textbbox((0, 0), cat_text, font=cat_font)
        cat_w = bbox[2] - bbox[0] + 16
        cat_h = bbox[3] - bbox[1] + 10
        _draw_rounded_rect(
            draw, (left_margin, badge_y, left_margin + cat_w, badge_y + cat_h), 6, badge_color
        )
        draw.text((left_margin + 8, badge_y + 4), cat_text, font=cat_font, fill=(255, 255, 255))
        version_x = left_margin + cat_w + 12
    else:
        version_x = left_margin

    # Badge de version
    ver_font = _get_font(16)
    ver_text = f"  v{version}  "
    bbox = draw.textbbox((0, 0), ver_text, font=ver_font)
    ver_w = bbox[2] - bbox[0] + 16
    ver_h = bbox[3] - bbox[1] + 10
    _draw_rounded_rect(
        draw, (version_x, badge_y, version_x + ver_w, badge_y + ver_h), 6, badge_color
    )
    draw.text((version_x + 8, badge_y + 4), ver_text, font=ver_font, fill=(255, 255, 255))

    # Descripcion (max 2 lineas)
    desc = data.get("descripcion", "")
    if desc:
        desc_font = _get_font(15)
        desc_display = _truncate_text(desc, 90)
        draw.text((left_margin, badge_y + 50), desc_display, font=desc_font, fill=(220, 220, 220))

    # --- ZONA DERECHA (x: 780-1140) ---
    right_x = 830

    # Linea divisoria vertical sutil
    draw.line([(760, 80), (760, HEIGHT - 100)], fill=(255, 255, 255), width=1)

    # Sage50BI logo area
    logo_font = _get_font(42, bold=True)
    draw.text((right_x, 200), "Sage50BI", font=logo_font, fill=(255, 255, 255))

    sub_font = _get_font(20)
    draw.text((right_x, 260), "ALCA TIC, S.L.", font=sub_font, fill=(200, 200, 200))

    url_font = _get_font(14)
    draw.text((right_x, 295), "pedironline.com", font=url_font, fill=(180, 180, 180))

    # Badge "plantillas gratuitas"
    free_font = _get_font(16)
    free_text = "  plantillas gratuitas  "
    bbox = draw.textbbox((0, 0), free_text, font=free_font)
    free_w = bbox[2] - bbox[0] + 16
    free_h = bbox[3] - bbox[1] + 10
    _draw_rounded_rect(draw, (right_x, 340, right_x + free_w, 340 + free_h), 6, (255, 255, 255))
    draw.text((right_x + 8, 344), free_text, font=free_font, fill=c_start)

    # --- BARRA INFERIOR ---
    bar_y = HEIGHT - 55
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=(0, 0, 0, 80))

    # Tags en la barra inferior
    if tags:
        tag_font = _get_font(13)
        tags_display = "  ".join(f"#{t}" for t in tags[:5])
        tags_truncated = _truncate_text(tags_display, 80)
        draw.text((left_margin, bar_y + 8), tags_truncated, font=tag_font, fill=(200, 200, 200))

    # Copyright
    copy_font = _get_font(12)
    draw.text(
        (right_x, bar_y + 10), "ALCA TIC, S.L. | Sage50BI", font=copy_font, fill=(180, 180, 180)
    )

    # Guardar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  [OK]   {output_path.name} ({output_path.stat().st_size:,} bytes)")
    return True


def generate_default_og(output_path: Path):
    """Genera la imagen OG generica de Sage50BI (sin plantilla especifica)."""
    # Gradiente azul generico
    c_start = (21, 101, 192)
    c_end = (33, 150, 243)

    img = Image.new("RGB", (WIDTH, HEIGHT))
    _draw_gradient(img, c_start, c_end)
    draw = ImageDraw.Draw(img)

    # Overlay
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(0, 0, 0, 50))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Logo central grande
    logo_font = _get_font(64, bold=True)
    logo_text = "Sage50BI"
    bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
    tw = bbox[2] - bbox[0]
    cx = (WIDTH - tw) // 2
    draw.text((cx, 180), logo_text, font=logo_font, fill=(255, 255, 255))

    # Subtitulo
    sub_font = _get_font(28)
    sub_text = "Plantillas SQL Gratuitas"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    tw = bbox[2] - bbox[0]
    cx = (WIDTH - tw) // 2
    draw.text((cx, 270), sub_text, font=sub_font, fill=(220, 220, 220))

    # ALCA TIC
    corp_font = _get_font(22)
    corp_text = "ALCA TIC, S.L."
    bbox = draw.textbbox((0, 0), corp_text, font=corp_font)
    tw = bbox[2] - bbox[0]
    cx = (WIDTH - tw) // 2
    draw.text((cx, 330), corp_text, font=corp_font, fill=(200, 200, 200))

    # URL
    url_font = _get_font(16)
    url_text = "pedironline.com"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    tw = bbox[2] - bbox[0]
    cx = (WIDTH - tw) // 2
    draw.text((cx, 370), url_text, font=url_font, fill=(180, 180, 180))

    # Badge gratuito
    free_font = _get_font(18)
    free_text = "  plantillas gratuitas  "
    bbox = draw.textbbox((0, 0), free_text, font=free_font)
    fw = bbox[2] - bbox[0] + 20
    fh = bbox[3] - bbox[1] + 12
    fx = (WIDTH - fw) // 2
    _draw_rounded_rect(draw, (fx, 420, fx + fw, 420 + fh), 8, (255, 255, 255))
    draw.text((fx + 10, 425), free_text, font=free_font, fill=c_start)

    # Barra inferior
    bar_y = HEIGHT - 50
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=(0, 0, 0, 80))
    copy_font = _get_font(13)
    copy_text = "Catálogo de plantillas SQL y dashboards Streamlit para Sage50BI"
    bbox = draw.textbbox((0, 0), copy_text, font=copy_font)
    tw = bbox[2] - bbox[0]
    cx = (WIDTH - tw) // 2
    draw.text((cx, bar_y + 12), copy_text, font=copy_font, fill=(190, 190, 190))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"  [OK]   {output_path.name} ({output_path.stat().st_size:,} bytes)")


def main():
    print("Generador de Open Graph images para Sage50BI")
    print("=" * 55)

    if not PUBLICAS_DIR.exists():
        print(f"ERROR: No existe el directorio {PUBLICAS_DIR}")
        sys.exit(1)

    # Asegurar directorio de salida
    DOCS_IMG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Directorio de salida: {DOCS_IMG_DIR}")

    # Buscar todas las plantillas
    template_dirs = sorted(
        d for d in PUBLICAS_DIR.iterdir() if d.is_dir() and (d / "template.json").exists()
    )

    if not template_dirs:
        print("No se encontraron plantillas en publicas/")
    else:
        print(f"Encontradas {len(template_dirs)} plantillas\n")

    generated = 0
    skipped = 0

    for td in template_dirs:
        template_json_path = td / "template.json"
        try:
            with open(template_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [SKIP] {td.name}: error leyendo template.json ({e})")
            skipped += 1
            continue

        tid = data.get("id", 0)
        if not tid:
            print(f"  [SKIP] {td.name}: sin ID")
            skipped += 1
            continue

        output_path = DOCS_IMG_DIR / f"og-{tid:04d}.png"
        try:
            generate_og_image(data, output_path)
            generated += 1
        except Exception as e:
            print(f"  [ERR]  {td.name}: {e}")
            skipped += 1

    # Generar OG generico
    print()
    default_path = DOCS_IMG_DIR / "og-default.png"
    try:
        generate_default_og(default_path)
        generated += 1
    except Exception as e:
        print(f"  [ERR]  og-default.png: {e}")

    print(f"\n{'=' * 55}")
    print(f"RESUMEN:")
    print(f"  Generadas: {generated}")
    print(f"  Omitidas/errores: {skipped}")
    print(f"  Total procesadas: {len(template_dirs) + 1}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
