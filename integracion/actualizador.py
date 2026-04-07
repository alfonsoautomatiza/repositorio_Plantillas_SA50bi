"""
Actualizador principal de plantillas Sage50BI.

Este es el punto de entrada que Sage50BI invoca para:
1. Comprobar si hay plantillas nuevas o actualizadas
2. Descargarlas e instalarlas
3. Gestionar plantillas privadas con licencia de cliente
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .descargador import Descargador
from .registro import RegistroLocal
from gestion.version_manager import version_es_mayor

# Importar cifrado de forma segura — puede no estar disponible en tests
try:
    from gestion.cifrado import descifrar_contenido_privado, CifradoError

    _CIFRADO_DISPONIBLE = True
except ImportError:
    _CIFRADO_DISPONIBLE = False

    class _CifradoError(Exception):
        pass

    descifrar_contenido_privado = None
    CifradoError = _CifradoError


# Streamlit — solo disponible dentro de Sage50BI
try:
    import streamlit as st
except ImportError:
    st = None


MANIFEST_URL_DEFAULT = "https://wertymsd.github.io/repositorio_Sage50bi/manifest-templates.json"


class ActualizadorPlantillas:
    """Handles automatic template updates for Sage50BI.

    This is the main entry point that Sage50BI calls to:
    1. Check for new/updated templates
    2. Download and install them
    3. Handle private templates with client license
    """

    def __init__(
        self,
        manifest_url: Optional[str] = None,
        plantillas_dir: Optional[str] = None,
        cliente_id: Optional[str] = None,
        licencia_key: Optional[str] = None,
    ):
        """
        Args:
            manifest_url: URL al manifest-templates.json.
                          Default: https://wertymsd.github.io/repositorio_Sage50bi/manifest-templates.json
            plantillas_dir: Directorio local donde Sage50BI almacena plantillas instaladas.
            cliente_id: ID de cliente para plantillas privadas (ej: 'CLI-00123').
            licencia_key: Clave de licencia para descifrar plantillas privadas.
        """
        self.manifest_url = manifest_url or MANIFEST_URL_DEFAULT
        self.cliente_id = cliente_id
        self.licencia_key = licencia_key

        # Directorio de plantillas — por defecto relativo al usuario
        if plantillas_dir:
            self.plantillas_dir = Path(plantillas_dir)
        else:
            self.plantillas_dir = Path.home() / "Sage50BI" / "Plantillas"

        self.plantillas_dir.mkdir(parents=True, exist_ok=True)

        # Componentes internos
        self.registro = RegistroLocal(str(self.plantillas_dir))
        self.descargador = Descargador(cache_dir=str(self.plantillas_dir / ".cache"))

        # Cache del manifest remoto
        self._manifest_cache: Optional[dict] = None
        self._manifest_cache_time: Optional[datetime] = None

    def _obtener_manifest(self, forzar: bool = False) -> Optional[dict]:
        """Obtiene el manifest remoto (con caché en memoria)."""
        if not forzar and self._manifest_cache is not None and self._manifest_cache_time:
            # Cache de 5 minutos
            delta = (datetime.now() - self._manifest_cache_time).total_seconds()
            if delta < 300:
                return self._manifest_cache

        manifest = self.descargador.descargar_manifest(self.manifest_url)
        if manifest:
            self._manifest_cache = manifest
            self._manifest_cache_time = datetime.now()
        return manifest

    def _obtener_plantilla_manifest(
        self, template_id: int, manifest: Optional[dict] = None
    ) -> Optional[dict]:
        """Busca una plantilla en el manifest por ID."""
        if manifest is None:
            manifest = self._manifest_cache
        if manifest is None:
            return None

        for p in manifest.get("plantillas", []):
            if p.get("id") == template_id:
                return p
        return None

    def _directorio_plantilla(self, template_id: int, nombre: str) -> Path:
        """Devuelve la ruta local para una plantilla."""
        # Limpiar nombre para usar como directorio
        nombre_limpio = nombre.replace("/", "-").replace("\\", "-").strip()
        return self.plantillas_dir / f"{template_id} - {nombre_limpio}"

    def comprobar_actualizaciones(self, manifest: Optional[dict] = None) -> dict:
        """Comprueba si hay actualizaciones disponibles.

        Args:
            manifest: Manifest opcional (para testing). Si es None, se descarga del remoto.

        Returns:
            {
                'nuevas': [lista de plantillas no instaladas],
                'actualizables': [lista de plantillas con versión más reciente],
                'instaladas': [lista de plantillas ya instaladas y actualizadas],
                'privadas': [lista de plantillas privadas para este cliente],
                'total_disponibles': int,
                'ultima_comprobacion': str con datetime
            }
        """
        if manifest is None:
            manifest = self._obtener_manifest(forzar=True)

        if manifest is None:
            return {
                "nuevas": [],
                "actualizables": [],
                "instaladas": [],
                "privadas": [],
                "total_disponibles": 0,
                "ultima_comprobacion": datetime.now().isoformat(),
                "error": "No se pudo obtener el manifest remoto",
            }

        nuevas = []
        actualizables = []
        instaladas = []
        privadas = []

        for plantilla in manifest.get("plantillas", []):
            tid = plantilla.get("id")
            version_remota = plantilla.get("version", "0.0.0")
            tipo = plantilla.get("tipo", "publica")

            # Plantillas privadas
            if tipo == "privada":
                # Solo interesan si son para este cliente
                cliente_plantilla = plantilla.get("cliente_id", "")
                if self.cliente_id and cliente_plantilla == self.cliente_id:
                    privadas.append(plantilla)
                continue

            # Plantillas públicas
            if not self.registro.esta_instalada(tid):
                nuevas.append(plantilla)
            elif self.registro.necesita_actualizacion(tid, version_remota):
                actualizables.append(plantilla)
            else:
                instaladas.append(plantilla)

        total = len(nuevas) + len(actualizables) + len(privadas)

        return {
            "nuevas": nuevas,
            "actualizables": actualizables,
            "instaladas": instaladas,
            "privadas": privadas,
            "total_disponibles": total,
            "ultima_comprobacion": datetime.now().isoformat(),
        }

    def instalar_plantilla(self, template_id: int) -> dict:
        """Instala una plantilla individual.

        Returns:
            {'exito': bool, 'template_id': int, 'version': str, 'mensaje': str}
        """
        manifest = self._obtener_manifest() or self._manifest_cache
        if manifest is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": "No se pudo obtener el manifest remoto",
            }

        plantilla = self._obtener_plantilla_manifest(template_id, manifest)
        if plantilla is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": f"Plantilla {template_id} no encontrada en el manifest",
            }

        nombre = plantilla.get("nombre", f"Plantilla {template_id}")
        version = plantilla.get("version", "0.0.0")
        categoria = plantilla.get("categoria", "Sin categoría")
        url_base = plantilla.get("url_base", "")
        archivos_manifest = plantilla.get("archivos", {})

        # Directorio destino
        dest_dir = self._directorio_plantilla(template_id, nombre)

        # Descargar archivos usando la url_base del manifest
        if url_base:
            resultado = self.descargador.descargar_plantilla_desde_url(
                url_base, archivos_manifest, str(dest_dir)
            )
        else:
            resultado = self.descargador.descargar_plantilla(template_id, nombre, str(dest_dir))

        if resultado["errores"]:
            return {
                "exito": False,
                "template_id": template_id,
                "version": version,
                "mensaje": f"Errores al descargar: {'; '.join(resultado['errores'])}",
            }

        # Registrar localmente
        self.registro.registrar(template_id, version, nombre, categoria)

        return {
            "exito": True,
            "template_id": template_id,
            "version": version,
            "mensaje": f"Plantilla '{nombre}' v{version} instalada correctamente",
        }

    def instalar_todas_nuevas(self) -> list[dict]:
        """Instala todas las plantillas nuevas.

        Returns:
            Lista de resultados por plantilla.
        """
        estado = self.comprobar_actualizaciones()
        resultados = []

        for plantilla in estado["nuevas"]:
            tid = plantilla.get("id")
            if tid is not None:
                resultados.append(self.instalar_plantilla(tid))

        return resultados

    def actualizar_plantilla(self, template_id: int) -> dict:
        """Actualiza una plantilla específica a la última versión.

        Returns:
            {'exito': bool, 'template_id': int, 'version': str, 'mensaje': str}
        """
        manifest = self._obtener_manifest() or self._manifest_cache
        if manifest is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": "No se pudo obtener el manifest remoto",
            }

        plantilla = self._obtener_plantilla_manifest(template_id, manifest)
        if plantilla is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": f"Plantilla {template_id} no encontrada en el manifest",
            }

        version_remota = plantilla.get("version", "0.0.0")
        nombre = plantilla.get("nombre", f"Plantilla {template_id}")

        # Verificar que realmente necesita actualización
        if not self.registro.necesita_actualizacion(template_id, version_remota):
            version_local = self.registro.obtener_version_instalada(template_id)
            return {
                "exito": False,
                "template_id": template_id,
                "version": version_local or "",
                "mensaje": f"La plantilla '{nombre}' ya está actualizada (v{version_local})",
            }

        # Eliminar versión anterior
        dest_dir = self._directorio_plantilla(template_id, nombre)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        # Re-instalar (que descarga y registra)
        return self.instalar_plantilla(template_id)

    def actualizar_todas(self) -> list[dict]:
        """Actualiza todas las plantillas que tienen versión más reciente.

        Returns:
            Lista de resultados por plantilla.
        """
        estado = self.comprobar_actualizaciones()
        resultados = []

        for plantilla in estado["actualizables"]:
            tid = plantilla.get("id")
            if tid is not None:
                resultados.append(self.actualizar_plantilla(tid))

        return resultados

    def instalar_plantilla_privada(self, template_id: int) -> dict:
        """Instala una plantilla privada usando la licencia del cliente.

        Returns:
            {'exito': bool, 'template_id': int, 'version': str, 'mensaje': str}
        """
        if not self.cliente_id or not self.licencia_key:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": "Se requiere cliente_id y licencia_key para plantillas privadas",
            }

        if not _CIFRADO_DISPONIBLE:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": "Módulo de cifrado no disponible",
            }

        manifest = self._obtener_manifest()
        if manifest is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": "No se pudo obtener el manifest remoto",
            }

        # Buscar en la sección de privadas (requiere manifest con privadas)
        plantilla = None
        for p in manifest.get("plantillas", []):
            if (
                p.get("id") == template_id
                and p.get("tipo") == "privada"
                and p.get("cliente_id") == self.cliente_id
            ):
                plantilla = p
                break

        if plantilla is None:
            return {
                "exito": False,
                "template_id": template_id,
                "version": "",
                "mensaje": f"Plantilla privada {template_id} no encontrada para este cliente",
            }

        nombre = plantilla.get("nombre", f"Privada {template_id}")
        version = plantilla.get("version", "0.0.0")
        categoria = plantilla.get("categoria", "Sin categoría")
        url_base = plantilla.get("url_base", "")

        # Descargar archivo cifrado
        archivos_manifest = plantilla.get("archivos", {})
        dest_dir = self._directorio_plantilla(template_id, nombre)
        dest_dir.mkdir(parents=True, exist_ok=True)

        resultado = self.descargador.descargar_plantilla_desde_url(
            url_base, archivos_manifest, str(dest_dir)
        )

        if resultado["errores"]:
            return {
                "exito": False,
                "template_id": template_id,
                "version": version,
                "mensaje": f"Errores al descargar: {'; '.join(resultado['errores'])}",
            }

        # Descifrar archivos SQL con la licencia del cliente
        try:
            for archivo in resultado["archivos"]:
                if archivo.endswith(".sql"):
                    ruta_cifrada = dest_dir / archivo
                    contenido_cifrado = ruta_cifrada.read_bytes()
                    contenido_claro = descifrar_contenido_privado(
                        contenido_cifrado, self.licencia_key
                    )
                    ruta_cifrada.write_bytes(contenido_claro)
        except CifradoError as e:
            return {
                "exito": False,
                "template_id": template_id,
                "version": version,
                "mensaje": f"Error al descifrar: {e}",
            }

        # Registrar
        self.registro.registrar(template_id, version, nombre, categoria, es_privada=True)

        return {
            "exito": True,
            "template_id": template_id,
            "version": version,
            "mensaje": f"Plantilla privada '{nombre}' v{version} instalada correctamente",
        }

    def desinstalar_plantilla(self, template_id: int) -> bool:
        """Elimina una plantilla instalada.

        Returns:
            True si se eliminó correctamente, False si no estaba instalada.
        """
        if not self.registro.esta_instalada(template_id):
            return False

        # Obtener info para encontrar el directorio
        instaladas = self.registro.listar_instaladas()
        info = None
        for p in instaladas:
            if p.get("id") == template_id:
                info = p
                break

        if info:
            nombre = info.get("nombre", "")
            dest_dir = self._directorio_plantilla(template_id, nombre)
            if dest_dir.exists():
                shutil.rmtree(dest_dir)

        self.registro.desregistrar(template_id)
        return True

    def obtener_estado(self) -> dict:
        """Obtiene un resumen del estado actual para la UI de Sage50BI.

        Returns:
            {
                'total_instaladas': int,
                'plantillas_instaladas': list,
                'directorio_plantillas': str,
                'cliente_id': str or None,
                'ultima_comprobacion': str or None,
            }
        """
        estado_registro = self.registro.exportar_estado()
        return {
            "total_instaladas": estado_registro["total_instaladas"],
            "plantillas_instaladas": estado_registro["plantillas"],
            "directorio_plantillas": str(self.plantillas_dir),
            "cliente_id": self.cliente_id,
            "ultima_comprobacion": estado_registro.get("fecha_actualizacion", ""),
        }
