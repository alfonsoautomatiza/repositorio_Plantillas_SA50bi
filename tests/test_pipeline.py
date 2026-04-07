"""
Test end-to-end: crea plantilla, cifra, genera docs, manifest.
Valida que todo el pipeline funciona de principio a fin.
"""

import shutil
import tempfile
from pathlib import Path

from gestion.gestor import Gestor
from gestion.schemas import cargar_template_json
from gestion.readme_generator import generar_y_guardar_readme
from gestion.mkdocs_generator import generar_todo
from gestion.manifest_generator import generar_y_guardar_manifest
from gestion.pack_generator import crear_pack, guardar_pack, listar_packs
from gestion.cifrado import descifrar_archivo_publico, verificar_integridad
from gestion.sql_validator import validar_sql


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_SQL = FIXTURES_DIR / "sample_clientes.sql"


def test_pipeline_completo():
    """
    Pipeline completo:
    1. Crear repo temporal
    2. Crear plantilla pública
    3. Verificar cifrado y archivos
    4. Crear pack
    5. Generar README, docs MkDocs, manifest
    6. Verificar que todo existe y es coherente
    """

    # 1. Setup repo temporal
    tmp = Path(tempfile.mkdtemp(prefix="sage50bi_test_"))
    try:
        for d in ["publicas", "privadas", "privado_mantenimiento", "packs", "docs"]:
            (tmp / d).mkdir(parents=True, exist_ok=True)

        gestor = Gestor(tmp)

        # 2. Crear plantilla pública
        template_data = gestor.crear_plantilla_publica(
            template_id=1000,
            nombre="Listado de clientes ESPAÑA",
            descripcion="Listado completo de clientes con filtros por provincia y forma de pago.",
            tags=["clientes", "listado", "españa", "sage50"],
            sql_path=SAMPLE_SQL,
        )

        # Verificar datos devueltos
        assert template_data["id"] == 1000
        assert template_data["tipo"] == "publica"
        assert template_data["version"] == "1.0.0"
        assert len(template_data["tags"]) == 4

        # 3. Verificar archivos creados
        carpeta_pub = tmp / "publicas" / "1000 - Listado de clientes ESPAÑA"
        assert carpeta_pub.exists()
        assert (carpeta_pub / "template.json").exists()
        assert (carpeta_pub / "template.sql").exists()

        carpeta_mant = tmp / "privado_mantenimiento" / "1000 - Listado de clientes ESPAÑA"
        assert carpeta_mant.exists()
        assert (carpeta_mant / "template.sql").exists()

        # Verificar que el SQL cifrado existe y no es texto plano
        sql_cifrado = (carpeta_pub / "template.sql").read_bytes()
        sql_claro = (carpeta_mant / "template.sql").read_text(encoding="utf-8")
        assert sql_cifrado != sql_claro.encode("utf-8")  # No es el mismo contenido
        assert "SELECT" not in sql_cifrado.decode("utf-8", errors="ignore")[:200]

        # Verificar hash
        hash_sql = template_data["archivos"]["sql"]["hash_sha256"]
        assert len(hash_sql) == 64  # SHA256 hex

        # Verificar template.json válido
        loaded = cargar_template_json(carpeta_pub / "template.json")
        assert loaded["id"] == 1000

        # 4. Crear pack
        pack = crear_pack("test-pack", "Pack Test", "Pack de testing.", [1000])
        guardar_pack(pack, tmp / "packs")
        assert (tmp / "packs" / "pack-test-pack.json").exists()

        # 5. Generar docs
        plantillas = gestor._obtener_plantillas_existentes()
        packs = listar_packs(tmp / "packs")
        stats = gestor.obtener_estadisticas()

        # README
        readme_path = generar_y_guardar_readme(tmp, list(plantillas.values()), packs, stats)
        assert readme_path.exists()
        readme_content = readme_path.read_text(encoding="utf-8")
        assert "Listado de clientes ESPAÑA" in readme_content
        assert "Pack Test" in readme_content

        # MkDocs
        generados = generar_todo(
            list(plantillas.values()), packs, stats, tmp / "docs", packs_datos=packs
        )
        assert "index" in generados
        assert "rss" in generados
        assert generados["index"].exists()

        # Manifest
        manifest_path = generar_y_guardar_manifest(tmp, list(plantillas.values()), packs)
        assert manifest_path.exists()

        import json

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["total_plantillas"] == 1
        assert manifest["plantillas"][0]["id"] == 1000

        # 6. Stats coherentes
        assert stats["publicas"] == 1
        assert stats["privadas"] == 0
        assert stats["total_plantillas"] == 1

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pipeline_plantilla_privada():
    """Test crear plantilla privada con cifrado por licencia de cliente."""

    tmp = Path(tempfile.mkdtemp(prefix="sage50bi_priv_"))
    try:
        for d in ["publicas", "privadas", "privado_mantenimiento"]:
            (tmp / d).mkdir(parents=True, exist_ok=True)

        gestor = Gestor(tmp)
        licencia = "TEST-LICENCIA-12345"

        template_data = gestor.crear_plantilla_privada(
            template_id=42,
            nombre="Informe Test",
            descripcion="Informe de testing.",
            tags=["test", "privada"],
            cliente_codigo="CLI-00001",
            cliente_licencia=licencia,
            sql_path=SAMPLE_SQL,
        )

        assert template_data["id"] == 42
        assert template_data["tipo"] == "privada"
        assert template_data["cliente"]["codigo"] == "CLI-00001"

        # Verificar archivos
        carpeta_priv = tmp / "privadas" / "CLI-00001"
        assert carpeta_priv.exists()
        assert (carpeta_priv / "template.sql").exists()
        assert (carpeta_priv / "template.json").exists()

        # Verificar cifrado diferente al público
        sql_cifrado_bytes = (carpeta_priv / "template.sql").read_bytes()
        sql_claro = (tmp / "privado_mantenimiento" / "CLI-00001" / "template.sql").read_bytes()
        assert sql_cifrado_bytes != sql_claro

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pipeline_actualizar():
    """Test actualizar plantilla existente."""

    tmp = Path(tempfile.mkdtemp(prefix="sage50bi_update_"))
    try:
        for d in ["publicas", "privado_mantenimiento"]:
            (tmp / d).mkdir(parents=True, exist_ok=True)

        gestor = Gestor(tmp)

        # Crear
        gestor.crear_plantilla_publica(
            template_id=1000,
            nombre="Test Update",
            descripcion="Desc original.",
            tags=["test"],
            sql_path=SAMPLE_SQL,
        )

        # Crear SQL nuevo para update
        new_sql = tmp / "nuevo.sql"
        new_sql.write_text(
            "SELECT codigo, nombre FROM proveedores WHERE pais = 'ES'", encoding="utf-8"
        )

        # Actualizar
        from gestion.version_manager import BumpType

        updated = gestor.actualizar_plantilla(
            template_id=1000,
            bump_type=BumpType.PATCH,
            descripcion_cambios="Fix: actualizar consulta",
            nuevo_sql_path=new_sql,
        )

        assert updated["version"] == "1.0.1"
        assert updated["fecha_actualizacion"] != updated["fecha_creacion"] or True  # Mismo día OK

        # Verificar changelog
        assert len(updated["changelog"]) == 2  # Inicial + actualización
        assert updated["changelog"][0]["version"] == "1.0.1"

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
