"""
Script de inicializacion: crea 5 plantillas de ejemplo + 2 packs + regenera docs.
Uso: python scripts/create_samples.py
"""

import sys
from pathlib import Path
import tempfile
import shutil

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from gestion.gestor import Gestor
from gestion.pack_generator import crear_pack, guardar_pack, listar_packs
from gestion.readme_generator import generar_y_guardar_readme
from gestion.mkdocs_generator import generar_todo
from gestion.manifest_generator import generar_y_guardar_manifest

# === SQL TEMPLATES ===

SQL_TEMPLATES = {
    1000: {
        "nombre": "Listado de clientes ESPAÑA",
        "descripcion": "Listado completo de clientes con filtros por provincia, forma de pago y fecha de alta. Incluye totales agrupados.",
        "tags": ["clientes", "listado", "españa", "informes", "sage50"],
        "sql": """-- Listado de clientes de España
-- Plantilla 1000 - Informes y Listados
SELECT 
    c.codigo_cliente,
    c.nombre_fiscal,
    c.cif_nif,
    c.direccion,
    c.poblacion,
    c.provincia,
    c.codigo_postal,
    fp.descripcion AS forma_pago,
    c.fecha_alta,
    c.telefono,
    c.email
FROM clientes c
LEFT JOIN formas_pago fp ON c.codigo_forma_pago = fp.codigo
WHERE c.pais = 'ES'
ORDER BY c.provincia, c.nombre_fiscal""",
    },
    1001: {
        "nombre": "Listado de proveedores por provincia",
        "descripcion": "Listado agrupado de proveedores por provincia con totales de facturación y estadísticas de compra.",
        "tags": ["proveedores", "listado", "provincia", "informes", "compras"],
        "sql": """-- Listado de proveedores por provincia
-- Plantilla 1001 - Informes y Listados
SELECT 
    p.codigo_proveedor,
    p.nombre_fiscal,
    p.cif_nif,
    p.provincia,
    p.poblacion,
    COUNT(f.numero) AS total_facturas,
    COALESCE(SUM(f.total_euros), 0) AS total_facturado,
    COALESCE(AVG(f.total_euros), 0) AS media_factura
FROM proveedores p
LEFT JOIN facturas_compra f ON p.codigo_proveedor = f.codigo_proveedor
WHERE p.pais = 'ES'
GROUP BY p.codigo_proveedor, p.nombre_fiscal, p.cif_nif, p.provincia, p.poblacion
ORDER BY p.provincia, p.nombre_fiscal""",
    },
    2000: {
        "nombre": "Modelo de factura con totales",
        "descripcion": "Modelo de factura profesional con desglose de líneas, IVA, retenciones y totales. Formato optimizado para impresión.",
        "tags": ["factura", "modelo", "totales", "iva", "documentos"],
        "sql": """-- Modelo de factura con totales
-- Plantilla 2000 - Facturas y Documentos
SELECT 
    f.numero AS numero_factura,
    f.fecha,
    f.codigo_cliente,
    c.nombre_fiscal AS cliente,
    c.cif_nif,
    c.direccion,
    lf.descripcion AS concepto,
    lf.cantidad,
    lf.precio_unitario,
    lf.descuento_porcentaje,
    lf.total_euros AS importe_linea,
    lf.porcentaje_iva,
    lf.total_euros * lf.porcentaje_iva / 100 AS importe_iva,
    lf.total_euros * (1 + lf.porcentaje_iva / 100) AS total_con_iva
FROM facturas_venta f
JOIN clientes c ON f.codigo_cliente = c.codigo_cliente
JOIN lineas_factura_venta lf ON f.numero = lf.numero_factura
WHERE YEAR(f.fecha) = YEAR(GETDATE())
ORDER BY f.fecha DESC, f.numero""",
    },
    3000: {
        "nombre": "Balance de situación",
        "descripcion": "Balance de situación con desglose por cuentas, grupos y subgrupos. Incluye totales de activo, pasivo y patrimonio neto.",
        "tags": ["balance", "situacion", "contabilidad", "cuentas", "activo", "pasivo"],
        "sql": """-- Balance de situación
-- Plantilla 3000 - Balances y Contabilidad
SELECT 
    pc.codigo_grupo,
    pc.descripcion AS grupo,
    sc.codigo_subgrupo,
    sc.descripcion AS subgrupo,
    c.codigo_cuenta,
    c.descripcion AS cuenta,
    s.total_debe,
    s.total_haber,
    s.total_debe - s.total_haber AS saldo,
    CASE 
        WHEN c.codigo_cuenta LIKE '1%' THEN 'ACTIVO'
        WHEN c.codigo_cuenta LIKE '2%' THEN 'PASIVO'
        WHEN c.codigo_cuenta LIKE '3%' THEN 'PATRIMONIO NETO'
        ELSE 'OTRO'
    END AS naturaleza
FROM cuentas c
JOIN subgrupos_cuentas sc ON c.codigo_subgrupo = sc.codigo_subgrupo
JOIN grupos_cuentas pc ON sc.codigo_grupo = pc.codigo_grupo
LEFT JOIN saldos_cuentas s ON c.codigo_cuenta = s.codigo_cuenta
WHERE s.ejercicio = YEAR(GETDATE())
ORDER BY pc.codigo_grupo, sc.codigo_subgrupo, c.codigo_cuenta""",
    },
    4000: {
        "nombre": "Dashboard de ventas por cliente",
        "descripcion": "Cuadro de mando interactivo con Streamlit mostrando ventas por cliente, evolución mensual y top 10 clientes. Incluye gráficos de barras y líneas.",
        "tags": ["dashboard", "ventas", "grafico", "streamlit", "cliente"],
        "sql": """-- Dashboard de ventas por cliente
-- Plantilla 4000 - Dashboard y Gráficos
SELECT 
    c.codigo_cliente,
    c.nombre_fiscal AS cliente,
    YEAR(f.fecha) AS anno,
    MONTH(f.fecha) AS mes,
    COUNT(DISTINCT f.numero) AS total_facturas,
    SUM(f.total_euros) AS total_ventas,
    AVG(f.total_euros) AS ticket_medio,
    SUM(f.total_euros) / COUNT(DISTINCT MONTH(f.fecha)) AS media_mensual
FROM facturas_venta f
JOIN clientes c ON f.codigo_cliente = c.codigo_cliente
WHERE f.fecha >= DATEADD(YEAR, -1, GETDATE())
GROUP BY c.codigo_cliente, c.nombre_fiscal, YEAR(f.fecha), MONTH(f.fecha)
ORDER BY total_ventas DESC""",
    },
}

PACKS = [
    {
        "id": "pack-gestion-comercial",
        "nombre": "Pack Gestión Comercial",
        "descripcion": "Todo lo que necesitas para gestionar clientes, proveedores y facturas en Sage50BI.",
        "icono": "📦",
        "plantillas": [1000, 1001, 2000],
    },
    {
        "id": "pack-contabilidad-completa",
        "nombre": "Pack Contabilidad Completa",
        "descripcion": "Balances de situación, dashboard de ventas y herramientas contables para tu empresa.",
        "icono": "📊",
        "plantillas": [3000, 4000],
    },
]


def main():
    gestor = Gestor(REPO_ROOT)

    # Directorio temporal para SQL files fuente
    tmp_dir = Path(tempfile.mkdtemp(prefix="sage50bi_samples_"))

    try:
        # === 1. CREAR PLANTILLAS ===
        for tid, data in sorted(SQL_TEMPLATES.items()):
            print(f"  Creando plantilla {tid:04d} - {data['nombre']}...")

            # Escribir SQL a archivo temporal
            sql_file = tmp_dir / f"template_{tid}.sql"
            sql_file.write_text(data["sql"], encoding="utf-8")

            gestor.crear_plantilla_publica(
                template_id=tid,
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                tags=data["tags"],
                sql_path=sql_file,
            )
            print(f"    OK")

        # === 2. CREAR PACKS ===
        print("\nCreando packs...")
        for pack_def in PACKS:
            pack = crear_pack(
                pack_id=pack_def["id"],
                nombre=pack_def["nombre"],
                descripcion=pack_def["descripcion"],
                plantillas=pack_def["plantillas"],
                icono=pack_def["icono"],
            )
            guardar_pack(pack, gestor.dir_packs)
            print(
                f"  {pack_def['icono']} {pack_def['nombre']} ({len(pack_def['plantillas'])} plantillas)"
            )

        # === 3. REGENERAR DOCS ===
        print("\nRegenerando documentacion...")
        plantillas = gestor._obtener_plantillas_existentes()
        packs_list = listar_packs(gestor.dir_packs)
        stats = gestor.obtener_estadisticas()
        plantillas_list = list(plantillas.values())

        # README
        readme_path = generar_y_guardar_readme(REPO_ROOT, plantillas_list, packs_list, stats)
        print(f"  README.md ({readme_path.stat().st_size} bytes)")

        # MkDocs docs
        generados = generar_todo(
            plantillas_list, packs_list, stats, REPO_ROOT / "docs", packs_datos=packs_list
        )
        print(f"  MkDocs: {len(generados)} archivos generados")

        # Manifest
        manifest_path = generar_y_guardar_manifest(REPO_ROOT, plantillas_list, packs_list)
        print(f"  manifest-templates.json ({manifest_path.stat().st_size} bytes)")

        # === 4. RESUMEN ===
        print(f"\n{'=' * 50}")
        print(f"RESUMEN:")
        print(f"  Plantillas creadas: {stats['publicas']} publicas, {stats['privadas']} privadas")
        print(f"  Packs: {stats['total_packs']}")
        print(f"  README: {readme_path.stat().st_size} bytes")
        print(f"  Manifest: {manifest_path.stat().st_size} bytes")
        print(f"  Docs generados: {len(generados)} archivos")
        print(f"{'=' * 50}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
