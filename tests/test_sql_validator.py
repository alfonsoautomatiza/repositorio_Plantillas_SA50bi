"""Tests para gestion/sql_validator.py"""

import tempfile
from pathlib import Path

from gestion.sql_validator import (
    validar_sql,
    validar_archivo_sql,
    es_sql_valido,
    validar_y_lanzar,
    SQLValidationError,
)


# === SQL valido ===

SQL_SELECT_SIMPLE = "SELECT * FROM clientes WHERE pais = 'ES' ORDER BY nombre"

SQL_SELECT_JOIN = """
SELECT c.codigo, c.nombre, fp.descripcion AS forma_pago
FROM clientes c
LEFT JOIN formas_pago fp ON c.codigo_fp = fp.codigo
WHERE c.pais = 'ES'
"""

SQL_CON_COMENTARIOS = """
-- Listado de clientes
SELECT codigo, nombre FROM clientes
/* Solo activos */
WHERE activo = 1
"""


def test_sql_valido_simple():
    assert validar_sql(SQL_SELECT_SIMPLE) == []


def test_sql_valido_join():
    assert validar_sql(SQL_SELECT_JOIN) == []


def test_sql_valido_comentarios():
    assert validar_sql(SQL_CON_COMENTARIOS) == []


def test_es_sql_valido():
    assert es_sql_valido("SELECT 1") is True
    assert es_sql_valido("DROP TABLE clientes") is False


# === SQL invalido: DDL ===

SQL_CREATE_VIEW = "CREATE VIEW vw_clientes AS SELECT * FROM clientes"
SQL_CREATE_TABLE = "CREATE TABLE temp (id INT)"
SQL_ALTER = "ALTER TABLE clientes ADD COLUMN email VARCHAR(100)"
SQL_DROP = "DROP TABLE clientes"


def test_create_view_prohibido():
    errores = validar_sql(SQL_CREATE_VIEW)
    assert len(errores) > 0
    assert any("DDL" in e for e in errores)


def test_create_table_prohibido():
    errores = validar_sql(SQL_CREATE_TABLE)
    assert len(errores) > 0


def test_alter_prohibido():
    errores = validar_sql(SQL_ALTER)
    assert len(errores) > 0


def test_drop_prohibido():
    errores = validar_sql(SQL_DROP)
    assert len(errores) > 0


# === SQL invalido: DML modificacion ===

SQL_INSERT = "INSERT INTO log VALUES (1, 'test')"
SQL_UPDATE = "UPDATE clientes SET nombre = 'X' WHERE id = 1"
SQL_DELETE = "DELETE FROM temp WHERE id = 1"


def test_insert_prohibido():
    errores = validar_sql(SQL_INSERT)
    assert len(errores) > 0


def test_update_prohibido():
    errores = validar_sql(SQL_UPDATE)
    assert len(errores) > 0


def test_delete_prohibido():
    errores = validar_sql(SQL_DELETE)
    assert len(errores) > 0


# === SQL sin SELECT ===


def test_sin_select():
    errores = validar_sql("SET @var = 1")
    assert any("SELECT" in e for e in errores)


# === Validar archivo ===


def test_validar_archivo(tmp_path):
    sql_file = tmp_path / "test.sql"
    sql_file.write_text("SELECT * FROM clientes", encoding="utf-8")
    assert validar_archivo_sql(sql_file) == []


def test_validar_archivo_inexistente():
    errores = validar_archivo_sql(Path("/no/existe.sql"))
    assert len(errores) > 0


def test_validar_y_lanzar_ok():
    validar_y_lanzar("SELECT 1")  # No lanza


def test_validar_y_lanzar_error():
    try:
        validar_y_lanzar("DROP TABLE clientes")
        assert False, "Debería lanzar SQLValidationError"
    except SQLValidationError:
        pass  # OK
