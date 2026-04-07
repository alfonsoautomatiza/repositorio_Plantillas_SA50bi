"""
Validador de SQL para plantillas Sage50BI.

REGLA CRÍTICA: Las plantillas contienen SOLO consultas SELECT.
No se permiten sentencias que modifiquen la base de datos o creen objetos.
"""

import re
from pathlib import Path
from typing import Union


class SQLValidationError(Exception):
    """Error de validación SQL."""

    pass


# === SENTENCIAS PROHIBIDAS ===

# Sentencias DDL (Data Definition Language) - modifican estructura
DDL_PROHIBIDAS = [
    r"\bCREATE\s+(TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|TRIGGER|DATABASE|SCHEMA)\b",
    r"\bALTER\s+(TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|TRIGGER|DATABASE|SCHEMA)\b",
    r"\bDROP\s+(TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|TRIGGER|DATABASE|SCHEMA)\b",
    r"\bTRUNCATE\s+TABLE\b",
]

# Sentencias DML que modifican datos (excepto SELECT)
DML_PROHIBIDAS = [
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\s+\w+\s+SET\b",
    r"\bDELETE\s+FROM\b",
    r"\bMERGE\s+INTO\b",
]

# Sentencias DCL (Data Control Language) - permisos
DCL_PROHIBIDAS = [
    r"\bGRANT\b",
    r"\bREVOKE\b",
]

# Sentencias TCL (Transaction Control) - transacciones
TCL_PROHIBIDAS = [
    r"\bCOMMIT\b",
    r"\bROLLBACK\b",
    r"\bSAVEPOINT\b",
]

# Otras sentencias peligrosas
OTRAS_PROHIBIDAS = [
    r"\bEXEC(UTE)?\s*\(",  # Ejecución dinámica
    r"\bsp_\w+",  # Stored procedures de sistema
    r"\bxp_\w+",  # Extended stored procedures
    r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)",  # SQL injection patterns
]

# Compilar todas las prohibidas en una lista
PATRONES_PROHIBIDOS = (
    [(p, "DDL") for p in DDL_PROHIBIDAS]
    + [(p, "DML modificación") for p in DML_PROHIBIDAS]
    + [(p, "DCL") for p in DCL_PROHIBIDAS]
    + [(p, "TCL") for p in TCL_PROHIBIDAS]
    + [(p, "Peligrosa") for p in OTRAS_PROHIBIDAS]
)


def limpiar_sql(sql: str) -> str:
    """
    Limpia el SQL eliminando comentarios y strings literales
    para evitar falsos positivos en la validación.
    """
    # Eliminar comentarios de línea (-- ...)
    sql = re.sub(r"--[^\n]*", " ", sql)

    # Eliminar comentarios de bloque (/* ... */)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)

    # Reemplazar strings literales con placeholder (evitar falsos positivos)
    # Strings con comillas simples
    sql = re.sub(r"'[^']*'", "'LITERAL'", sql)

    # Strings con comillas dobles (algunos dialectos SQL)
    sql = re.sub(r'"[^"]*"', '"LITERAL"', sql)

    return sql


def validar_sql(sql: str, nombre_archivo: str = "SQL") -> list[str]:
    """
    Valida que un SQL contenga solo sentencias SELECT permitidas.

    Args:
        sql: Contenido SQL a validar
        nombre_archivo: Nombre para mensajes de error

    Returns:
        Lista de errores encontrados (vacía si es válido)
    """
    errores = []

    # Limpiar SQL para validación
    sql_limpio = limpiar_sql(sql).upper()

    # Verificar que haya al menos un SELECT
    if not re.search(r"\bSELECT\b", sql_limpio):
        errores.append(f"{nombre_archivo}: No se encontró ninguna sentencia SELECT")

    # Buscar sentencias prohibidas
    for patron, tipo in PATRONES_PROHIBIDOS:
        matches = re.finditer(patron, sql_limpio, re.IGNORECASE)
        for match in matches:
            # Encontrar la línea aproximada
            pos = match.start()
            linea = sql_limpio[:pos].count("\n") + 1
            errores.append(
                f"{nombre_archivo} (línea ~{linea}): Sentencia {tipo} prohibida: '{match.group()}'"
            )

    return errores


def validar_archivo_sql(path: Path) -> list[str]:
    """
    Valida un archivo SQL.

    Args:
        path: Ruta al archivo SQL

    Returns:
        Lista de errores (vacía si es válido)
    """
    if not path.exists():
        return [f"Archivo no encontrado: {path}"]

    try:
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
    except UnicodeDecodeError:
        # Puede ser un archivo ya cifrado
        return [f"{path}: El archivo parece estar cifrado o no es texto válido"]

    return validar_sql(sql, path.name)


def es_sql_valido(sql: str) -> bool:
    """Devuelve True si el SQL es válido (solo SELECT)."""
    return len(validar_sql(sql)) == 0


def validar_y_lanzar(sql: str, nombre: str = "SQL") -> None:
    """
    Valida SQL y lanza excepción si hay errores.

    Raises:
        SQLValidationError: Si el SQL contiene sentencias prohibidas
    """
    errores = validar_sql(sql, nombre)
    if errores:
        raise SQLValidationError(
            "SQL inválido - Solo se permiten consultas SELECT:\n"
            + "\n".join(f"  • {e}" for e in errores)
        )


# === EJEMPLOS DE USO ===


def ejemplo_sql_valido() -> str:
    """Ejemplo de SQL válido para plantillas."""
    return """
    -- Listado de clientes de España
    SELECT 
        c.codigo_cliente,
        c.nombre_fiscal,
        c.cif_nif,
        c.poblacion,
        c.provincia,
        fp.descripcion AS forma_pago,
        c.fecha_alta
    FROM clientes c
    LEFT JOIN formas_pago fp ON c.codigo_forma_pago = fp.codigo
    WHERE c.pais = 'ES'
    ORDER BY c.nombre_fiscal
    """


def ejemplo_sql_invalido() -> str:
    """Ejemplo de SQL inválido (para testing)."""
    return """
    -- Esto NO está permitido
    CREATE VIEW vw_clientes AS SELECT * FROM clientes;
    INSERT INTO log_accesos VALUES (GETDATE(), 'test');
    """


if __name__ == "__main__":
    # Test rápido
    print("=== SQL Válido ===")
    errores = validar_sql(ejemplo_sql_valido())
    print("Errores:", errores if errores else "Ninguno ✅")

    print("\n=== SQL Inválido ===")
    errores = validar_sql(ejemplo_sql_invalido())
    for e in errores:
        print(f"  ❌ {e}")
