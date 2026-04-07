"""
Instalador de plantillas Sage50BI.

Gestiona la descarga, descifrado e instalación de plantillas
desde el catálogo remoto al directorio local de Sage50BI.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .manifest_reader import ManifestReader

logger = logging.getLogger(__name__)


class Instalador:
    """Instala y gestiona plantillas desde el manifest remoto."""

    def __init__(self, manifest_reader: ManifestReader, destino_base: str):
        """
        Inicializa el instalador.

        Args:
            manifest_reader: Instancia de ManifestReader para acceder al manifest
            destino_base: Directorio base donde Sage50BI almacena las plantillas
        """
        self.reader = manifest_reader
        self.destino_base = Path(destino_base)
        self.destino_base.mkdir(parents=True, exist_ok=True)
        self._registro_path = self.destino_base / ".catalogo_instaladas.json"

    def instalar(self, template_id: int) -> bool:
        """
        Descarga + descifra + instala una plantilla.

        Args:
            template_id: ID de la plantilla a instalar

        Returns:
            True si la instalación fue exitosa
        """
        plantilla = self.reader.obtener_plantilla(template_id)
        if not plantilla:
            logger.error(f"Plantilla {template_id} no encontrada en el manifest")
            return False

        # Crear directorio de destino
        nombre_dir = f"{template_id:04d}"
        dir_destino = self.destino_base / nombre_dir
        dir_destino.mkdir(parents=True, exist_ok=True)

        # Descargar archivos
        exito = self.reader.descargar_plantilla(template_id, str(dir_destino))
        if not exito:
            logger.error(f"Error descargando plantilla {template_id}")
            return False

        # Intentar descifrar archivos (si hay módulo de cifrado disponible)
        self._descifrar_archivos(plantilla, dir_destino)

        # Registrar instalación
        self._registrar_instalacion(plantilla)

        logger.info(f"Plantilla {template_id} '{plantilla.get('nombre', '')}' instalada")
        return True

    def instalar_pack(self, pack_id: str) -> list[bool]:
        """
        Instala todas las plantillas de un pack.

        Args:
            pack_id: ID del pack

        Returns:
            Lista de resultados (True/False) por cada plantilla
        """
        packs = self.reader.obtener_packs()
        pack = None
        for p in packs:
            if p.get("id") == pack_id:
                pack = p
                break

        if not pack:
            logger.error(f"Pack '{pack_id}' no encontrado")
            return []

        resultados = []
        for tid in pack.get("plantillas", []):
            resultados.append(self.instalar(tid))
        return resultados

    def estado_instalacion(self, template_id: int) -> str:
        """
        Comprueba el estado de instalación de una plantilla.

        Args:
            template_id: ID de la plantilla

        Returns:
            Estado: 'no_instalada', 'actualizable', 'instalada'
        """
        instaladas = self._cargar_registro()
        instalada = instaladas.get(str(template_id))

        if not instalada:
            return "no_instalada"

        # Comparar versión instalada con la del manifest
        version_instalada = instalada.get("version", "0.0.0")
        plantilla = self.reader.obtener_plantilla(template_id)

        if not plantilla:
            return "instalada"  # No hay manifest para comparar

        version_remota = plantilla.get("version", "0.0.0")
        if version_remota > version_instalada:
            return "actualizable"

        return "instalada"

    def actualizar(self, template_id: int) -> bool:
        """
        Actualiza una plantilla instalada a la última versión.

        Args:
            template_id: ID de la plantilla a actualizar

        Returns:
            True si la actualización fue exitosa
        """
        estado = self.estado_instalacion(template_id)
        if estado == "no_instalada":
            logger.warning(f"Plantilla {template_id} no instalada, no se puede actualizar")
            return False

        # Reinstalar (sobrescribe)
        return self.instalar(template_id)

    def listar_instaladas(self) -> list[dict]:
        """
        Lista todas las plantillas instaladas localmente.

        Returns:
            Lista de diccionarios con datos de plantillas instaladas
        """
        return [{"id": int(k), **v} for k, v in self._cargar_registro().items()]

    # --- Métodos privados ---

    def _descifrar_archivos(self, plantilla: dict, dir_destino: Path) -> None:
        """Intenta descifrar los archivos descargados."""
        try:
            from gestion.cifrado import descifrar_archivo_publico, CifradoError

            archivos = plantilla.get("archivos", {})
            for tipo, info in archivos.items():
                nombre = info.get("nombre", "")
                archivo_cifrado = dir_destino / nombre
                if archivo_cifrado.exists():
                    archivo_descifrado = dir_destino / f"dec_{nombre}"
                    try:
                        descifrar_archivo_publico(archivo_cifrado, archivo_descifrado)
                        # Reemplazar el cifrado con el descifrado
                        archivo_cifrado.unlink()
                        archivo_descifrado.rename(archivo_cifrado)
                    except CifradoError as e:
                        logger.warning(f"No se pudo descifrar {nombre}: {e}")
        except ImportError:
            logger.debug("Módulo de cifrado no disponible, archivos sin descifrar")

    def _registrar_instalacion(self, plantilla: dict) -> None:
        """Registra la instalación en el archivo local."""
        registro = self._cargar_registro()
        registro[str(plantilla.get("id"))] = {
            "nombre": plantilla.get("nombre", ""),
            "version": plantilla.get("version", "0.0.0"),
            "categoria": plantilla.get("categoria", ""),
            "fecha_instalacion": self._fecha_actual(),
        }
        self._guardar_registro(registro)

    def _cargar_registro(self) -> dict:
        """Carga el registro de plantillas instaladas."""
        if not self._registro_path.exists():
            return {}
        try:
            with open(self._registro_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _guardar_registro(self, registro: dict) -> None:
        """Guarda el registro de plantillas instaladas."""
        try:
            with open(self._registro_path, "w", encoding="utf-8") as f:
                json.dump(registro, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"Error guardando registro de instalación: {e}")

    @staticmethod
    def _fecha_actual() -> str:
        """Devuelve la fecha actual en formato ISO."""
        from datetime import datetime

        return datetime.now().isoformat()
