# Informes SSM — plantilla 4006 de actividad comercial (desde fm_barrancos)

Adaptar el app personalizado del cliente Barrancos (`clientes personalizado/fm_barrancos`,
"informes_ssm") como plantilla **pública gratuita** del catálogo, con la lógica protegida
en `.pyd` (núcleo) y una cáscara `.py` visible. Estudio de viabilidad aprobado por el
usuario (2026-11-03).

## Decisiones (usuario)

- D1: Pública gratuita (aparece en el portal como las demás).
- D2: apiforce y cryptutil se AÑADEN al host Sage50BI (instalador/runtime) — cambio en el repo producto.
- D3: Núcleo `.pyd` (bistream/api/lógica/PDF) + cáscara `.py` visible que importa el módulo.
- D4: Datos SOLO del CRM vía apiforce; `template.sql` placeholder.

## Specs

- S1: Cáscara `dashboard.py` con contrato `pintar(df=None, conexion=None, tabla_sql=None)` que ignora el df (placeholder) y delega en `informes_ssm_core` (importable vía sys.path local a la carpeta de la plantilla). Sin `fm_barrancos`/`barranco` en ningún nombre ni texto.
- S2: Si el núcleo no está disponible (pyd no construido aún), la cáscara muestra mensaje claro y no revienta el host.
- S3: Núcleo genérico `informes_ssm_core.py`: carga de actividades por apiforce (`lista('activities')`+`lista('users')`), credenciales en la raíz de datos (no CWD), login por comercial/supervisor (data-driven), filtros, métricas, análisis, gráficos y export CSV/TXT/PDF. Compatible con host: reportlab 5, pandas 3 (dtype str).
- S4: Formato del catálogo: `schemas` admite archivo binario opcional `nucleo` (pyd cifrado) y `descargador` lo descarga si existe; opcional ausente = se omite sin error.
- S5: `template.sql` placeholder SELECT válido (solo-SELECT) documentando que el dato viene del CRM.
- S6: Plantilla 4006 "Informe de actividad comercial" empaquetada en publicas/ con preview y catálogo regenerado (README/docs/manifest/tienda).
- S7: Verificación: verificar 14/14, suite fuente verde, round-trip de los blobs nuevos, 0 URLs muertas, cáscara importable sin núcleo (mensaje) y con núcleo real vía pyd compilado por el usuario en Windows.
- S8: Cambios en el repo producto Sage50BI (deps apiforce/cryptutil) quedan documentados como paso del usuario con instrucciones exactas; compilación del .pyd también (entorno Windows pydobj).

## Tasks

- T1 [S4] Fuente: schemas + descargador para archivo `nucleo` opcional — RED primero.
- T2 [S1,S2,S3] App genérica: núcleo + cáscara (refactor de informe_comercial.py, sin branding).
- T3 [S5,S6] Plantilla 4006 empaquetada + catálogo regenerado.
- T4 [S7] Verificación completa + commits.
- T5 [S8] Instrucciones de build Windows (.pyd) y cambios de host Sage50BI.

## Log

- L1: "estudiar si es viable que esto esté en la pública con toda la lógica que tiene para que aparezca en el portal, pero encriptado en pyd la parte de código; hazme las preguntas que te surgan" — estudio hecho, viable; decisiones D1-D4 del usuario.
- L2: Origen: `clientes personalizado/fm_barrancos` (informe_comercial.py 751 líneas + bistream.py 371, apiforce; sin strings "barranco" en código; branding solo en carpeta/proyecto).
