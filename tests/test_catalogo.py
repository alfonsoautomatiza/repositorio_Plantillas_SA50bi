"""Tests para el módulo catalogo/."""

import json
import tempfile
from pathlib import Path

from catalogo.manifest_reader import ManifestReader
from catalogo.recomendaciones import (
    recomendar_por_tags,
    recomendar_por_manifest,
    recomendar_por_categoria,
)
from catalogo.instalador import Instalador


# --- Helpers ---

MANIFEST_PATH = Path(__file__).parent.parent / "manifest-templates.json"


def _manifest_data():
    """Carga el manifest real del proyecto como datos de test."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _manifest_temp(manifest_data: dict = None):
    """Crea un archivo temporal con manifest para tests."""
    if manifest_data is None:
        manifest_data = _manifest_data()
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(manifest_data, tmp, ensure_ascii=False)
    tmp.flush()
    tmp.close()
    return tmp.name


def _plantilla(**overrides):
    """Crea una plantilla de test con valores por defecto."""
    p = {
        "id": 9999,
        "nombre": "Plantilla Test",
        "version": "1.0.0",
        "tipo": "publica",
        "categoria": "Informes y Listados",
        "url_base": "https://example.com/",
        "archivos": {"sql": {"nombre": "template.sql", "hash_sha256": "abc123", "opcional": False}},
        "preview_url": "",
        "youtube_url": "",
        "recomendaciones": [],
        "descripcion": "Descripción de test",
        "tags": ["test", "prueba"],
    }
    p.update(overrides)
    return p


# === ManifestReader ===


def test_cargar_manifest_local():
    """Carga el manifest desde archivo local."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        manifest = reader.cargar_manifest()
        assert "plantillas" in manifest
        assert len(manifest["plantillas"]) > 0
    finally:
        Path(path).unlink(missing_ok=True)


def test_cargar_manifest_cache():
    """El manifest se cachea en memoria tras la primera carga."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        m1 = reader.cargar_manifest()
        m2 = reader.cargar_manifest()
        assert m1 is m2  # Mismo objeto en memoria
    finally:
        Path(path).unlink(missing_ok=True)


def test_cargar_manifest_archivo_inexistente():
    """Error si el archivo local no existe."""
    reader = ManifestReader("/no/existe/manifest.json")
    try:
        reader.cargar_manifest()
        assert False, "Debería lanzar FileNotFoundError"
    except FileNotFoundError:
        pass


def test_obtener_plantillas_sin_filtro():
    """Obtener todas las plantillas sin filtro de categoría."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        plantillas = reader.obtener_plantillas()
        assert len(plantillas) == 5
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_plantillas_por_categoria():
    """Filtrar plantillas por categoría específica."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        # Informes y Listados: IDs 1000, 1001
        plantillas = reader.obtener_plantillas("Informes y Listados")
        assert len(plantillas) == 2
        assert all(p["categoria"] == "Informes y Listados" for p in plantillas)
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_plantillas_categoria_vacia():
    """Categoría sin plantillas devuelve lista vacía."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        plantillas = reader.obtener_plantillas("Categoría Inexistente")
        assert plantillas == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_buscar_por_nombre():
    """Buscar por texto en el nombre y descripción."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        resultados = reader.buscar("clientes")
        # "clientes" aparece en nombre (1000) y en descripción de 4000 ("por cliente")
        assert len(resultados) == 2
        ids = [r["id"] for r in resultados]
        assert 1000 in ids
    finally:
        Path(path).unlink(missing_ok=True)


def test_buscar_por_tag():
    """Buscar por texto en tags."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        resultados = reader.buscar("compras")
        assert len(resultados) >= 1
        # ID 1001 tiene tag "compras"
        ids = [r["id"] for r in resultados]
        assert 1001 in ids
    finally:
        Path(path).unlink(missing_ok=True)


def test_buscar_por_descripcion():
    """Buscar por texto en descripción."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        resultados = reader.buscar("interactivo")
        assert len(resultados) >= 1
        ids = [r["id"] for r in resultados]
        assert 4000 in ids
    finally:
        Path(path).unlink(missing_ok=True)


def test_buscar_vacio_devuelve_todas():
    """Búsqueda vacía devuelve todas las plantillas."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        resultados = reader.buscar("")
        assert len(resultados) == 5
    finally:
        Path(path).unlink(missing_ok=True)


def test_buscar_sin_resultados():
    """Búsqueda sin coincidencias devuelve lista vacía."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        resultados = reader.buscar("xyz_no_existe_12345")
        assert resultados == []
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_packs():
    """Obtener packs del manifest."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        packs = reader.obtener_packs()
        assert len(packs) == 2
        ids = [p["id"] for p in packs]
        assert "pack-contabilidad-completa" in ids
        assert "pack-gestion-comercial" in ids
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_plantilla_existente():
    """Obtener una plantilla específica por ID."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        p = reader.obtener_plantilla(1000)
        assert p is not None
        assert p["id"] == 1000
        assert p["nombre"] == "Listado de clientes ESPAÑA"
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_plantilla_inexistente():
    """Obtener plantilla inexistente devuelve None."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        p = reader.obtener_plantilla(99999)
        assert p is None
    finally:
        Path(path).unlink(missing_ok=True)


def test_obtener_novedades():
    """Obtener novedades devuelve plantillas del manifest actual."""
    path = _manifest_temp()
    try:
        reader = ManifestReader(path)
        novedades = reader.obtener_novedades(30)
        # El manifest actual tiene fecha de hoy, así que todas son novedades
        assert len(novedades) > 0
    finally:
        Path(path).unlink(missing_ok=True)


# === recomendar_por_tags ===


def test_recomendar_por_tags_basico():
    """Recomendar por tags con solapamiento."""
    actual = _plantilla(tags=["clientes", "listado", "españa"])
    todas = [
        _plantilla(id=1001, tags=["proveedores", "listado", "compras"]),
        _plantilla(id=2000, tags=["factura", "modelo", "totales"]),
        _plantilla(id=2001, tags=["clientes", "listado", "informes"]),
    ]
    resultados = recomendar_por_tags(actual, todas)
    # 2001 tiene 2 tags en común (clientes, listado), 1001 tiene 1 (listado)
    assert len(resultados) == 2
    assert resultados[0]["id"] == 2001  # Más coincidencias primero


def test_recomendar_por_tags_max_resultados():
    """Respeta el límite de max_resultados."""
    actual = _plantilla(tags=["a", "b", "c"])
    todas = [_plantilla(id=i, tags=["a", "b", "c"]) for i in range(10)]
    resultados = recomendar_por_tags(actual, todas, max_resultados=2)
    assert len(resultados) == 2


def test_recomendar_por_tags_sin_coincidencias():
    """Sin coincidencias devuelve lista vacía."""
    actual = _plantilla(tags=["unico", "exclusivo"])
    todas = [
        _plantilla(id=1, tags=["otro", "diferente"]),
    ]
    resultados = recomendar_por_tags(actual, todas)
    assert resultados == []


def test_recomendar_por_tags_sin_tags():
    """Plantilla sin tags devuelve lista vacía."""
    actual = _plantilla(tags=[])
    todas = [_plantilla(id=1, tags=["test"])]
    resultados = recomendar_por_tags(actual, todas)
    assert resultados == []


def test_recomendar_por_tags_se_excluye_a_si_misma():
    """La plantilla actual no aparece en sus propias recomendaciones."""
    actual = _plantilla(id=1000, tags=["test"])
    todas = [_plantilla(id=1000, tags=["test"])]
    resultados = recomendar_por_tags(actual, todas)
    assert resultados == []


# === recomendar_por_manifest ===


def test_recomendar_por_manifest_manual():
    """Las recomendaciones manuales tienen prioridad."""
    data = {
        "plantillas": [
            _plantilla(id=1000, recomendaciones=[1001, 1002]),
            _plantilla(id=1001, tags=["listado"]),
            _plantilla(id=1002, tags=["informes"]),
            _plantilla(id=1003, tags=["test"]),
        ]
    }
    resultados = recomendar_por_manifest(data, 1000, max_resultados=3)
    ids = [r["id"] for r in resultados]
    assert 1001 in ids
    assert 1002 in ids


def test_recomendar_por_manifest_auto_rellena():
    """Las automáticas rellenan los huecos cuando no hay suficientes manuales."""
    data = {
        "plantillas": [
            _plantilla(id=1000, tags=["clientes", "listado"], recomendaciones=[1001]),
            _plantilla(id=1001, tags=["proveedores"]),
            _plantilla(id=1002, tags=["clientes", "listado"]),
            _plantilla(id=1003, tags=["clientes"]),
        ]
    }
    resultados = recomendar_por_manifest(data, 1000, max_resultados=3)
    ids = [r["id"] for r in resultados]
    # 1001 es manual, 1002 y 1003 son auto por tags
    assert 1001 in ids
    assert len(resultados) == 3


def test_recomendar_por_manifest_id_inexistente():
    """ID inexistente devuelve lista vacía."""
    data = {"plantillas": [_plantilla(id=1000)]}
    resultados = recomendar_por_manifest(data, 9999)
    assert resultados == []


def test_recomendar_por_manifest_no_duplica():
    """No duplica manuales en las automáticas."""
    data = {
        "plantillas": [
            _plantilla(id=1000, tags=["a", "b"], recomendaciones=[1001]),
            _plantilla(id=1001, tags=["a", "b"]),
            _plantilla(id=1002, tags=["a"]),
        ]
    }
    resultados = recomendar_por_manifest(data, 1000, max_resultados=3)
    ids = [r["id"] for r in resultados]
    # 1001 aparece solo una vez
    assert ids.count(1001) == 1


# === recomendar_por_categoria ===


def test_recomendar_por_categoria_basico():
    """Recomienda plantillas de la misma categoría."""
    actual = _plantilla(categoria="Informes y Listados")
    todas = [
        _plantilla(id=1001, categoria="Informes y Listados"),
        _plantilla(id=2000, categoria="Facturas y Documentos"),
        _plantilla(id=1002, categoria="Informes y Listados"),
    ]
    resultados = recomendar_por_categoria(actual, todas)
    assert len(resultados) == 2
    assert all(r["categoria"] == "Informes y Listados" for r in resultados)


def test_recomendar_por_categoria_limite():
    """Respeta el límite de max_resultados."""
    actual = _plantilla(categoria="Test")
    todas = [_plantilla(id=i, categoria="Test") for i in range(10)]
    resultados = recomendar_por_categoria(actual, todas, max_resultados=2)
    assert len(resultados) == 2


def test_recomendar_por_categoria_sin_categoria():
    """Sin categoría devuelve lista vacía."""
    actual = _plantilla(categoria="")
    todas = [_plantilla(id=1, categoria="Test")]
    resultados = recomendar_por_categoria(actual, todas)
    assert resultados == []


# === Instalador.estado_instalacion ===


def test_instalador_estado_no_instalada():
    """Plantilla no instalada devuelve 'no_instalada'."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)
            estado = instalador.estado_instalacion(1000)
            assert estado == "no_instalada"
        finally:
            Path(path).unlink(missing_ok=True)


def test_instalador_estado_instalada():
    """Plantilla instalada con misma versión devuelve 'instalada'."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)

            # Simular instalación previa
            registro = {
                "1000": {
                    "nombre": "Listado de clientes ESPAÑA",
                    "version": "1.0.0",
                    "categoria": "Informes y Listados",
                    "fecha_instalacion": "2026-04-07T00:00:00",
                }
            }
            with open(instalador._registro_path, "w", encoding="utf-8") as f:
                json.dump(registro, f)

            estado = instalador.estado_instalacion(1000)
            assert estado == "instalada"
        finally:
            Path(path).unlink(missing_ok=True)


def test_instalador_estado_actualizable():
    """Plantilla instalada con versión anterior devuelve 'actualizable'."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)

            # Simular instalación previa con versión anterior
            registro = {
                "1000": {
                    "nombre": "Listado de clientes ESPAÑA",
                    "version": "0.9.0",
                    "categoria": "Informes y Listados",
                    "fecha_instalacion": "2026-04-01T00:00:00",
                }
            }
            with open(instalador._registro_path, "w", encoding="utf-8") as f:
                json.dump(registro, f)

            estado = instalador.estado_instalacion(1000)
            assert estado == "actualizable"
        finally:
            Path(path).unlink(missing_ok=True)


def test_instalador_listar_instaladas():
    """Listar plantillas instaladas."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)

            # Simular dos instalaciones
            registro = {
                "1000": {
                    "nombre": "Plantilla A",
                    "version": "1.0.0",
                    "categoria": "Informes y Listados",
                    "fecha_instalacion": "2026-04-07T00:00:00",
                },
                "2000": {
                    "nombre": "Plantilla B",
                    "version": "1.0.0",
                    "categoria": "Facturas y Documentos",
                    "fecha_instalacion": "2026-04-07T00:00:00",
                },
            }
            with open(instalador._registro_path, "w", encoding="utf-8") as f:
                json.dump(registro, f)

            instaladas = instalador.listar_instaladas()
            assert len(instaladas) == 2
            ids = [i["id"] for i in instaladas]
            assert 1000 in ids
            assert 2000 in ids
        finally:
            Path(path).unlink(missing_ok=True)


def test_instalador_listar_instaladas_vacio():
    """Sin instalaciones devuelve lista vacía."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)
            instaladas = instalador.listar_instaladas()
            assert instaladas == []
        finally:
            Path(path).unlink(missing_ok=True)


def test_instalador_registro_corrupto():
    """Registro corrupto no rompe el estado de instalación."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _manifest_temp()
        try:
            reader = ManifestReader(path)
            instalador = Instalador(reader, tmp)

            # Escribir JSON inválido
            with open(instalador._registro_path, "w") as f:
                f.write("no es json valido{{{")

            # Debería devolver no_instalada sin crashear
            estado = instalador.estado_instalacion(1000)
            assert estado == "no_instalada"
        finally:
            Path(path).unlink(missing_ok=True)
