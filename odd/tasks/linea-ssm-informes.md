# Línea SSM — informes BI de s50info como plantillas de catálogo

Crear una línea de 7 informes públicos a partir de las `BI_QUERIES` de
s50info (`s50script.py`), cada uno con SQL validado + dashboard genérico
(tabla + filtros de fecha + exportación TXT/Excel). El usuario los afinará
uno a uno después. Fuera de alcance: el informe personalizado de Barrasco
(el usuario indicará su ubicación; se adaptará quitando los nombres del
cliente) y la 4001 ya publicada.

## Specs

- S1: Los 7 informes salen de `BI_QUERIES` de `s50info/s50script.py` (fuente canónica de las SELECT), excluyendo `Carga_Reparto_por_cliente` (duplica la 4001 ya publicada).
- S2: Cada plantilla: template.sql con la SELECT del sample + cabecera de comentario, validada solo-SELECT por el pipeline; dashboard.py genérico derivado del de la 4001 con `TITULO` y `NOMBRE_ARCHIVO` por informe.
- S3: IDs por rango de categoría: informes de deuda/cuotas en 1000-1999 (1002-1004); análisis de ventas/carga en 4000-4999 (4002-4005). Sin colisiones (el pipeline aborta si el ID existe).
- S4: Nombres/descripciones/tags por informe (base: titulo/descripcion de BIQuery, español profesional).
- S5: preview.png para las 7 (generate_previews). Catálogo regenerado: README, docs ES/CA, manifest-templates.json; artefactos de tienda regenerados con los generadores (CSV/manifest-tienda/release-notes) con las URLs canónicas.
- S6: Verificación: verificar 13/13 plantillas OK, suite fuente verde, round-trip cripto de los 14 blobs contra maestros, 0 URLs muertas.
- S7: Commits locales en el público sobre feat/4001-carga-camion; fuente sin cambios de código (maestros van a privado_mantenimiento, gitignored).
- S8: Los hardcodes de cliente detectados se conservan tal cual (EMPRESA='01', [lotes0JP]) y se listan para el afinado uno a uno del usuario.

## Tasks

- T1 [S1,S8] Extraer y pre-validar las 7 SELECT desde BI_QUERIES.
- T2 [S2] Dashboard genérico base + 7 variantes con título/nombre por informe.
- T3 [S3,S4] Crear las 7 plantillas con el pipeline (crear_plantilla_publica).
- T4 [S5] Previews + regenerar catálogo + artefactos de tienda.
- T5 [S6] Verificación completa (verificar, suite, round-trip, URLs).
- T6 [S7] Commits locales en el público + reporte con la lista para afinar.

## Log

- L1: "en s50info tenemos un script y query para las plantillas usas esos informes a crear más contenidos luego los afino uno a uno" — instrucción original.
- L2: "crea una línea de informes de SSM y adapta el que tenemos personalizado para Barrasco; obvio que quites los nombres de Barranco" — la línea SSM = los BI_QUERIES; el de Barrasco está en otro sitio (pendiente ubicación) y se adaptará quitando los nombres del cliente.
- L3: Formato elegido por el usuario: SQL + dashboard genérico para cada informe.
- L4: Hallazgo durante smoke: en pandas 3 las columnas de texto son dtype `str` (no `object`) y `obtener_columnas_fecha` las ignoraba (el filtro de fechas desaparecía). Corregido en las 7 variantes Y en el maestro de la 4001 (código compartido), con re-cifrado y hash nuevo de 4001.
- L5: Resultado: 7 plantillas creadas (1002-1004, 4002-4005), 13 previews, catálogo y tienda a 13, verificar 13/13, round-trip 13/13, 246 tests, 0 URLs muertas. Hardcodes pendientes de afinado por informe: EMPRESA='01' (1002, 1004, 4003), BD [lotes0JP] (4004). Commits públicos locales en feat/4001-carga-camion.
