"""
Integración Sage50BI — Módulo de actualización automática de plantillas.

Este módulo es el que Sage50BI importa para:
1. Comprobar actualizaciones de plantillas desde el repositorio remoto
2. Descargar e instalar plantillas nuevas o actualizadas
3. Gestionar plantillas privadas con licencia de cliente

Uso básico:
    from integracion import ActualizadorPlantillas

    actualizador = ActualizadorPlantillas(
        plantillas_dir="C:/Sage50BI/Plantillas"
    )
    estado = actualizador.comprobar_actualizaciones()
"""

from .actualizador import ActualizadorPlantillas
from .descargador import Descargador
from .registro import RegistroLocal

__version__ = "1.0.0"
__all__ = [
    "ActualizadorPlantillas",
    "Descargador",
    "RegistroLocal",
]
