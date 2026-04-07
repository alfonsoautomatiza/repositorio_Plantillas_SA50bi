# PRD — Repositorio de Plantillas Sage50BI

> **Proyecto**: repositorio_Sage50bi  
> **Fecha**: 2026-04-07  
> **Estado**: Borrador v2 — Con mejoras aprobadas  
> **Autor**: Alfonso Martinez Gonzalez — ALCA TIC, S.L.

---

## 1. Visión General

Crear un repositorio público de plantillas para **Sage50BI** que funcione como **catálogo web visible y posicionable**, fuente de actualización automática desde la aplicación, y escaparate público del proyecto. Incluye:

- **Site MkDocs** como catálogo público con SEO, Open Graph y RSS
- **Catálogo Streamlit** dentro de Sage50BI con búsqueda, preview y recomendaciones
- Sistema de plantillas privadas por cliente con cifrado
- **Packs/Bundles** de plantillas agrupadas
- Tool de gestión visual a prueba de errores humanos
- Auto-generación de texto YouTube para cada plantilla

### Objetivos

| # | Objetivo | Métrica de éxito |
|---|----------|------------------|
| 1 | Catálogo público de plantillas gratuitas con SEO fuerte | README.md indexable por IA y buscadores |
| 2 | Site MkDocs como **catálogo público y escaparate** | Cada plantilla tiene su página con foto, vídeo, descripción, tags, Open Graph |
| 3 | Catálogo Streamlit dentro de Sage50BI | Búsqueda, preview, recomendaciones, instalación con 1 click |
| 4 | Actualización automática desde Sage50BI | Sage50BI lee manifest y descarga sin intervención |
| 5 | Gestión de versiones partial/full | Reutilizar modelo de `libwertyupdate.py` |
| 6 | Plantillas privadas por cliente cifradas | Cliente introduce código → Sage50BI descifra |
| 7 | Tool de gestión visual paso a paso | Un solo botón para publicar sin errores |
| 8 | Cifrado con `libwertyconfig.py` | Reutilizar `FERNET_KEY_COMPILED` existente para públicas, licencia para privadas |
| 9 | Packs/Bundles de plantillas | Agrupaciones temáticas instalables con 1 click |
| 10 | Auto-generación YouTube | Texto SEO-ready para copiar-pegar en YouTube |
| 11 | RSS Feed de novedades | Feed automático indexable por buscadores |

---

## 2. Estructura del Repositorio

```
repositorio_Sage50bi/
│
├── publicas/                              # Plantillas públicas gratuitas
│   ├── 1000 - Listado de clientes ESPAÑA/
│   │   ├── template.json                  # Metadatos de la plantilla
│   │   ├── preview.png                    # Captura de pantalla / imagen
│   │   ├── template.sql                   # SQL con contenido cifrado (Fernet)
│   │   └── dashboard.py                   # Streamlit cifrado (Fernet)
│   ├── 1001 - Balance de situación/
│   │   └── ...
│   └── ...
│
├── privadas/                              # Plantillas privadas por cliente
│   └── CLI-00123/
│       ├── template.json                  # Metadatos (sin info sensible)
│       ├── preview.png
│       ├── template.sql                   # SQL cifrado con clave del cliente
│       └── dashboard.py                   # Streamlit cifrado con clave del cliente
│
├── packs/                                 # Bundles de plantillas
│   ├── pack-contabilidad-completa.json
│   ├── pack-gestion-comercial.json
│   └── ...
│
├── privado_mantenimiento/                 # NO se publica - versiones en claro
│   ├── 1000 - Listado de clientes ESPAÑA/
│   │   ├── template.sql                   # SQL en claro para editar
│   │   └── dashboard.py                   # Streamlit en claro
│   └── CLI-00123/
│       └── ...
│
├── docs/                                  # Fuente MkDocs (catálogo público)
│   ├── index.md                           # Home: presentación + catálogo visual
│   ├── plantillas/                        # Una página por plantilla
│   │   ├── 1000-listado-clientes-espana.md
│   │   └── ...
│   ├── categorias/                        # Páginas de categorías
│   │   ├── informes-listados.md
│   │   └── ...
│   ├── packs/                             # Páginas de packs
│   │   ├── pack-contabilidad-completa.md
│   │   └── ...
│   ├── privadas/                          # Páginas ocultas (NO en nav)
│   │   └── cli-00123.md
│   ├── feed.xml                           # RSS autogenerado
│   └── css/
│       └── extra.css
│
├── gestion/                               # Tool de gestión
│   ├── gestion.py                         # GUI principal PySimpleGUI
│   ├── gestor.py                          # Lógica de negocio
│   ├── cifrado.py                         # Cifrado/descifrado vía libwertyconfig
│   ├── readme_generator.py               # Generador de README.md
│   ├── mkdocs_generator.py               # Generador de docs/ + Open Graph + RSS
│   ├── manifest_generator.py             # Generador de manifest para Sage50BI
│   ├── youtube_generator.py              # Auto-generador de texto YouTube
│   ├── pack_generator.py                 # Gestión de packs/bundles
│   └── version_manager.py               # Gestión de versiones
│
├── README.md                              # Auto-generado - NO editar manualmente
├── manifest-templates.json                # Última versión de cada plantilla (público)
├── mkdocs.yml                             # Config MkDocs
├── requirements.txt                       # Dependencias del tool de gestión
└── PRD.md                                 # Este documento
```

### Reglas de la estructura

- `publicas/` → archivos `.sql` y `.py` con **contenido cifrado** (Fernet). Misma extensión, contenido binario.
- `privado_mantenimiento/` → **NO se sube al repositorio público** (`.gitignore`). Versiones en claro para editar.
- `privadas/` → se publica en el repo pero **no aparece en la navegación MkDocs**. Solo accesible con código.
- `packs/` → JSON con lista de IDs de plantillas + nombre + descripción del pack.
- `README.md` → **100% auto-generado**. Banner de advertencia: no editar manualmente.

### Regla CRÍTICA: Separación SQL vs Vistas

> **Las plantillas contienen SOLO consultas SQL (SELECT). No se usan vistas (CREATE VIEW).**
> 
> Si un usuario intenta mezclar plantillas con vistas que permiten ver el query, 
> el sistema lo BLOQUEA. Las plantillas son para ejecutar informes, no para crear 
> objetos en la base de datos. Esta separación es intencionada y no negociable.

---

## 3. Contenido de una Plantilla

### 3.1 Archivos por tipo

| Archivo | Público (en repo) | Privado (mantenimiento) | Descripción |
|---------|-------------------|------------------------|-------------|
| `template.sql` | `.sql` con contenido cifrado (Fernet) | `.sql` en claro | Consulta SQL principal de la plantilla |
| `dashboard.py` | `.py` con contenido cifrado (Fernet) | `.py` en claro | Cuadro de Streamlit asociado (opcional) |
| `preview.png` | `preview.png` en claro | — | Captura de pantalla para docs |
| `template.json` | `template.json` en claro | — | Metadatos |

> **Nota**: No hay archivos `.txt` en público. El SQL va cifrado dentro del `.sql`. 
> El `.txt` solo existe en `privado_mantenimiento/` como versión en claro para mantenimiento.

### 3.2 Formato de `template.json`

```json
{
  "id": 1000,
  "nombre": "Listado de clientes ESPAÑA",
  "slug": "1000-listado-clientes-espana",
  "version": "1.0.0",
  "categoria": {
    "rango": "1000-1999",
    "nombre": "Informes y Listados",
    "icono": "📋"
  },
  "descripcion": "Listado completo de clientes con filtros por provincia, forma de pago y fecha de alta. Incluye totales agrupados.",
  "descripcion_larga": "Descripción extendida con ejemplos de uso, casos prácticos y notas técnicas para Sage50BI. Generada para que IA y buscadores entiendan el valor de la plantilla.",
  "tags": ["clientes", "listado", "españa", "informes", "sage50"],
  "gratuita": true,
  "tipo": "publica",
  "archivos": {
    "sql": {
      "nombre": "template.sql",
      "cifrado": true,
      "hash_sha256": "abc123..."
    },
    "dashboard": {
      "nombre": "dashboard.py",
      "cifrado": true,
      "hash_sha256": "ghi789...",
      "opcional": true
    }
  },
  "media": {
    "preview": "preview.png",
    "video_youtube": "https://www.youtube.com/watch?v=XXXXXXXXX",
    "video_miniatura": "https://img.youtube.com/vi/XXXXXXXXX/0.jpg"
  },
  "recomendaciones": [1001, 2000],
  "packs": ["pack-gestion-comercial"],
  "sage50bi": {
    "min_version": "1.0.0",
    "compatibilidad": ["sage50bi"]
  },
  "youtube_seo": {
    "titulo": "Listado de clientes ESPAÑA — Plantilla gratuita para Sage50BI",
    "descripcion": "📊 Plantilla gratuita para Sage50BI de ALCA TIC.\n\nListado completo de clientes con filtros por provincia, forma de pago y fecha de alta. Incluye totales agrupados y exportación a Excel.\n\n✅ Gratuita ✅ Actualización automática ✅ Sin registro\n\n🔗 Más plantillas: https://wertymsd.github.io/repositorio_Sage50bi/\n🏢 ALCA TIC: https://pedironline.com",
    "tags_youtube": ["sage50", "sage50bi", "plantillas sql", "listado clientes", "informe contable"]
  },
  "open_graph": {
    "title": "Listado de clientes ESPAÑA — Plantilla gratuita Sage50BI",
    "description": "Listado completo de clientes con filtros por provincia, forma de pago y fecha de alta.",
    "image": "preview.png",
    "type": "article"
  },
  "fecha_creacion": "2026-04-07",
  "fecha_actualizacion": "2026-04-07",
  "changelog": [
    {
      "version": "1.0.0",
      "fecha": "2026-04-07",
      "cambios": "Versión inicial"
    }
  ]
}
```

### 3.3 Formato para plantillas privadas

```json
{
  "id": 42,
  "nombre": "Informe personalizado Ferretería López",
  "slug": "0042-informe-ferreteria-lopez",
  "version": "1.2.0",
  "tipo": "privada",
  "cliente": {
    "codigo": "CLI-00123",
    "clave_hash": "sha256 de la clave de licencia (no la clave en sí)"
  },
  "gratuita": false,
  "...": "... (resto igual que pública, sin youtube_seo ni open_graph)"
}
```

### 3.4 Formato de packs (`packs/pack-xxx.json`)

```json
{
  "id": "pack-gestion-comercial",
  "nombre": "Pack Gestión Comercial",
  "slug": "pack-gestion-comercial",
  "descripcion": "Todo lo que necesitas para gestionar clientes, facturas y albaranes en Sage50BI.",
  "icono": "📦",
  "plantillas": [1000, 1001, 2000, 2001],
  "precio_referencia": "Ahorras instalando el pack completo",
  "preview": "pack-gestion-comercial.png"
}
```

---

## 4. Sistema de Categorías

| Rango | Categoría | Icono | Descripción |
|-------|-----------|-------|-------------|
| 1–999 | Personalizadas | 🔒 | Plantillas privadas por cliente |
| 1000–1999 | Informes y Listados | 📋 | Listados de clientes, proveedores, artículos... |
| 2000–2999 | Facturas y Documentos | 🧾 | Modelos de facturas, albaranes, pedidos... |
| 3000–3999 | Balances y Contabilidad | 📊 | Balances, cuentas de resultados, sumas y saldos... |
| 4000–4999 | Dashboard y Gráficos | 📈 | Cuadros de mando Streamlit, gráficos... |
| 5000–5999 | Reservado futuro | 🔮 | — |

---

## 5. Sistema de Versiones

### 5.1 Modelo (reutiliza `libwertyupdate.py`)

El sistema de versiones funciona a **dos niveles**:

#### Nivel A: Versión del repositorio (global)
- `manifest-templates.json` en la raíz del repo
- Contiene la versión de CADA plantilla disponible + packs
- **Sage50BI lee este archivo** para saber qué plantillas hay y si hay nuevas

```json
{
  "version_manifest": "1.0.0",
  "fecha_generacion": "2026-04-07T12:00:00Z",
  "total_plantillas": 5,
  "total_packs": 2,
  "plantillas": [
    {
      "id": 1000,
      "nombre": "Listado de clientes ESPAÑA",
      "version": "1.0.0",
      "tipo": "publica",
      "categoria": "Informes y Listados",
      "url_base": "https://raw.githubusercontent.com/wertyMSD/repositorio_Sage50bi/main/publicas/1000%20-%20Listado%20de%20clientes%20ESPA%C3%91A/",
      "archivos": {
        "sql": {"nombre": "template.sql", "hash_sha256": "abc123..."},
        "dashboard": {"nombre": "dashboard.py", "hash_sha256": "ghi789...", "opcional": true}
      },
      "preview_url": "...",
      "youtube_url": "...",
      "recomendaciones": [1001, 2000]
    }
  ],
  "packs": [
    {
      "id": "pack-gestion-comercial",
      "nombre": "Pack Gestión Comercial",
      "plantillas": [1000, 1001, 2000, 2001]
    }
  ],
  "clientes_privados": [
    {
      "codigo": "CLI-00123",
      "plantillas": [42, 43]
    }
  ]
}
```

#### Nivel B: Versión por plantilla (individual)
- Cada `template.json` lleva su propio `version` semántico (major.minor.patch)
- Cambio menor (fix SQL) → patch: `1.0.0` → `1.0.1`
- Nuevo feature (nuevo dashboard) → minor: `1.0.0` → `1.1.0`
- Cambio incompatible → major: `1.0.0` → `2.0.0`

### 5.2 Flujo de actualización

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                     SAGE50BI ARRANCA                             │
  │                                                                  │
  │  1. Lee manifest-templates.json (raw.githubusercontent.com)      │
  │  2. Compara con plantillas instaladas localmente                 │
  │  3. Si hay versión nueva → descarga archivos cifrados           │
  │  4. Descifra con cifrador de libwertyconfig (FERNET_KEY)        │
  │  5. Para privadas: usa clave de licencia del cliente             │
  │  6. Instala en carpeta local de plantillas                       │
  └──────────────────────────────────────────────────────────────────┘
```

### 5.3 Cifrado

Se usan **dos mecanismos distintos**:

| Tipo | Mecanismo | Clave | Quién la tiene |
|------|-----------|-------|----------------|
| Pública | `libwertyconfig.cifrador` (Fernet con `FERNET_KEY_COMPILED`) | Embebida en Sage50BI compilado | Todos los usuarios de Sage50BI |
| Privada | Fernet con clave derivada SHA256 de la licencia del cliente | Licencia del cliente | Solo ese cliente |

**La clave pública no es secreto** — su propósito es evitar que alguien copie el SQL directamente del repo y lo use sin Sage50BI. Es una barrera de conveniencia, no de seguridad.

**Las privadas SÍ son seguras** — cada cliente tiene su clave única derivada de su licencia.

---

## 6. README.md Auto-generado

### 6.1 Propósito

README.md es el documento que IA (ChatGPT, Claude, Gemini) y buscadores indexan. Debe contener:

- **Título potente** con keywords (Sage50BI, plantillas gratuitas, SQL, informes)
- **Descripción del repositorio** — qué es, para qué sirve, qué se puede hacer
- **Tabla de todas las plantillas** con número, nombre, versión, descripción corta, tags, enlace YouTube
- **Packs/Bundles** destacados
- **Instrucciones de uso** desde Sage50BI
- **Categorías** explicadas con emoji
- **Badges** (versión, número de plantillas, license)
- **SEO keywords** naturales integradas en el texto

### 6.2 Estructura del README generado

```markdown
# 🏢 Plantillas Gratuitas para Sage50BI — ALCA TIC

[![Plantillas](https://img.shields.io/badge/Plantillas-5-blue)](...)
[![Packs](https://img.shields.io/badge/Packs-2-purple)](...)
[![Versión](https://img.shields.io/badge/Manifest-1.0.0-green)](...)
[![Gratis](https://img.shields.io/badge/Gratuitas-100%25-success)](...)

> ⚠️ **Este archivo se genera automáticamente.** No editar manualmente.
> Para modificar, use el tool de gestión: `python gestion/gestion.py`

## ¿Qué son estas plantillas?

Colección de **plantillas SQL y dashboards Streamlit** gratuitas para
[Sage50BI](https://...). Cada plantilla incluye:

- 📊 Consultas SQL optimizadas para Sage50
- 🐍 Dashboards interactivos con Streamlit
- 🎥 Vídeos explicativos en YouTube
- 🔄 Actualización automática desde la aplicación

## 📦 Packs destacados

| Pack | Plantillas | Descripción |
|------|-----------|-------------|
| 📦 Gestión Comercial | 4 | Clientes, facturas, albaranes... |
| 📦 Contabilidad Completa | 3 | Balances, sumas y saldos... |

## Catálogo de Plantillas

### 📋 Informes y Listados (1000-1999)

| # | Plantilla | Versión | Descripción | Tags | YouTube |
|---|-----------|---------|-------------|------|---------|
| 1000 | Listado de clientes ESPAÑA | 1.0.0 | Listado completo... | `clientes` `listado` | [▶️](...) |

## ¿Cómo usarlas?

1. Instala **Sage50BI** de ALCA TIC
2. Las plantillas se **actualizan automáticamente** al iniciar la aplicación
3. Explora el catálogo desde Sage50BI con búsqueda y recomendaciones
4. ¡Listo!

## Licencia

© 2026 ALCA TIC, S.L. — Plantillas gratuitas para usuarios de Sage50BI.
```

---

## 7. MkDocs — Catálogo Público y Escaparate

### 7.1 Propósito DUAL

El site MkDocs no es solo documentación técnica. Es el **catálogo público** del proyecto:

- **Escaparate visual** con cards de cada plantilla
- **SEO fuerte** — cada página indexable con Open Graph
- **RSS Feed** de novedades para suscriptores y buscadores
- **Catálogo por categorías** navegables
- **Packs destacados** como sección principal

### 7.2 Estructura

```
docs/
├── index.md                              # Home: catálogo visual con cards
├── plantillas/                           # Una página por plantilla
│   ├── 1000-listado-clientes-espana.md
│   └── ...
├── categorias/
│   ├── informes-listados.md              # Listado filtrado por categoría
│   └── ...
├── packs/
│   ├── pack-gestion-comercial.md         # Pack con todas sus plantillas
│   └── ...
├── privadas/
│   └── cli-00123.md                      # Página oculta (NO en nav)
├── feed.xml                              # RSS autogenerado
└── css/
    └── extra.css
```

### 7.3 Página de plantilla (con Open Graph)

```markdown
---
title: Listado de clientes ESPAÑA — Plantilla gratuita Sage50BI
description: Listado completo de clientes con filtros por provincia, forma de pago y fecha de alta.
og_image: preview.png
og_type: article
---

# 📋 1000 - Listado de clientes ESPAÑA

![Preview](../img/1000-preview.png)

## Descripción

Listado completo de clientes con filtros por provincia, forma de pago
y fecha de alta. Incluye totales agrupados.

## Vídeo explicativo

[![Vídeo](https://img.youtube.com/vi/XXXXXXXXX/0.jpg)](https://www.youtube.com/watch?v=XXXXXXXXX)

## Detalles

| Campo | Valor |
|-------|-------|
| Versión | 1.0.0 |
| Categoría | 📋 Informes y Listados |
| Incluye | SQL + Dashboard Streamlit |
| Gratuito | ✅ Sí |
| Actualizado | 2026-04-07 |

## Plantillas relacionadas

| # | Nombre | Categoría |
|---|--------|-----------|
| 1001 | Balance de situación | 📊 Balances |
| 2000 | Modelo factura | 🧾 Facturas |

## Tags

`clientes` `listado` `españa` `informes` `sage50`

## Historial de cambios

### v1.0.0 (2026-04-07)
- Versión inicial
```

### 7.4 Open Graph y Social Cards

Cada página de plantilla incluye meta tags Open Graph autogenerados:

```html
<meta property="og:title" content="Listado de clientes ESPAÑA — Plantilla gratuita Sage50BI">
<meta property="og:description" content="Listado completo de clientes con filtros...">
<meta property="og:image" content="https://...preview.png">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
```

Esto hace que al compartir un link en LinkedIn/Twitter/Slack, se vea una card profesional con imagen, título y descripción.

### 7.5 RSS Feed

El generador MkDocs crea automáticamente `docs/feed.xml` con las últimas plantillas publicadas:

```xml
<rss version="2.0">
  <channel>
    <title>Plantillas Sage50BI — Novedades</title>
    <link>https://wertymsd.github.io/repositorio_Sage50bi/</link>
    <description>Últimas plantillas gratuitas para Sage50BI</description>
    <item>
      <title>1000 - Listado de clientes ESPAÑA</title>
      <link>https://wertymsd.github.io/repositorio_Sage50bi/plantillas/1000-listado-clientes-espana/</link>
      <description>Listado completo de clientes...</description>
      <pubDate>2026-04-07</pubDate>
      <category>Informes y Listados</category>
    </item>
  </channel>
</rss>
```

### 7.6 Plantillas privadas en MkDocs

- Páginas en `docs/privadas/cli-XXXXX.md`
- **NO aparecen en la navegación** (`mkdocs.yml` no las lista en `nav`)
- Solo accesibles si se conoce la URL exacta
- El código del cliente es la parte de la URL → fácil de compartir

### 7.7 Idiomas

- **Español** (principal)
- **Catalán** (traducción)
- Soporte i18n con `mkdocs-static-i18n`

---

## 8. Fichero para Sage50BI (`manifest-templates.json`)

### 8.1 Propósito

Archivo JSON público que Sage50BI descarga al arrancar para saber:
- Qué plantillas públicas hay disponibles
- Qué versión tiene cada una
- Qué packs existen
- Si hay plantillas privadas para el cliente actual
- De dónde descargar los archivos

### 8.2 Ubicación

```
https://raw.githubusercontent.com/wertyMSD/repositorio_Sage50bi/main/manifest-templates.json
```

### 8.3 Formato (ver sección 5.1)

### 8.4 Flujo en Sage50BI

```python
# Pseudocódigo dentro de Sage50BI
def check_template_updates():
    manifest = download("manifest-templates.json")
    local_templates = get_installed_templates()
    
    for template in manifest.plantillas:
        if template.tipo == "publica":
            if template.version > local_version(template.id):
                for archivo in template.archivos:
                    download(archivo)
                decrypt_with_cifrador(archivos)  # libwertyconfig.cifrador
                install(template)
        
        elif template.tipo == "privada":
            if template.cliente_codigo == mi_codigo_cliente:
                if template.version > local_version(template.id):
                    for archivo in template.archivos:
                        download(archivo)
                    decrypt_with_license_key(archivos, mi_licencia)
                    install(template)
```

---

## 9. Sistema de Cifrado

### 9.1 Cifrado de plantillas públicas (reutiliza `libwertyconfig.py`)

```python
# Usando el cifrador existente de libwertyconfig
from libwertyconfig import cifrador  # Fernet(FERNET_KEY_COMPILED)

def cifrar_archivo_publico(input_path, output_path):
    with open(input_path, 'rb') as f_in:
        data = f_in.read()
    encrypted = cifrador.encrypt(data)
    with open(output_path, 'wb') as f_out:
        f_out.write(encrypted)

def descifrar_archivo_publico(input_path, output_path):
    with open(input_path, 'rb') as f_in:
        data = f_in.read()
    decrypted = cifrador.decrypt(data)
    with open(output_path, 'wb') as f_out:
        f_out.write(decrypted)
```

- **Clave**: `FERNET_KEY_COMPILED` ya existe y está embebida en Sage50BI compilado
- **No hay que generar claves nuevas** — se reutiliza toda la infraestructura existente
- **Objetivo**: evitar uso directo sin la app, no seguridad militar

### 9.2 Cifrado de plantillas privadas

```python
# Usando clave derivada de la licencia del cliente
import hashlib, base64
from cryptography.fernet import Fernet

def clave_desde_licencia(licencia_cliente):
    """Deriva una clave Fernet desde la licencia del cliente."""
    digest = hashlib.sha256(licencia_cliente.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def cifrar_privado(input_path, output_path, licencia_cliente):
    key = clave_desde_licencia(licencia_cliente)
    f = Fernet(key)
    with open(input_path, 'rb') as f_in:
        data = f_in.read()
    encrypted = f.encrypt(data)
    with open(output_path, 'wb') as f_out:
        f_out.write(encrypted)
```

- **Cada cliente tiene su clave única** derivada de su licencia
- El `template.json` privado guarda un **hash** de la clave (para verificación), nunca la clave en sí

---

## 10. Catálogo Streamlit dentro de Sage50BI

### 10.1 Marketplace interno

Sage50BI ya tiene Streamlit integrado. Se añade una sección **Catálogo de Plantillas** que:

1. Lee el manifest remoto
2. Muestra cards de cada plantilla con preview, descripción y tags
3. Búsqueda por nombre y tags
4. Filtro por categoría
5. Recomendaciones cruzadas
6. Packs instalables con 1 click
7. Estado de cada plantilla (instalada / actualizable / nueva)

### 10.2 Sistema de Recomendaciones

Las recomendaciones funcionan a dos niveles:

#### A. Recomendaciones manuales (definidas en template.json)

Cada plantilla tiene un campo `recomendaciones` con IDs de plantillas relacionadas:

```json
"recomendaciones": [1001, 2000]
```

El tool de gestión permite configurar estas relaciones visualmente.

#### B. Recomendaciones automáticas por tags

El catálogo Streamlit cruza los tags de la plantilla actual con todas las demás:

```python
def recomendar_por_tags(plantilla_actual, todas_plantillas, max_resultados=3):
    tags_actual = set(plantilla_actual["tags"])
    puntuaciones = []
    for p in todas_plantillas:
        if p["id"] == plantilla_actual["id"]:
            continue
        tags_p = set(p["tags"])
        coincidencias = len(tags_actual & tags_p)
        if coincidencias > 0:
            puntuaciones.append((coincidencias, p))
    puntuaciones.sort(reverse=True)
    return [p for _, p in puntuaciones[:max_resultados]]
```

### 10.3 Pantalla del Catálogo Streamlit

```
┌─────────────────────────────────────────────────────────────┐
│  🏪 CATÁLOGO DE PLANTILLAS SAGE50BI                         │
│                                                              │
│  🔍 [Buscar plantillas...               ] [📋] [📊] [🧾]  │
│                                                              │
│  ┌─ 📦 PACKS ────────────────────────────────────────────┐  │
│  │ 📦 Gestión Comercial (4 plantillas)  [INSTALAR TODO]  │  │
│  │ 📦 Contabilidad Completa (3)         [INSTALAR TODO]  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ 🆕 NOVEDADES ────────────────────────────────────────┐  │
│  │                                                        │  │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │ │  🖼️      │  │  🖼️      │  │  🖼️      │             │  │
│  │ │ 1000     │  │ 1001     │  │ 2000     │             │  │
│  │ │ Clientes │  │ Balance  │  │ Factura  │             │  │
│  │ │ ESPAÑA   │  │ situación│  │ modelo   │             │  │
│  │ │          │  │          │  │          │             │  │
│  │ │ [▶️] [📥]│  │ [▶️] [📥]│  │ [▶️] [📥]│             │  │
│  │ └──────────┘  └──────────┘  └──────────┘             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ 🔒 MIS PLANTILLAS PRIVADAS ──────────────────────────┐  │
│  │ 🔒 42 - Informe Ferretería López v1.2    [ACTUALIZAR] │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  📡 Última actualización: 2026-04-07 | 5 plantillas        │
└─────────────────────────────────────────────────────────────┘
```

### 10.4 Vista de detalle con recomendaciones

```
┌─────────────────────────────────────────────────────────────┐
│  ← Volver al catálogo                                       │
│                                                              │
│  📋 1000 - Listado de clientes ESPAÑA                       │
│                                                              │
│  ┌─────────────────────────────┐  Versión: 1.0.0            │
│  │                             │  Categoría: Informes       │
│  │     [PREVIEW GRANDE]        │  Tags: clientes, listado   │
│  │                             │  Gratuito: ✅               │
│  └─────────────────────────────┘                             │
│                                                              │
│  Listado completo de clientes con filtros por provincia,    │
│  forma de pago y fecha de alta. Incluye totales agrupados.  │
│                                                              │
│  [▶️ Ver en YouTube]  [📥 INSTALAR]  [✅ INSTALADA v1.0.0]  │
│                                                              │
│  ┌─ 👥 QUIEN VIO ESTO TAMBIÉN VIO... ────────────────────┐  │
│  │                                                        │  │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │ │ 1001     │  │ 2000     │  │ 3000     │             │  │
│  │ │ Balance  │  │ Factura  │  │ Sumas y  │             │  │
│  │ │ situación│  │ modelo   │  │ saldos   │             │  │
│  │ └──────────┘  └──────────┘  └──────────┘             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Auto-generación YouTube

### 11.1 Propósito

Cada plantilla puede generar un texto listo para copiar-pegar en YouTube, optimizado para SEO.

### 11.2 Formato generado

El tool de gestión genera este texto a partir del `template.json`:

```
━━━ COPIAR EN YOUTUBE ━━━

TÍTULO: Listado de clientes ESPAÑA — Plantilla gratuita para Sage50BI

DESCRIPCIÓN:
📊 Plantilla gratuita para Sage50BI de ALCA TIC.

Listado completo de clientes con filtros por provincia, forma de pago
y fecha de alta. Incluye totales agrupados y exportación a Excel.

✅ Gratuita ✅ Actualización automática ✅ Sin registro

🔗 Más plantillas: https://wertymsd.github.io/repositorio_Sage50bi/
🔗 RSS Novedades: https://wertymsd.github.io/repositorio_Sage50bi/feed.xml
🏢 ALCA TIC: https://pedironline.com

#sage50 #sage50bi #plantillas #sql #informes #contabilidad #españa

TAGS: sage50, sage50bi, plantillas sql, listado clientes, informe contable
━━━━━━━━━━━━━━━━━━━━━━━━
```

### 11.3 En el tool de gestión

Paso adicional en el wizard de nueva plantilla: se muestra el texto generado y un botón **📋 COPIAR AL PORTAPAPELES**. También accesible desde el menú de plantilla existente.

---

## 12. Tool de Gestión Visual (PySimpleGUI)

### 12.1 Pantalla principal

```
┌──────────────────────────────────────────────────────────────┐
│            🏢 GESTIÓN DE PLANTILLAS SAGE50BI                  │
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 🆕 NUEVA │ │ 🔄 ACTUAL.│ │ 🔒 PRIVADA│ │ 📦 PACK  │        │
│  │ PLANTILLA│ │ PLANTILLA │ │ CLIENTE  │ │ /BUNDLE  │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 📋 REGEN.│ │ 🚀 PUBLI-│ │ 🎥 YOU-  │ │ ⚙️ CONFIG │        │
│  │ DOCS     │ │   CAR    │ │ TUBE TXT │ │          │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                                │
│  ─────────────────────────────────────────────────            │
│  Plantillas: 5 públicas | 3 privadas | Packs: 2              │
│  Manifest: v1.0.0 | Última publicación: 2026-04-07          │
└──────────────────────────────────────────────────────────────┘
```

### 12.2 Flujo: Nueva Plantilla Pública

```
PASO 1/7 → Datos básicos
┌──────────────────────────────────────────────────────────────┐
│  🆕 NUEVA PLANTILLA PÚBLICA                                   │
│                                                                │
│  Número:     [1000        ] ← Auto-sugerido siguiente libre   │
│  Nombre:     [Listado de clientes ESPAÑA                    ] │
│  Categoría:  [Informes y Listados ▼]  (auto por número)      │
│  Descripción:[Listado completo de clientes con filtros...   ] │
│  Tags:       [clientes, listado, españa, sage50            ] │
│                                                                │
│  Recomendaciones (IDs): [1001, 2000                          ] │
│                                                                │
│                              [CANCELAR] [SIGUIENTE →]         │
└──────────────────────────────────────────────────────────────┘

PASO 2/7 → Archivos
┌──────────────────────────────────────────────────────────────┐
│  📁 ARCHIVOS DE LA PLANTILLA                                  │
│                                                                │
│  SQL principal:   [/path/to/template.sql        ] [BUSCAR]   │
│  Dashboard (.py): [/path/to/dashboard.py        ] [BUSCAR]   │
│              (opcional)                                        │
│                                                                │
│  ✅ Los archivos se copiarán a privado_mantenimiento/          │
│  ⚠️ Solo SELECT — se validará que no haya CREATE VIEW/ALTER   │
│                                                                │
│                    [← ANTERIOR] [CANCELAR] [SIGUIENTE →]     │
└──────────────────────────────────────────────────────────────┘

PASO 3/7 → Multimedia
┌──────────────────────────────────────────────────────────────┐
│  🎥 MULTIMEDIA                                                │
│                                                                │
│  Preview (PNG):   [/path/to/preview.png         ] [BUSCAR]   │
│  YouTube URL:     [https://youtube.com/watch?v=XXX         ] │
│                                                                │
│  Vista previa:                                                 │
│  ┌─────────────────────────────┐                              │
│  │     [IMAGEN PREVIEW]        │                              │
│  └─────────────────────────────┘                              │
│                                                                │
│                    [← ANTERIOR] [CANCELAR] [SIGUIENTE →]     │
└──────────────────────────────────────────────────────────────┘

PASO 4/7 → Packs (opcional)
┌──────────────────────────────────────────────────────────────┐
│  📦 ASIGNAR A PACKS                                           │
│                                                                │
│  ☑️ Pack Gestión Comercial (4 plantillas)                     │
│  ☐ Pack Contabilidad Completa (3 plantillas)                  │
│  ☐ Crear pack nuevo...                                        │
│                                                                │
│                    [← ANTERIOR] [CANCELAR] [SIGUIENTE →]     │
└──────────────────────────────────────────────────────────────┘

PASO 5/7 → YouTube SEO (auto-generado)
┌──────────────────────────────────────────────────────────────┐
│  🎥 TEXTO YOUTUBE (auto-generado)                             │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ TÍTULO: Listado de clientes ESPAÑA — Plantilla...       ││
│  │                                                          ││
│  │ DESCRIPCIÓN:                                             ││
│  │ 📊 Plantilla gratuita para Sage50BI de ALCA TIC...      ││
│  │                                                          ││
│  │ TAGS: sage50, sage50bi, plantillas sql...               ││
│  └──────────────────────────────────────────────────────────┘│
│                                                                │
│  [📋 COPIAR AL PORTAPAPELES]  [✏️ EDITAR MANUALMENTE]       │
│                                                                │
│                    [← ANTERIOR] [CANCELAR] [SIGUIENTE →]     │
└──────────────────────────────────────────────────────────────┘

PASO 6/7 → Confirmación
┌──────────────────────────────────────────────────────────────┐
│  ✅ CONFIRMAR NUEVA PLANTILLA                                 │
│                                                                │
│  Se creará:                                                    │
│  • publicas/1000 - Listado de clientes ESPAÑA/               │
│  • privado_mantenimiento/1000 - Listado de clientes ESPAÑA/  │
│  • docs/plantillas/1000-listado-clientes-espana.md            │
│                                                                │
│  Archivos:                                                     │
│  • template.sql (contenido cifrado con libwertyconfig)        │
│  • dashboard.py (contenido cifrado con libwertyconfig)        │
│  • preview.png                                                 │
│  • template.json                                               │
│                                                                │
│  Open Graph: ✅  YouTube: ✅  RSS: ✅                         │
│  Pack: Gestión Comercial  Recomendaciones: 1001, 2000        │
│  Versión inicial: 1.0.0                                        │
│                                                                │
│                    [← ANTERIOR] [CANCELAR] [✅ CREAR]         │
└──────────────────────────────────────────────────────────────┘

PASO 7/7 → Ejecución + Resultado
┌──────────────────────────────────────────────────────────────┐
│  ⏳ EJECUTANDO...                                             │
│                                                                │
│  ✅ Carpeta creada en privado_mantenimiento/                   │
│  ✅ SQL validado (solo SELECT)                                 │
│  ✅ Archivos copiados (sin cifrar)                             │
│  ✅ Archivos cifrados con libwertyconfig.cifrador              │
│  ✅ template.json generado                                     │
│  ✅ preview.png copiado                                        │
│  ✅ README.md actualizado                                      │
│  ✅ docs MkDocs regenerado (página + Open Graph)               │
│  ✅ RSS feed actualizado                                       │
│  ✅ manifest-templates.json actualizado                        │
│  ✅ Pack actualizado                                           │
│                                                                │
│  ████████████████████████████████████ 100%                    │
│                                                                │
│  ✅ ¡PLANTILLA CREADA CON ÉXITO!                              │
│                                                                │
│  [ABRIR CARPETA] [PUBLICAR AHORA] [CERRAR]                   │
└──────────────────────────────────────────────────────────────┘
```

### 12.3 Flujo: Crear/Editar Pack

```
PASO 1/3 → Datos del pack
┌──────────────────────────────────────────────────────────────┐
│  📦 NUEVO PACK DE PLANTILLAS                                  │
│                                                                │
│  ID:           [pack-gestion-comercial                       ] │
│  Nombre:       [Pack Gestión Comercial                       ] │
│  Descripción:  [Todo para gestionar clientes y facturas...  ] │
│  Icono:        [📦 ▼]                                         │
│                                                                │
│  Plantillas incluidas:                                         │
│  ☑️ 1000 - Listado de clientes ESPAÑA                         │
│  ☑️ 1001 - Balance de situación                               │
│  ☑️ 2000 - Modelo factura                                     │
│  ☐ 2001 - Albarán                                            │
│                                                                │
│                    [CANCELAR] [SIGUIENTE →]                   │
└──────────────────────────────────────────────────────────────┘
```

### 12.4 Flujo: Regenerar Documentación

```
┌──────────────────────────────────────────────────────────────┐
│  📋 REGENERAR DOCUMENTACIÓN                                   │
│                                                                │
│  ☑️ README.md                                                  │
│  ☑️ MkDocs (docs/ + Open Graph)                                │
│  ☑️ RSS feed (feed.xml)                                        │
│  ☑️ manifest-templates.json                                    │
│  ☑️ mkdocs.yml                                                 │
│                                                                │
│  Se regenerarán todos los archivos a partir de los            │
│  template.json de cada plantilla.                             │
│                                                                │
│                    [CANCELAR] [🔄 REGENERAR]                  │
└──────────────────────────────────────────────────────────────┘
```

### 12.5 Flujo: Publicar

```
┌──────────────────────────────────────────────────────────────┐
│  🚀 PUBLICAR EN GITHUB                                        │
│                                                                │
│  Cambios pendientes:                                           │
│  • + publicas/1000 - Listado de clientes ESPAÑA/              │
│  • + packs/pack-gestion-comercial.json                         │
│  • ~ README.md (modificado)                                    │
│  • ~ manifest-templates.json (modificado)                      │
│  • + docs/plantillas/1000-listado-clientes-espana.md           │
│  • ~ docs/feed.xml (actualizado)                               │
│                                                                │
│  Commit message:                                               │
│  [feat: añadir plantilla 1000 + pack gestión comercial      ] │
│                                                                │
│  ⚠️ privado_mantenimiento/ está en .gitignore (no se sube)    │
│                                                                │
│                    [CANCELAR] [🚀 PUBLICAR]                   │
└──────────────────────────────────────────────────────────────┘
```

### 12.6 Flujo: Plantilla Privada de Cliente

```
PASO 1/5 → Datos del cliente
┌──────────────────────────────────────────────────────────────┐
│  🔒 NUEVA PLANTILLA PRIVADA                                   │
│                                                                │
│  Código cliente: [CLI-00123   ]                               │
│  Clave licencia: [••••••••••• ] ← Para cifrar                 │
│                                                                │
│  ¿Partir de plantilla pública? [SÍ ▼]                         │
│  Plantilla base: [1000 - Listado de clientes ESPAÑA ▼]       │
│                                                                │
│  Nombre:        [Informe personalizado Ferretería López     ] │
│  Descripción:   [Adaptación del listado con filtros...      ] │
│                                                                │
│                    [CANCELAR] [SIGUIENTE →]                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 13. Módulos del Tool de Gestión

| Módulo | Archivo | Responsabilidad |
|--------|---------|----------------|
| GUI | `gestion/gestion.py` | Interfaz PySimpleGUI, wizard paso a paso |
| Lógica | `gestion/gestor.py` | Orquestación de operaciones, validación |
| Cifrado | `gestion/cifrado.py` | Cifrar/descifrar vía `libwertyconfig.cifrador` |
| README | `gestion/readme_generator.py` | Generar README.md desde template.json |
| MkDocs | `gestion/mkdocs_generator.py` | Generar docs/ + Open Graph + RSS |
| Manifest | `gestion/manifest_generator.py` | Generar manifest-templates.json |
| Versiones | `gestion/version_manager.py` | Bump version, changelog, comparar |
| YouTube | `gestion/youtube_generator.py` | Auto-generar texto SEO YouTube |
| Packs | `gestion/pack_generator.py` | Crear/editar packs de plantillas |

---

## 14. Dependencias

```
# requirements.txt
PySimpleGUI>=5.0
cryptography>=42.0
Jinja2>=3.1
mkdocs>=1.5
mkdocs-material>=9.5
mkdocs-static-i18n>=1.2
mkdocs-rss-plugin>=1.0
packaging>=24.0
Pillow>=10.0
pyperclip>=1.9
```

---

## 15. Consideraciones Técnicas

### 15.1 `.gitignore`

```gitignore
# Versiones en claro (NUNCA se publican)
privado_mantenimiento/

# Python
__pycache__/
*.pyc
*.pyd
.env

# OS
.DS_Store
Thumbs.db

# Temporales
temp/
*.tmp
```

### 15.2 Validaciones del tool de gestión

El tool valida en cada paso:
- **Número de plantilla**: rango válido, no duplicado
- **Archivos obligatorios**: al menos `template.sql` debe existir
- **SQL solo SELECT**: validar que no haya `CREATE VIEW`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, `DELETE`
- **Nombre de carpeta**: formato correcto `NNNN - Nombre`
- **YouTube URL**: formato válido si se proporciona
- **preview.png**: existe y es imagen válida
- **Código de cliente**: formato `CLI-XXXXX` para privadas
- **Clave de licencia**: no vacía para privadas
- **Cifrado**: verificar que cifrado → descifrado → original es idéntico
- **Pack**: al menos 2 plantillas para crear un pack
- **Recomendaciones**: IDs existen y son de plantillas públicas

### 15.3 Idempotencia

Todas las operaciones de generación (README, MkDocs, manifest, RSS) son **idempotentes**:
- Se pueden ejecutar N veces sin efectos secundarios
- Siempre regeneran desde los `template.json` actuales
- Nunca pierden datos si se interrumpe

---

## 16. Plan de Implementación (Fases)

### Fase 1: Estructura base
- [ ] Crear estructura de carpetas del repositorio
- [ ] `.gitignore` con `privado_mantenimiento/`
- [ ] `template.json` schema y validación
- [ ] Módulo de cifrado (`cifrado.py`) reutilizando `libwertyconfig.cifrador`
- [ ] Validación SQL (solo SELECT)

### Fase 2: Tool de gestión - Núcleo
- [ ] `version_manager.py` — gestión de versiones
- [ ] `gestor.py` — lógica de crear/actualizar plantillas
- [ ] `gestion.py` — GUI wizard con PySimpleGUI
- [ ] `youtube_generator.py` — auto-generación texto YouTube
- [ ] `pack_generator.py` — gestión de packs

### Fase 3: Generadores
- [ ] `readme_generator.py` — README.md auto-generado con SEO
- [ ] `mkdocs_generator.py` — docs/ completo + Open Graph meta tags
- [ ] `manifest_generator.py` — manifest-templates.json
- [ ] RSS feed auto-generado

### Fase 4: MkDocs
- [ ] `mkdocs.yml` con tema Material
- [ ] Soporte ES/CA
- [ ] Páginas de categorías
- [ ] Páginas de plantillas (públicas y privadas ocultas)
- [ ] Páginas de packs
- [ ] Open Graph en cada página
- [ ] RSS feed

### Fase 5: Catálogo Streamlit en Sage50BI
- [ ] Componente catálogo que lee manifest remoto
- [ ] Cards con preview, descripción y tags
- [ ] Búsqueda por nombre y tags
- [ ] Filtro por categoría
- [ ] Sistema de recomendaciones (manual + automático por tags)
- [ ] Instalación de plantillas con 1 click
- [ ] Instalación de packs completos

### Fase 6: Integración Sage50BI (actualización)
- [ ] Lector de `manifest-templates.json` en Sage50BI
- [ ] Descarga + descifrado de plantillas públicas
- [ ] Descarga + descifrado de plantillas privadas con licencia
- [ ] Instalación local de plantillas

### Fase 7: Publicación inicial
- [ ] Crear primeras 3-5 plantillas de ejemplo
- [ ] Crear 1-2 packs de ejemplo
- [ ] Publicar en GitHub
- [ ] Configurar GitHub Pages para MkDocs
- [ ] Probar flujo completo end-to-end

### Fase 8 (futuro): Auto-preview
- [ ] Ejecutar SQL contra BD de test y capturar resultado como imagen
- [ ] Generación automática de preview.png

---

## 17. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Alguien descifra plantillas públicas | Bajo — son gratuitas de todos modos | Cifrado es barrera de conveniencia, no de seguridad |
| Clave de cliente se pierde | Alto — plantilla irrecuperable | Backup en claro en `privado_mantenimiento/` (no se publica) |
| README.md editado manualmente | Medio — se pierde en regeneración | Banner visible de advertencia + validación |
| Sage50BI no puede leer manifest | Alto — plantillas no se actualizan | URL fallback + cache local + logging |
| Carpeta privado_mantenimiento se sube por error | Crítico — código en claro público | `.gitignore` + validación pre-commit + check en tool |
| SQL con CREATE VIEW se cuela | Alto — mezcla plantillas con vistas | Validación estricta en tool de gestión + test en Sage50BI |

---

## 18. Decisiones Tomadas

| # | Decisión | Resultado |
|---|----------|-----------|
| 1 | ¿Dependencias entre plantillas? | ❌ NO — no se usan vistas en los cuadros. Sistema bloquea si usuario mezcla |
| 2 | ¿Deprecación/compatibilidad Sage50? | ❌ NO — Sage50 siempre actualizado a última versión |
| 3 | ¿Open Graph + Social Cards? | ✅ SÍ — meta tags autogenerados en cada página |
| 4 | ¿Auto-generación YouTube? | ✅ SÍ — texto SEO-ready copiable |
| 5 | ¿Packs/Bundles? | ✅ SÍ — packs temáticos instalables con 1 click |
| 6 | ¿RSS Feed? | ✅ SÍ — feed de novedades indexable |
| 7 | ¿Auto-preview SQL? | ⏳ FASE 2 — ejecución contra BD test |
| 8 | ¿Catálogo dentro de Sage50BI? | ✅ SÍ — en Streamlit con recomendaciones |
| 9 | ¿Cifrado público? | ✅ Reutilizar `libwertyconfig.cifrador` (Fernet con `FERNET_KEY_COMPILED`) |
| 10 | ¿Archivos en público? | ✅ `.sql` y `.py` con contenido cifrado (misma extensión, contenido Fernet) |
| 11 | ¿Idiomas? | ✅ Español + Catalán |

---

## 19. Pendientes de Decisión

| # | Pregunta | Opciones | Recomendación |
|---|----------|----------|---------------|
| 1 | ¿GitHub del repo? | `wertyMSD/repositorio_Sage50bi` | Confirmar |
| 2 | ¿GitHub Pages para MkDocs? | Sí / No | Sí — `wertymsd.github.io/repositorio_Sage50bi/` |
| 3 | ¿Las privadas llevan preview.png? | Sí / No | Sí — pero sin info sensible |
| 4 | ¿Cuántas plantillas iniciales? | 3 / 5 / 10 | 3-5 para validar el flujo |
| 5 | ¿El catálogo Streamlit es una página nueva dentro de Sage50BI? | Sí / Integrar en menú existente | Nueva página dedicada |
