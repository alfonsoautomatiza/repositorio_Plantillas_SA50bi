"""Tests para integracion/ — Módulo de actualización automática."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from integracion.actualizador import ActualizadorPlantillas
from integracion.descargador import Descargador
from integracion.registro import RegistroLocal


# === Fixtures ===


@pytest.fixture
def tmp_dir(tmp_path):
    """Directorio temporal para tests."""
    return tmp_path


@pytest.fixture
def registro(tmp_dir):
    """RegistroLocal con directorio temporal."""
    return RegistroLocal(str(tmp_dir / "plantillas"))


@pytest.fixture
def manifest_data():
    """Carga el manifest real como datos de test."""
    manifest_path = Path(__file__).parent.parent / "manifest-templates.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def descargador(tmp_dir):
    """Descargador con directorio de caché temporal."""
    return Descargador(cache_dir=str(tmp_dir / "cache"))


@pytest.fixture
def actualizador(tmp_dir):
    """ActualizadorPlantillas con directorio temporal."""
    return ActualizadorPlantillas(
        plantillas_dir=str(tmp_dir / "plantillas"),
        manifest_url="https://example.com/manifest.json",
    )


# ============================================================
# RegistroLocal — 8 tests
# ============================================================


class TestRegistroLocal:
    """Tests para integracion/registro.py"""

    def test_registrar_y_obtener(self, registro):
        """Registrar una plantilla y obtener su versión."""
        registro.registrar(1000, "1.0.0", "Listado de clientes", "Informes y Listados")
        version = registro.obtener_version_instalada(1000)
        assert version == "1.0.0"

    def test_registrar_duplicado_actualiza_version(self, registro):
        """Registrar la misma plantilla dos veces actualiza la versión."""
        registro.registrar(1000, "1.0.0", "Listado de clientes", "Informes y Listados")
        registro.registrar(1000, "1.1.0", "Listado de clientes", "Informes y Listados")
        assert registro.obtener_version_instalada(1000) == "1.1.0"

    def test_desregistrar(self, registro):
        """Desregistrar una plantilla la elimina del registro."""
        registro.registrar(1000, "1.0.0", "Test", "Test")
        assert registro.esta_instalada(1000) is True

        registro.desregistrar(1000)
        assert registro.esta_instalada(1000) is False
        assert registro.obtener_version_instalada(1000) is None

    def test_listar_instaladas(self, registro):
        """Listar todas las plantillas instaladas."""
        registro.registrar(1000, "1.0.0", "Clientes", "Informes")
        registro.registrar(2000, "2.0.0", "Facturas", "Documentos")

        instaladas = registro.listar_instaladas()
        assert len(instaladas) == 2
        ids = [p["id"] for p in instaladas]
        assert 1000 in ids
        assert 2000 in ids

    def test_necesita_actualizacion_true(self, registro):
        """Detecta que una plantilla necesita actualización."""
        registro.registrar(1000, "1.0.0", "Test", "Test")
        assert registro.necesita_actualizacion(1000, "1.1.0") is True

    def test_necesita_actualizacion_false(self, registro):
        """Detecta que una plantilla ya está actualizada."""
        registro.registrar(1000, "1.0.0", "Test", "Test")
        assert registro.necesita_actualizacion(1000, "1.0.0") is False
        assert registro.necesita_actualizacion(1000, "0.9.0") is False

    def test_exportar_estado(self, registro):
        """Exportar el estado completo del registro."""
        registro.registrar(1000, "1.0.0", "Clientes", "Informes")
        estado = registro.exportar_estado()

        assert estado["total_instaladas"] == 1
        assert len(estado["plantillas"]) == 1
        assert "version_registro" in estado
        assert "fecha_actualizacion" in estado

    def test_registro_corrupto(self, tmp_dir):
        """Maneja un archivo de registro corrupto (JSON inválido)."""
        plantillas_dir = tmp_dir / "corrupto"
        plantillas_dir.mkdir()
        registro_path = plantillas_dir / "registro_plantillas.json"
        # Escribir JSON inválido
        registro_path.write_text("{invalid json!!!", encoding="utf-8")

        registro = RegistroLocal(str(plantillas_dir))
        # Debería empezar con un registro vacío
        assert registro.listar_instaladas() == []
        # Y debería poder registrar normalmente
        registro.registrar(1000, "1.0.0", "Test", "Test")
        assert registro.esta_instalada(1000)


class TestRegistroLocalVacio:
    """Tests de edge cases con registro vacío."""

    def test_obtener_version_no_existente(self, registro):
        """Obtener versión de plantilla no registrada devuelve None."""
        assert registro.obtener_version_instalada(9999) is None

    def test_no_instalada(self, registro):
        """Verificar que una plantilla no registrada no está instalada."""
        assert registro.esta_instalada(9999) is False

    def test_necesita_actualizacion_no_instalada(self, registro):
        """necesita_actualizacion devuelve False si no está instalada."""
        assert registro.necesita_actualizacion(9999, "1.0.0") is False

    def test_desregistrar_no_existente(self, registro):
        """Desregistrar algo que no existe no lanza error."""
        registro.desregistrar(9999)  # No debería fallar


# ============================================================
# Descargador — 5 tests
# ============================================================


class TestDescargador:
    """Tests para integracion/descargador.py"""

    def test_url_construida_correctamente(self):
        """La URL base se construye correctamente."""
        assert "wertyMSD/repositorio_Sage50bi/main" in Descargador.BASE_URL

    def test_descargar_desde_archivo_local(self, descargador, tmp_dir):
        """Simula descarga usando mock de urllib."""
        contenido = b"SELECT * FROM clientes"
        url = "https://example.com/test.sql"

        with patch.object(descargador, "descargar_bytes", return_value=contenido):
            resultado = descargador.descargar_archivo(
                "publicas/test/template.sql",
                str(tmp_dir / "template.sql"),
            )
            assert resultado is True
            archivo = tmp_dir / "template.sql"
            assert archivo.exists()
            assert archivo.read_bytes() == contenido

    def test_descargar_archivo_inexistente(self, descargador, tmp_dir):
        """Maneja archivos que no existen (descarga fallida)."""
        with patch.object(descargador, "descargar_bytes", return_value=None):
            resultado = descargador.descargar_archivo(
                "noexiste/archivo.sql",
                str(tmp_dir / "noexiste.sql"),
            )
            assert resultado is False

    def test_descargar_plantilla_completa(self, descargador, tmp_dir):
        """Descarga todos los archivos de una plantilla (mock)."""

        # Mock: template.json y template.sql existen, dashboard.py y preview.png no
        def mock_descargar_bytes(url):
            if "template.json" in url:
                return json.dumps({"id": 1000, "version": "1.0.0"}).encode()
            elif "template.sql" in url:
                return b"SELECT * FROM test"
            return None

        with patch.object(descargador, "descargar_bytes", side_effect=mock_descargar_bytes):
            resultado = descargador.descargar_plantilla(
                1000, "Test Plantilla", str(tmp_dir / "plantilla1000")
            )
            assert "template.json" in resultado["archivos"]
            assert "template.sql" in resultado["archivos"]
            # dashboard.py y preview.png son opcionales, no error
            assert len(resultado["errores"]) == 0

    def test_cache_fallback(self, tmp_dir):
        """Cuando la descarga falla, usa la caché como fallback."""
        cache_dir = tmp_dir / "cache"
        cache_dir.mkdir()
        desc = Descargador(cache_dir=str(cache_dir))

        url = "https://example.com/data.json"
        contenido_original = b'{"test": true}'

        # Primera descarga: exitosa (mock)
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = contenido_original
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            datos = desc.descargar_bytes(url)
            assert datos == contenido_original

        # Segunda descarga: falla la red, usa caché
        with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
            datos = desc.descargar_bytes(url)
            assert datos == contenido_original


# ============================================================
# ActualizadorPlantillas — 10 tests
# ============================================================


class TestActualizadorPlantillas:
    """Tests para integracion/actualizador.py"""

    def test_comprobar_con_manifest_local(self, actualizador, manifest_data):
        """Comprobar actualizaciones usando manifest local (sin red)."""
        resultado = actualizador.comprobar_actualizaciones(manifest=manifest_data)

        assert "nuevas" in resultado
        assert "actualizables" in resultado
        assert "instaladas" in resultado
        assert "privadas" in resultado
        assert "total_disponibles" in resultado
        assert "ultima_comprobacion" in resultado
        # Todas deberían ser nuevas (registro vacío)
        assert len(resultado["nuevas"]) == len(manifest_data.get("plantillas", []))

    def test_identificar_plantillas_nuevas(self, actualizador, manifest_data):
        """Identifica correctamente las plantillas nuevas."""
        resultado = actualizador.comprobar_actualizaciones(manifest=manifest_data)
        # Como el registro está vacío, todas son nuevas
        ids_nuevas = [p["id"] for p in resultado["nuevas"]]
        assert 1000 in ids_nuevas
        assert 1001 in ids_nuevas
        assert 2000 in ids_nuevas

    def test_identificar_actualizables(self, actualizador, manifest_data):
        """Identifica plantillas con versión más reciente disponible."""
        # Instalar una versión vieja de la plantilla 1000
        actualizador.registro.registrar(
            1000, "0.9.0", "Listado de clientes ESPAÑA", "Informes y Listados"
        )

        resultado = actualizador.comprobar_actualizaciones(manifest=manifest_data)
        # La 1000 debería ser actualizable
        ids_actualizables = [p["id"] for p in resultado["actualizables"]]
        assert 1000 in ids_actualizables

    def test_instalar_plantilla_mock(self, actualizador, manifest_data):
        """Instala una plantilla con descarga mockeada."""
        # Inyectar manifest en caché
        actualizador._manifest_cache = manifest_data
        actualizador._manifest_cache_time = datetime.now()

        contenido_json = json.dumps(
            {"id": 1000, "nombre": "Listado de clientes ESPAÑA", "version": "1.0.0"}
        ).encode()
        contenido_sql = b"SELECT * FROM clientes WHERE pais = 'ES'"

        def mock_descargar_plantilla_desde_url(url_base, archivos, dest_dir):
            dest = Path(dest_dir)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "template.json").write_bytes(contenido_json)
            (dest / "template.sql").write_bytes(contenido_sql)
            return {"archivos": ["template.json", "template.sql"], "errores": []}

        with patch.object(
            actualizador.descargador,
            "descargar_plantilla_desde_url",
            side_effect=mock_descargar_plantilla_desde_url,
        ):
            resultado = actualizador.instalar_plantilla(1000)

        assert resultado["exito"] is True
        assert resultado["template_id"] == 1000
        assert resultado["version"] == "1.0.0"
        assert actualizador.registro.esta_instalada(1000)

    def test_instalar_todas_nuevas(self, actualizador, manifest_data):
        """Instala todas las plantillas nuevas (mock)."""
        actualizador._manifest_cache = manifest_data
        actualizador._manifest_cache_time = datetime.now()

        def mock_instalar(tid):
            return {
                "exito": True,
                "template_id": tid,
                "version": "1.0.0",
                "mensaje": "OK",
            }

        with patch.object(
            actualizador.descargador, "descargar_manifest", return_value=manifest_data
        ):
            with patch.object(actualizador, "instalar_plantilla", side_effect=mock_instalar):
                resultados = actualizador.instalar_todas_nuevas()

        # Debería intentar instalar todas las del manifest
        assert len(resultados) == len(manifest_data.get("plantillas", []))

    def test_actualizar_plantilla(self, actualizador, manifest_data):
        """Actualiza una plantilla a la última versión."""
        actualizador._manifest_cache = manifest_data
        actualizador._manifest_cache_time = datetime.now()

        # Registrar versión vieja
        actualizador.registro.registrar(
            1000, "0.9.0", "Listado de clientes ESPAÑA", "Informes y Listados"
        )

        def mock_descargar_plantilla_desde_url(url_base, archivos, dest_dir):
            dest = Path(dest_dir)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "template.json").write_bytes(b'{"id": 1000}')
            (dest / "template.sql").write_bytes(b"SELECT 1")
            return {"archivos": ["template.json", "template.sql"], "errores": []}

        with patch.object(
            actualizador.descargador, "descargar_manifest", return_value=manifest_data
        ):
            with patch.object(
                actualizador.descargador,
                "descargar_plantilla_desde_url",
                side_effect=mock_descargar_plantilla_desde_url,
            ):
                resultado = actualizador.actualizar_plantilla(1000)

        assert resultado["exito"] is True
        assert resultado["version"] == "1.0.0"

    def test_plantilla_privada_sin_licencia(self, actualizador):
        """No se puede instalar plantilla privada sin licencia."""
        resultado = actualizador.instalar_plantilla_privada(5001)
        assert resultado["exito"] is False
        assert (
            "licencia" in resultado["mensaje"].lower() or "cliente" in resultado["mensaje"].lower()
        )

    def test_desinstalar_plantilla(self, actualizador, tmp_dir):
        """Desinstala una plantilla correctamente."""
        # Registrar y crear directorio
        actualizador.registro.registrar(1000, "1.0.0", "Test Plantilla", "Test")
        dest_dir = actualizador._directorio_plantilla(1000, "Test Plantilla")
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / "template.sql").write_text("SELECT 1")

        resultado = actualizador.desinstalar_plantilla(1000)
        assert resultado is True
        assert not actualizador.registro.esta_instalada(1000)
        assert not dest_dir.exists()

    def test_obtener_estado(self, actualizador):
        """Obtiene el resumen del estado actual."""
        actualizador.registro.registrar(1000, "1.0.0", "Test", "Test")
        estado = actualizador.obtener_estado()

        assert estado["total_instaladas"] == 1
        assert len(estado["plantillas_instaladas"]) == 1
        assert "directorio_plantillas" in estado

    def test_manejar_error_red(self, actualizador):
        """Maneja errores de red de forma graceful."""
        with patch.object(
            actualizador.descargador,
            "descargar_manifest",
            return_value=None,
        ):
            resultado = actualizador.comprobar_actualizaciones()
            assert resultado["total_disponibles"] == 0
            assert "error" in resultado
