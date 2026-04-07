"""
Gestor principal de plantillas Sage50BI.
Orquesta todas las operaciones: crear, actualizar, cifrar, publicar.
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from .schemas import (
    crear_template_json,
    validar_template_json,
    cargar_template_json,
    guardar_template_json,
    get_categoria_por_id,
    es_plantilla_privada,
    CATEGORIAS,
)
from .cifrado import (
    cifrar_archivo_publico,
    cifrar_archivo_privado,
    hash_licencia,
    verificar_cifrado_roundtrip,
)
from .sql_validator import validar_archivo_sql, validar_y_lanzar
from .version_manager import (
    BumpType,
    bump_version,
    actualizar_template_version,
    crear_changelog_entry,
)
from .youtube_generator import generar_youtube_seo
from .pack_generator import obtener_packs_de_plantilla, actualizar_pack, cargar_pack, guardar_pack


class GestorError(Exception):
    """Error en operación del gestor."""

    pass


class Gestor:
    """
    Gestor principal de plantillas Sage50BI.

    Estructura de directorios esperada:
    - repo_root/publicas/         → Plantillas públicas cifradas
    - repo_root/privadas/         → Plantillas privadas cifradas
    - repo_root/privado_mantenimiento/  → Versiones en claro (no se publica)
    - repo_root/packs/            → Definiciones de packs
    - repo_root/docs/             → Fuente MkDocs
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

        # Directorios principales
        self.dir_publicas = self.repo_root / "publicas"
        self.dir_privadas = self.repo_root / "privadas"
        self.dir_mantenimiento = self.repo_root / "privado_mantenimiento"
        self.dir_packs = self.repo_root / "packs"
        self.dir_docs = self.repo_root / "docs"
        self.dir_gestion = self.repo_root / "gestion"

        # Archivos principales
        self.manifest_path = self.repo_root / "manifest-templates.json"
        self.readme_path = self.repo_root / "README.md"

    def _nombre_carpeta(self, template_id: int, nombre: str) -> str:
        """Genera el nombre de carpeta: 'NNNN - Nombre'."""
        return f"{template_id:04d} - {nombre}"

    def _obtener_plantillas_existentes(self) -> dict[int, dict]:
        """
        Escanea las plantillas existentes.

        Returns:
            Dict {id: template_data}
        """
        plantillas = {}

        # Públicas
        if self.dir_publicas.exists():
            for carpeta in self.dir_publicas.iterdir():
                if carpeta.is_dir():
                    template_json = carpeta / "template.json"
                    if template_json.exists():
                        try:
                            data = cargar_template_json(template_json)
                            plantillas[data["id"]] = data
                        except Exception:
                            continue

        # Privadas
        if self.dir_privadas.exists():
            for carpeta in self.dir_privadas.iterdir():
                if carpeta.is_dir():
                    template_json = carpeta / "template.json"
                    if template_json.exists():
                        try:
                            data = cargar_template_json(template_json)
                            plantillas[data["id"]] = data
                        except Exception:
                            continue

        return plantillas

    def _siguiente_id_disponible(self, rango_min: int, rango_max: int) -> int:
        """Encuentra el siguiente ID disponible en un rango."""
        existentes = set(self._obtener_plantillas_existentes().keys())
        for i in range(rango_min, rango_max + 1):
            if i not in existentes:
                return i
        raise GestorError(f"No hay IDs disponibles en el rango {rango_min}-{rango_max}")

    def siguiente_id_publico(self, categoria_inicio: int = 1000) -> int:
        """
        Encuentra el siguiente ID disponible para plantillas públicas.

        Args:
            categoria_inicio: ID inicial de la categoría (1000, 2000, etc.)
        """
        rango_max = categoria_inicio + 999
        return self._siguiente_id_disponible(categoria_inicio, rango_max)

    def siguiente_id_privado(self) -> int:
        """Encuentra el siguiente ID disponible para plantillas privadas (1-999)."""
        return self._siguiente_id_disponible(1, 999)

    def crear_plantilla_publica(
        self,
        template_id: int,
        nombre: str,
        descripcion: str,
        tags: list[str],
        sql_path: Path,
        dashboard_path: Optional[Path] = None,
        preview_path: Optional[Path] = None,
        video_youtube: str = "",
        recomendaciones: list[int] = None,
        packs: list[str] = None,
        on_progress: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Crea una nueva plantilla pública.

        Args:
            template_id: ID de la plantilla (1000+)
            nombre: Nombre de la plantilla
            descripcion: Descripción corta
            tags: Lista de tags
            sql_path: Ruta al archivo SQL en claro
            dashboard_path: Ruta al archivo .py Streamlit (opcional)
            preview_path: Ruta a la imagen preview (opcional)
            video_youtube: URL del video YouTube (opcional)
            recomendaciones: Lista de IDs de plantillas relacionadas
            packs: Lista de IDs de packs a los que añadir
            on_progress: Callback para reportar progreso (mensaje, porcentaje)

        Returns:
            template.json generado
        """

        def progress(msg: str, pct: int):
            if on_progress:
                on_progress(msg, pct)

        progress("Validando parámetros...", 5)

        # Validar que no es rango privado
        if es_plantilla_privada(template_id):
            raise GestorError(
                f"ID {template_id} es de rango privado. Use crear_plantilla_privada()"
            )

        # Validar que no existe
        existentes = self._obtener_plantillas_existentes()
        if template_id in existentes:
            raise GestorError(f"Ya existe plantilla con ID {template_id}")

        # Validar SQL
        progress("Validando SQL...", 10)
        errores_sql = validar_archivo_sql(sql_path)
        if errores_sql:
            raise GestorError("SQL inválido:\n" + "\n".join(errores_sql))

        # Nombres de carpeta
        nombre_carpeta = self._nombre_carpeta(template_id, nombre)
        carpeta_publica = self.dir_publicas / nombre_carpeta
        carpeta_mantenimiento = self.dir_mantenimiento / nombre_carpeta

        # Crear carpetas
        progress("Creando estructura de carpetas...", 15)
        carpeta_publica.mkdir(parents=True, exist_ok=True)
        carpeta_mantenimiento.mkdir(parents=True, exist_ok=True)

        # Copiar SQL a mantenimiento (en claro)
        progress("Copiando archivos a mantenimiento...", 20)
        sql_mant = carpeta_mantenimiento / "template.sql"
        shutil.copy2(sql_path, sql_mant)

        # Cifrar SQL para público
        progress("Cifrando SQL...", 30)
        sql_pub = carpeta_publica / "template.sql"
        hash_sql = cifrar_archivo_publico(sql_path, sql_pub)

        # Dashboard (opcional)
        hash_dashboard = ""
        tiene_dashboard = dashboard_path and dashboard_path.exists()
        if tiene_dashboard:
            progress("Copiando y cifrando dashboard...", 40)
            # Copiar a mantenimiento
            dashboard_mant = carpeta_mantenimiento / "dashboard.py"
            shutil.copy2(dashboard_path, dashboard_mant)
            # Cifrar para público
            dashboard_pub = carpeta_publica / "dashboard.py"
            hash_dashboard = cifrar_archivo_publico(dashboard_path, dashboard_pub)

        # Preview (opcional)
        progress("Copiando preview...", 50)
        if preview_path and preview_path.exists():
            preview_pub = carpeta_publica / "preview.png"
            shutil.copy2(preview_path, preview_pub)

        # Crear template.json
        progress("Generando template.json...", 60)
        template_data = crear_template_json(
            id=template_id,
            nombre=nombre,
            descripcion=descripcion,
            tags=tags,
            tiene_dashboard=tiene_dashboard,
            video_youtube=video_youtube,
            recomendaciones=recomendaciones or [],
            packs=packs or [],
        )

        # Actualizar hashes
        template_data["archivos"]["sql"]["hash_sha256"] = hash_sql
        if tiene_dashboard:
            template_data["archivos"]["dashboard"]["hash_sha256"] = hash_dashboard

        # Guardar template.json
        progress("Guardando template.json...", 70)
        template_json_path = carpeta_publica / "template.json"
        guardar_template_json(template_data, template_json_path)

        # Actualizar packs si se especificaron
        if packs:
            progress("Actualizando packs...", 80)
            for pack_id in packs:
                pack_path = self.dir_packs / f"{pack_id}.json"
                if pack_path.exists():
                    pack_data = cargar_pack(pack_path)
                    pack_data = actualizar_pack(pack_data, template_id, "add")
                    guardar_pack(pack_data, self.dir_packs)

        progress("¡Plantilla creada!", 100)

        return template_data

    def crear_plantilla_privada(
        self,
        template_id: int,
        nombre: str,
        descripcion: str,
        tags: list[str],
        cliente_codigo: str,
        cliente_licencia: str,
        sql_path: Path,
        dashboard_path: Optional[Path] = None,
        preview_path: Optional[Path] = None,
        plantilla_base_id: Optional[int] = None,
        on_progress: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Crea una nueva plantilla privada para un cliente.

        Args:
            template_id: ID de la plantilla (1-999)
            nombre: Nombre de la plantilla
            descripcion: Descripción
            tags: Lista de tags
            cliente_codigo: Código del cliente (ej: CLI-00123)
            cliente_licencia: Licencia del cliente para cifrado
            sql_path: Ruta al SQL en claro
            dashboard_path: Ruta al dashboard (opcional)
            preview_path: Ruta al preview (opcional)
            plantilla_base_id: ID de plantilla pública base (opcional)
            on_progress: Callback de progreso

        Returns:
            template.json generado
        """

        def progress(msg: str, pct: int):
            if on_progress:
                on_progress(msg, pct)

        progress("Validando parámetros...", 5)

        # Validar rango privado
        if not es_plantilla_privada(template_id):
            raise GestorError(f"ID {template_id} no es de rango privado (1-999)")

        # Validar cliente
        if not cliente_codigo or not cliente_licencia:
            raise GestorError("Se requiere código y licencia del cliente")

        # Validar SQL
        progress("Validando SQL...", 10)
        errores_sql = validar_archivo_sql(sql_path)
        if errores_sql:
            raise GestorError("SQL inválido:\n" + "\n".join(errores_sql))

        # Carpetas
        carpeta_privada = self.dir_privadas / cliente_codigo
        carpeta_mantenimiento = self.dir_mantenimiento / cliente_codigo

        progress("Creando estructura de carpetas...", 15)
        carpeta_privada.mkdir(parents=True, exist_ok=True)
        carpeta_mantenimiento.mkdir(parents=True, exist_ok=True)

        # Copiar a mantenimiento (en claro)
        progress("Copiando archivos a mantenimiento...", 20)
        sql_mant = carpeta_mantenimiento / "template.sql"
        shutil.copy2(sql_path, sql_mant)

        # Cifrar con licencia del cliente
        progress("Cifrando SQL con clave del cliente...", 35)
        sql_priv = carpeta_privada / "template.sql"
        hash_sql = cifrar_archivo_privado(sql_path, sql_priv, cliente_licencia)

        # Dashboard (opcional)
        hash_dashboard = ""
        tiene_dashboard = dashboard_path and dashboard_path.exists()
        if tiene_dashboard:
            progress("Copiando y cifrando dashboard...", 50)
            dashboard_mant = carpeta_mantenimiento / "dashboard.py"
            shutil.copy2(dashboard_path, dashboard_mant)
            dashboard_priv = carpeta_privada / "dashboard.py"
            hash_dashboard = cifrar_archivo_privado(
                dashboard_path, dashboard_priv, cliente_licencia
            )

        # Preview
        progress("Copiando preview...", 60)
        if preview_path and preview_path.exists():
            preview_priv = carpeta_privada / "preview.png"
            shutil.copy2(preview_path, preview_priv)

        # Crear template.json
        progress("Generando template.json...", 70)
        template_data = crear_template_json(
            id=template_id,
            nombre=nombre,
            descripcion=descripcion,
            tags=tags,
            tiene_dashboard=tiene_dashboard,
            cliente_codigo=cliente_codigo,
            cliente_clave_hash=hash_licencia(cliente_licencia),
        )

        # Actualizar hashes
        template_data["archivos"]["sql"]["hash_sha256"] = hash_sql
        if tiene_dashboard:
            template_data["archivos"]["dashboard"]["hash_sha256"] = hash_dashboard

        # Guardar
        progress("Guardando template.json...", 85)
        template_json_path = carpeta_privada / "template.json"
        guardar_template_json(template_data, template_json_path)

        progress("¡Plantilla privada creada!", 100)

        return template_data

    def actualizar_plantilla(
        self,
        template_id: int,
        bump_type: BumpType,
        descripcion_cambios: str,
        nuevo_sql_path: Optional[Path] = None,
        nuevo_dashboard_path: Optional[Path] = None,
        cliente_licencia: Optional[str] = None,
        on_progress: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Actualiza una plantilla existente.

        Args:
            template_id: ID de la plantilla a actualizar
            bump_type: Tipo de bump de versión
            descripcion_cambios: Descripción para el changelog
            nuevo_sql_path: Nuevo SQL (opcional)
            nuevo_dashboard_path: Nuevo dashboard (opcional)
            cliente_licencia: Licencia del cliente (requerido para privadas)
            on_progress: Callback de progreso

        Returns:
            template.json actualizado
        """

        def progress(msg: str, pct: int):
            if on_progress:
                on_progress(msg, pct)

        progress("Buscando plantilla...", 5)

        # Encontrar plantilla
        existentes = self._obtener_plantillas_existentes()
        if template_id not in existentes:
            raise GestorError(f"No existe plantilla con ID {template_id}")

        template_data = existentes[template_id]
        es_privada = template_data["tipo"] == "privada"

        # Determinar carpetas
        if es_privada:
            cliente_codigo = template_data["cliente"]["codigo"]
            carpeta_cifrada = self.dir_privadas / cliente_codigo
            carpeta_mant = self.dir_mantenimiento / cliente_codigo
            if not cliente_licencia:
                raise GestorError(
                    "Se requiere licencia del cliente para actualizar plantilla privada"
                )
        else:
            nombre_carpeta = self._nombre_carpeta(template_id, template_data["nombre"])
            carpeta_cifrada = self.dir_publicas / nombre_carpeta
            carpeta_mant = self.dir_mantenimiento / nombre_carpeta

        # Actualizar SQL si se proporciona
        if nuevo_sql_path and nuevo_sql_path.exists():
            progress("Validando nuevo SQL...", 15)
            errores = validar_archivo_sql(nuevo_sql_path)
            if errores:
                raise GestorError("SQL inválido:\n" + "\n".join(errores))

            progress("Actualizando SQL...", 30)
            # Actualizar mantenimiento
            sql_mant = carpeta_mant / "template.sql"
            shutil.copy2(nuevo_sql_path, sql_mant)

            # Cifrar
            sql_cifrado = carpeta_cifrada / "template.sql"
            if es_privada:
                hash_sql = cifrar_archivo_privado(nuevo_sql_path, sql_cifrado, cliente_licencia)
            else:
                hash_sql = cifrar_archivo_publico(nuevo_sql_path, sql_cifrado)

            template_data["archivos"]["sql"]["hash_sha256"] = hash_sql

        # Actualizar dashboard si se proporciona
        if nuevo_dashboard_path and nuevo_dashboard_path.exists():
            progress("Actualizando dashboard...", 50)
            # Actualizar mantenimiento
            dashboard_mant = carpeta_mant / "dashboard.py"
            shutil.copy2(nuevo_dashboard_path, dashboard_mant)

            # Cifrar
            dashboard_cifrado = carpeta_cifrada / "dashboard.py"
            if es_privada:
                hash_dash = cifrar_archivo_privado(
                    nuevo_dashboard_path, dashboard_cifrado, cliente_licencia
                )
            else:
                hash_dash = cifrar_archivo_publico(nuevo_dashboard_path, dashboard_cifrado)

            if "dashboard" not in template_data["archivos"]:
                template_data["archivos"]["dashboard"] = {
                    "nombre": "dashboard.py",
                    "cifrado": True,
                    "opcional": True,
                }
            template_data["archivos"]["dashboard"]["hash_sha256"] = hash_dash

        # Bump versión
        progress("Actualizando versión...", 70)
        template_data = actualizar_template_version(template_data, bump_type, descripcion_cambios)

        # Guardar
        progress("Guardando cambios...", 85)
        template_json_path = carpeta_cifrada / "template.json"
        guardar_template_json(template_data, template_json_path)

        progress("¡Plantilla actualizada!", 100)

        return template_data

    def listar_plantillas(
        self, solo_publicas: bool = False, solo_privadas: bool = False
    ) -> list[dict]:
        """
        Lista todas las plantillas.

        Returns:
            Lista de resúmenes de plantillas
        """
        todas = self._obtener_plantillas_existentes()

        resultado = []
        for tid, data in sorted(todas.items()):
            if solo_publicas and data["tipo"] == "privada":
                continue
            if solo_privadas and data["tipo"] == "publica":
                continue

            resultado.append(
                {
                    "id": data["id"],
                    "nombre": data["nombre"],
                    "version": data["version"],
                    "tipo": data["tipo"],
                    "categoria": data["categoria"]["nombre"],
                    "gratuita": data["gratuita"],
                    "tags": data["tags"][:3],
                    "fecha_actualizacion": data["fecha_actualizacion"],
                }
            )

        return resultado

    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas del repositorio.
        """
        plantillas = self._obtener_plantillas_existentes()

        # Contar por tipo
        publicas = [p for p in plantillas.values() if p["tipo"] == "publica"]
        privadas = [p for p in plantillas.values() if p["tipo"] == "privada"]

        # Contar por categoría
        por_categoria = {}
        for p in publicas:
            cat = p["categoria"]["nombre"]
            por_categoria[cat] = por_categoria.get(cat, 0) + 1

        # Contar packs
        packs = list(self.dir_packs.glob("pack-*.json")) if self.dir_packs.exists() else []

        return {
            "total_plantillas": len(plantillas),
            "publicas": len(publicas),
            "privadas": len(privadas),
            "por_categoria": por_categoria,
            "total_packs": len(packs),
            "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d"),
        }
