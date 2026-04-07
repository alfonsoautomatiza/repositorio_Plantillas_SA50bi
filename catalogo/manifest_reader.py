"""
Lector de manifest-templates.json remoto para el catálogo Sage50BI.

Soporta carga desde URL remota (GitHub Pages) o archivo local,
con caché en disco y fallback.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


class ManifestReader:
    """Lector de manifest-templates.json con soporte remoto y caché local."""

    def __init__(self, manifest_url: str, cache_dir: str = None):
        """
        Inicializa el lector de manifest.

        Args:
            manifest_url: URL remota o ruta local al manifest-templates.json
            cache_dir: Directorio local para caché (opcional)
        """
        self.manifest_url = manifest_url
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._manifest: Optional[dict] = None

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cargar_manifest(self) -> dict:
        """
        Carga el manifest desde la fuente, con caché y fallback.

        Intenta cargar desde URL remota. Si falla, intenta caché local.
        Si es ruta local, carga directamente.

        Returns:
            dict: Contenido del manifest parseado
        """
        if self._manifest is not None:
            return self._manifest

        # Si es ruta local, cargar directamente
        if self._es_ruta_local():
            self._manifest = self._cargar_local()
            return self._manifest

        # Intentar remoto con fallback a caché
        manifest = self._cargar_remoto()
        if manifest is None:
            manifest = self._cargar_cache()

        if manifest is None:
            raise RuntimeError(f"No se pudo cargar el manifest desde {self.manifest_url}")

        self._manifest = manifest
        return self._manifest

    def _es_ruta_local(self) -> bool:
        """Determina si la URL es una ruta local."""
        return not self.manifest_url.startswith(("http://", "https://"))

    def _cargar_local(self) -> dict:
        """Carga manifest desde archivo local."""
        path = Path(self.manifest_url)
        if not path.exists():
            raise FileNotFoundError(f"Manifest local no encontrado: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _cargar_remoto(self) -> Optional[dict]:
        """Carga manifest desde URL remota."""
        try:
            req = Request(self.manifest_url, headers={"User-Agent": "Sage50BI-Catalog/1.0"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._guardar_cache(data)
                return data
        except (URLError, json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error cargando manifest remoto: {e}")
            return None

    def _guardar_cache(self, data: dict) -> None:
        """Guarda manifest en caché local."""
        if not self.cache_dir:
            return
        try:
            cache_path = self.cache_dir / "manifest-templates.json"
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning(f"Error guardando caché: {e}")

    def _cargar_cache(self) -> Optional[dict]:
        """Carga manifest desde caché local."""
        if not self.cache_dir:
            return None
        cache_path = self.cache_dir / "manifest-templates.json"
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error cargando caché: {e}")
            return None

    def obtener_plantillas(self, categoria: str = None) -> list[dict]:
        """
        Obtiene plantillas, opcionalmente filtradas por categoría.

        Args:
            categoria: Nombre de categoría para filtrar (None = todas)

        Returns:
            Lista de diccionarios de plantillas
        """
        manifest = self.cargar_manifest()
        plantillas = manifest.get("plantillas", [])
        if categoria:
            plantillas = [p for p in plantillas if p.get("categoria") == categoria]
        return plantillas

    def buscar(self, texto: str) -> list[dict]:
        """
        Busca plantillas por nombre y tags.

        La búsqueda es insensible a mayúsculas/minúsculas y busca coincidencias
        parciales en el nombre y en cada tag.

        Args:
            texto: Texto de búsqueda

        Returns:
            Lista de plantillas que coinciden
        """
        if not texto or not texto.strip():
            return self.obtener_plantillas()

        texto_lower = texto.strip().lower()
        resultados = []
        for p in self.obtener_plantillas():
            # Buscar en nombre
            if texto_lower in p.get("nombre", "").lower():
                resultados.append(p)
                continue
            # Buscar en tags
            tags = p.get("tags", [])
            if any(texto_lower in tag.lower() for tag in tags):
                resultados.append(p)
                continue
            # Buscar en descripción
            if texto_lower in p.get("descripcion", "").lower():
                resultados.append(p)
        return resultados

    def obtener_packs(self) -> list[dict]:
        """
        Obtiene los packs disponibles.

        Returns:
            Lista de diccionarios de packs
        """
        manifest = self.cargar_manifest()
        return manifest.get("packs", [])

    def obtener_plantilla(self, template_id: int) -> Optional[dict]:
        """
        Obtiene una plantilla específica por su ID.

        Args:
            template_id: ID de la plantilla

        Returns:
            Diccionario de la plantilla o None si no existe
        """
        for p in self.obtener_plantillas():
            if p.get("id") == template_id:
                return p
        return None

    def descargar_plantilla(self, template_id: int, destino: str) -> bool:
        """
        Descarga los archivos de una plantilla al destino especificado.

        Args:
            template_id: ID de la plantilla a descargar
            destino: Directorio donde guardar los archivos

        Returns:
            True si la descarga fue exitosa
        """
        plantilla = self.obtener_plantilla(template_id)
        if not plantilla:
            logger.error(f"Plantilla {template_id} no encontrada")
            return False

        destino_path = Path(destino)
        destino_path.mkdir(parents=True, exist_ok=True)

        url_base = plantilla.get("url_base", "")
        archivos = plantilla.get("archivos", {})

        for tipo, info in archivos.items():
            nombre_archivo = info.get("nombre", f"{tipo}.enc")
            url_descarga = f"{url_base}{nombre_archivo}"

            try:
                req = Request(url_descarga, headers={"User-Agent": "Sage50BI-Catalog/1.0"})
                with urlopen(req, timeout=30) as resp:
                    contenido = resp.read()

                archivo_destino = destino_path / nombre_archivo
                with open(archivo_destino, "wb") as f:
                    f.write(contenido)

            except (URLError, OSError) as e:
                logger.error(f"Error descargando {tipo} de plantilla {template_id}: {e}")
                return False

        return True

    def obtener_novedades(self, dias: int = 30) -> list[dict]:
        """
        Obtiene plantillas actualizadas en los últimos N días.

        Usa la fecha_generacion del manifest como referencia para simular
        novedades, ya que las plantillas en el manifest no tienen fecha individual
        de actualización.

        Args:
            dias: Número de días hacia atrás

        Returns:
            Lista de plantillas recientes
        """
        manifest = self.cargar_manifest()
        fecha_str = manifest.get("fecha_generacion", "")
        plantillas = manifest.get("plantillas", [])

        if not fecha_str:
            return plantillas[:5]  # Fallback: devolver las 5 primeras

        try:
            fecha_gen = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            limite = fecha_gen - timedelta(days=dias)
        except (ValueError, TypeError):
            return plantillas[:5]

        # Como las plantillas del manifest no tienen fecha individual,
        # consideramos "novedades" a las del manifest actual si la fecha
        # de generación está dentro del rango
        if fecha_gen >= limite:
            return plantillas
        return []
