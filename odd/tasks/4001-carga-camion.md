# Publicar plantilla 4001 — Carga de camión (pública genérica)

Empaquetar y publicar la plantilla 4001 "Carga camion" (informe de carga de camión
por familias para albaranes de venta) como plantilla pública genérica del catálogo,
corrigiendo el bug detectado y eliminando la marca del cliente Distrigonza.

## Specs

- S1: "Solo corregir y commitear" incluye corregir el bug latente: `pd.DataFrame(columns=['txt','num'], use_container_width=False, hide_index=True, height=1200)` usa kwargs de `st.dataframe` inválidos para `pd.DataFrame`; con informe filtrado vacío lanza `TypeError`. Tras el fix, con DataFrame vacío debe devolver `pd.DataFrame(columns=['txt','num'])` sin excepción.
- S2: "Publicar como pública genérica" — renombrar `distrigonza.py` → `dashboard.py`, quitar la marca del cliente: "INFORME DISTRIGONZA" → "INFORME CARGA DE CAMIÓN", `informe_distrigonza.txt` → `informe_carga_camion.txt`, `informe_distrigonza.xlsx` → `informe_carga_camion.xlsx`. Sin otras changes de comportamiento.
- S3: El maestro en claro vive en `privado_mantenimiento/4001 - Carga camion/template.sql` (gitignored) y contiene la SELECT extraída de `[SQL] sql = DES: ...` del cuadro INI `distrigonza.sql`, sin las secciones FTP/EMAIL/INFORME ni credenciales (`clavevista = a918336110Z@` jamás se publica).
- S4: `publicas/4001 - Carga camion/template.sql` es el cifrado Fernet público (misma mecánica que las demás plantillas públicas).
- S5: `publicas/4001 - Carga camion/template.json` con id 4001, nombre "Carga de camión", categoría Dashboard y Gráficos (4000-4999), archivos `sql` + `dashboard` (dashboard.py), versión 1.0.0.
- S6: `publicas/4001 - Carga camion/preview.png` generada con la mecánica de previews del proyecto.
- S7: Catálogo regenerado: README.md, docs/, manifest-templates.json, plantillas.csv y manifest-tienda.json incluyen 4001; `distrigonza.sql` original no se publica (se conserva solo en privado_mantenimiento).
- S8: Verificación: `uv run pytest` en fuente (con `UV_PROJECT_ENVIRONMENT=.venvlinux`), verificación de integridad del repo y sanity del cifrado (descifrado round-trip).
- S9: Commits en slices revisables en rama de feature del repo público.

## Tasks

- T1 [S1] bugfix inline: fix `pd.DataFrame` kwargs — RED antes del fix. ✓ commit `72daf17`
- T2 [S2] inline: generalizar naming en dashboard.py. ✓ commit `72daf17`
- T3 [S3] inline: extraer SELECT → maestro privado. ✓ bóveda gitignored, commit `72daf17` (cifrado)
- T4 [S4] pipeline fuente: cifrado Fernet público. ✓ commit `72daf17` — con clave de producción (ver Log L4)
- T5 [S5] pipeline fuente: template.json vía schemas (sql + dashboard). ✓ commit `72daf17`
- T6 [S6] pipeline fuente: preview.png. ✓ commit `72daf17`
- T7 [S7] pipeline fuente: regenerar catálogo. ✓ commit `04a907b`
- T8 [S8] inline: verificación completa. ✓ 233 tests OK, verificar 6/6, hashes válidos
- T9 [S9] inline: commits por slices. ✓ `2c01e25` (chore gitattributes), `72daf17` (feat), `04a907b` (catálogo)

## Log

- L1: "retoma esto" — reanudar la plantilla 4001 - Carga camion de la sesión del 13/10 (bugs ya corregidos: pintar(df=...), filtro fechas, separadores, TXT en Windows, barra exportación).
- L2: Decisión del usuario (ask_user_choice): "Publicar como pública genérica" — renombrar distrigonza → carga de camión, quitar marca del cliente, template.json + SQL cifrado + preview, regenerar catálogo y commitear.
- L3: Hallazgo durante revisión: credencial `clavevista` en `[INFORME]` del cuadro INI — no publicar el INI, solo la SELECT.
- L4: Hallazgo crítico de cifrado: las plantillas publicadas (1000-4000) NO descifran con la clave actual de `mislibrerias/libwertyconfig.py` (ni con el fallback de `cifrado.py`). La clave de producción es la `_FERNET_SEED` de `libwertyconfig.py.old` (misma que compila el `.pyd` desde `pipx/pydobj/.../libwertyconfig.c`). Se re-cifró 4001 con esa clave y se verificó round-trip de las 6 plantillas contra sus maestros.
- L5: Verificación final: pytest fuente 233 passed; `verificar` 6/6 OK; hashes sha256 válidos; maestro dashboard.py compila. Commits en `feat/4001-carga-camion`: `2c01e25`, `72daf17`, `04a907b`. Push y release quedan como decisión del usuario (CSV/manifest-tienda se generan en el release).
- L6: El usuario confirmó que el catálogo AÚN NO está en producción: se descarta la compatibilidad con la clave vieja. `cifrado.py` ahora verifica contra `publicas/*/template.sql` antes de cifrar y aborta si la clave es ajena al catálogo (commit fuente `20b20c5`, 236 tests, pushed). Catálogo completo re-cifrado con la clave ACTUAL de libwertyconfig (7 blobs, round-trip y hashes verificados, guard end-to-end OK). PENDIENTE: recompilar el `.pyd` de Sage50BI con la clave actual o sus builds no descifrarán el catálogo.
