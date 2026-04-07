"""
Registro local de plantillas instaladas.

Mantiene un JSON con las plantillas instaladas, sus versiones
y metadatos para comparar con el manifest remoto.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from gestion.version_manager import version_es_mayor, comparar_versiones


class RegistroLocal:
    """Tracks which templates are installed locally and their versions.

    Uses a JSON file in the Sage50BI templates directory.
    """

    ARCHIVO_REGISTRO = "registro_plantillas.json"

    def __init__(self, plantillas_dir: str):
        """
        Args:
            plantillas_dir: Directorio local donde Sage50BI almacena las plantillas.
        """
        self.plantillas_dir = Path(plantillas_dir)
        self.plantillas_dir.mkdir(parents=True, exist_ok=True)
        self.archivo_registro = self.plantillas_dir / self.ARCHIVO_REGISTRO
        self._datos = self._cargar()

    def _cargar(self) -> dict:
        """Carga el registro desde disco. Si no existe o está corrupto, crea uno vacío."""
        if not self.archivo_registro.exists():
            return self._registro_vacio()

        try:
            with open(self.archivo_registro, "r", encoding="utf-8") as f:
                datos = json.load(f)
            # Validar estructura mínima
            if "plantillas" not in datos or not isinstance(datos["plantillas"], list):
                return self._registro_vacio()
            return datos
        except (json.JSONDecodeError, OSError):
            # Registro corrupto — empezar limpio
            return self._registro_vacio()

    def _registro_vacio(self) -> dict:
        """Devuelve la estructura de un registro vacío."""
        return {
            "version": "1.0.0",
            "fecha_creacion": datetime.now().isoformat(),
            "plantillas": [],
        }

    def _guardar(self) -> None:
        """Persiste el registro a disco."""
        self._datos["fecha_actualizacion"] = datetime.now().isoformat()
        with open(self.archivo_registro, "w", encoding="utf-8") as f:
            json.dump(self._datos, f, indent=2, ensure_ascii=False)

    def _buscar_indice(self, template_id: int) -> int:
        """Busca el índice de una plantilla por ID. Devuelve -1 si no existe."""
        for i, p in enumerate(self._datos["plantillas"]):
            if p.get("id") == template_id:
                return i
        return -1

    def registrar(
        self,
        template_id: int,
        version: str,
        nombre: str,
        categoria: str,
        es_privada: bool = False,
    ) -> None:
        """Registra una plantilla instalada.

        Si ya existe con el mismo ID, actualiza la versión y datos.
        """
        idx = self._buscar_indice(template_id)
        entrada = {
            "id": template_id,
            "version": version,
            "nombre": nombre,
            "categoria": categoria,
            "es_privada": es_privada,
            "fecha_instalacion": datetime.now().isoformat(),
        }

        if idx >= 0:
            # Actualizar existente — mantener fecha_instalacion original
            entrada["fecha_instalacion"] = self._datos["plantillas"][idx].get(
                "fecha_instalacion", entrada["fecha_instalacion"]
            )
            self._datos["plantillas"][idx] = entrada
        else:
            self._datos["plantillas"].append(entrada)

        self._guardar()

    def desregistrar(self, template_id: int) -> None:
        """Elimina una plantilla del registro."""
        idx = self._buscar_indice(template_id)
        if idx >= 0:
            self._datos["plantillas"].pop(idx)
            self._guardar()

    def obtener_version_instalada(self, template_id: int) -> Optional[str]:
        """Devuelve la versión instalada de una plantilla, o None si no está."""
        idx = self._buscar_indice(template_id)
        if idx >= 0:
            return self._datos["plantillas"][idx].get("version")
        return None

    def listar_instaladas(self) -> list[dict]:
        """Lista todas las plantillas instaladas con su información."""
        return list(self._datos["plantillas"])

    def esta_instalada(self, template_id: int) -> bool:
        """Comprueba si una plantilla está instalada."""
        return self._buscar_indice(template_id) >= 0

    def necesita_actualizacion(self, template_id: int, version_remota: str) -> bool:
        """Compara la versión instalada con la remota usando semver.

        Returns:
            True si la versión remota es mayor que la instalada.
            False si no está instalada o ya está actualizada.
        """
        version_local = self.obtener_version_instalada(template_id)
        if version_local is None:
            return False
        return version_es_mayor(version_remota, version_local)

    def exportar_estado(self) -> dict:
        """Exporta el estado completo del registro como diccionario."""
        return {
            "version_registro": self._datos.get("version", "1.0.0"),
            "fecha_actualizacion": self._datos.get("fecha_actualizacion", ""),
            "total_instaladas": len(self._datos["plantillas"]),
            "plantillas": self.listar_instaladas(),
        }
