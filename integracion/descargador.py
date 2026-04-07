"""
Descargador de archivos de plantillas desde GitHub.

Usa únicamente urllib.request (sin dependencias externas).
Maneja cache local para modo offline.
"""

import hashlib
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


class Descargador:
    """Downloads template files from GitHub raw URLs."""

    BASE_URL = "https://raw.githubusercontent.com/wertyMSD/repositorio_Sage50bi/main"

    # Timeout en segundos para peticiones HTTP
    TIMEOUT = 30

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Args:
            cache_dir: Directorio local para cache de descargas.
                       Si es None, no se usa caché.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _url_a_ruta_cache(self, url: str) -> Path:
        """Convierte una URL en una ruta de caché local."""
        # Usar hash de la URL como nombre de archivo
        hash_url = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self.cache_dir / hash_url

    def _guardar_en_cache(self, url: str, datos: bytes) -> None:
        """Guarda datos descargados en la caché."""
        if not self.cache_dir:
            return
        ruta = self._url_a_ruta_cache(url)
        ruta.write_bytes(datos)

    def _obtener_de_cache(self, url: str) -> Optional[bytes]:
        """Intenta obtener datos desde la caché local."""
        if not self.cache_dir:
            return None
        ruta = self._url_a_ruta_cache(url)
        if ruta.exists():
            return ruta.read_bytes()
        return None

    def descargar_bytes(self, url: str) -> Optional[bytes]:
        """Descarga un archivo y devuelve su contenido como bytes.

        Si falla la descarga, intenta usar la caché como fallback.
        """
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Sage50BI/1.0"})
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                datos = resp.read()
                self._guardar_en_cache(url, datos)
                return datos
        except Exception:
            # Fallback a caché — cualquier error de red
            return self._obtener_de_cache(url)

    def descargar_archivo(self, ruta_relativa: str, destino: str) -> bool:
        """Descarga un archivo del repositorio a una ruta local.

        Args:
            ruta_relativa: Ruta relativa en el repo (ej: 'publicas/1000%20-%20.../template.sql')
            destino: Ruta local donde guardar el archivo

        Returns:
            True si se descargó correctamente, False si no.
        """
        url = f"{self.BASE_URL}/{ruta_relativa}"
        datos = self.descargar_bytes(url)
        if datos is None:
            return False

        destino_path = Path(destino)
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        destino_path.write_bytes(datos)
        return True

    def descargar_plantilla(self, template_id: int, nombre: str, destino_dir: str) -> dict:
        """Descarga todos los archivos de una plantilla.

        Descarga: template.json, template.sql (cifrado),
                  dashboard.py si existe, preview.png si existe.

        Args:
            template_id: ID de la plantilla.
            nombre: Nombre de la plantilla (para construir la URL).
            destino_dir: Directorio local donde guardar los archivos.

        Returns:
            {'archivos': [lista de archivos descargados], 'errores': [lista de errores]}
        """
        # Codificar nombre para URL
        nombre_codificado = urllib.request.quote(f"{template_id} - {nombre}", safe="")
        # Para las URLs del manifest, el nombre ya viene codificado con espacios como %20
        ruta_base = f"publicas/{nombre_codificado}"

        destino = Path(destino_dir)
        destino.mkdir(parents=True, exist_ok=True)

        archivos = []
        errores = []

        # Archivos obligatorios y opcionales
        archivos_a_descargar = [
            ("template.json", True),
            ("template.sql", True),
            ("dashboard.py", False),
            ("preview.png", False),
        ]

        for nombre_archivo, obligatorio in archivos_a_descargar:
            ruta_relativa = f"{ruta_base}/{nombre_archivo}"
            ruta_destino = destino / nombre_archivo

            exito = self.descargar_archivo(ruta_relativa, str(ruta_destino))
            if exito:
                archivos.append(nombre_archivo)
            elif obligatorio:
                errores.append(f"No se pudo descargar archivo obligatorio: {nombre_archivo}")

        return {"archivos": archivos, "errores": errores}

    def descargar_plantilla_desde_url(
        self, url_base: str, archivos_manifest: dict, destino_dir: str
    ) -> dict:
        """Descarga los archivos de una plantilla usando la url_base del manifest.

        Este método usa directamente la url_base del manifest (ya codificada)
        en vez de reconstruirla.

        Args:
            url_base: URL base del manifest (ej: https://raw.githubusercontent.com/...).
            archivos_manifest: Diccionario 'archivos' del manifest.
            destino_dir: Directorio local destino.

        Returns:
            {'archivos': [lista], 'errores': [lista]}
        """
        destino = Path(destino_dir)
        destino.mkdir(parents=True, exist_ok=True)

        archivos = []
        errores = []

        # Descargar template.json (siempre está)
        url_template_json = f"{url_base}template.json"
        datos = self.descargar_bytes(url_template_json)
        if datos:
            (destino / "template.json").write_bytes(datos)
            archivos.append("template.json")
        else:
            errores.append("No se pudo descargar template.json")

        # Descargar archivos del manifest
        for tipo, info in archivos_manifest.items():
            nombre_archivo = info.get("nombre", f"template.{tipo}")
            url_archivo = f"{url_base}{nombre_archivo}"
            datos = self.descargar_bytes(url_archivo)
            if datos:
                (destino / nombre_archivo).write_bytes(datos)
                archivos.append(nombre_archivo)
            elif not info.get("opcional", False):
                errores.append(f"No se pudo descargar archivo obligatorio: {nombre_archivo}")

        return {"archivos": archivos, "errores": errores}

    def descargar_pack(self, pack_json_url: str, destino: str) -> bool:
        """Descarga un archivo JSON de pack.

        Args:
            pack_json_url: URL del archivo pack JSON.
            destino: Ruta local donde guardarlo.

        Returns:
            True si se descargó correctamente.
        """
        datos = self.descargar_bytes(pack_json_url)
        if datos is None:
            return False

        destino_path = Path(destino)
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        destino_path.write_bytes(datos)
        return True

    def descargar_manifest(self, manifest_url: str) -> Optional[dict]:
        """Descarga y parsea el manifest-templates.json remoto.

        Args:
            manifest_url: URL del manifest JSON.

        Returns:
            Diccionario con el manifest, o None si falla.
        """
        datos = self.descargar_bytes(manifest_url)
        if datos is None:
            return None

        try:
            return json.loads(datos.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
