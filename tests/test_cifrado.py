"""Tests para gestion/cifrado.py"""

import tempfile
from pathlib import Path

from gestion.cifrado import (
    cifrar_contenido_publico,
    descifrar_contenido_publico,
    cifrar_archivo_publico,
    descifrar_archivo_publico,
    cifrar_contenido_privado,
    descifrar_contenido_privado,
    cifrar_archivo_privado,
    descifrar_archivo_privado,
    hash_licencia,
    verificar_integridad,
    verificar_cifrado_roundtrip,
    derivar_clave_desde_licencia,
    CifradoError,
)


CONTENIDO = b"SELECT * FROM clientes WHERE pais = 'ES'"


# === Cifrado publico ===


def test_cifrar_descifrar_publico():
    cifrado = cifrar_contenido_publico(CONTENIDO)
    descifrado = descifrar_contenido_publico(cifrado)
    assert descifrado == CONTENIDO


def test_cifrado_publico_no_igual_original():
    cifrado = cifrar_contenido_publico(CONTENIDO)
    assert cifrado != CONTENIDO


def test_archivo_publico(tmp_path):
    in_file = tmp_path / "original.sql"
    in_file.write_bytes(CONTENIDO)
    out_file = tmp_path / "cifrado.sql"
    result_file = tmp_path / "descifrado.sql"

    hash_orig = cifrar_archivo_publico(in_file, out_file)
    assert out_file.exists()
    assert hash_orig != ""

    hash_dec = descifrar_archivo_publico(out_file, result_file)
    assert result_file.read_bytes() == CONTENIDO
    assert hash_orig == hash_dec


def test_descifrar_token_invalido():
    try:
        descifrar_contenido_publico(b"esto_no_es_fernet")
        assert False, "Debería lanzar CifradoError"
    except CifradoError:
        pass  # OK


# === Cifrado privado ===


def test_cifrar_descifrar_privado():
    licencia = "LIC-TEST-12345"
    cifrado = cifrar_contenido_privado(CONTENIDO, licencia)
    descifrado = descifrar_contenido_privado(cifrado, licencia)
    assert descifrado == CONTENIDO


def test_privado_licencia_incorrecta():
    cifrado = cifrar_contenido_privado(CONTENIDO, "licencia_correcta")
    try:
        descifrar_contenido_privado(cifrado, "licencia_incorrecta")
        assert False, "Debería lanzar CifradoError"
    except CifradoError:
        pass  # OK


def test_archivo_privado(tmp_path):
    in_file = tmp_path / "priv.sql"
    in_file.write_bytes(CONTENIDO)
    out_file = tmp_path / "priv_cifrado.sql"
    result_file = tmp_path / "priv_desc.sql"
    licencia = "CLIENTE-LIC-001"

    hash_orig = cifrar_archivo_privado(in_file, out_file, licencia)
    hash_dec = descifrar_archivo_privado(out_file, result_file, licencia)
    assert result_file.read_bytes() == CONTENIDO
    assert hash_orig == hash_dec


# === Utilidades ===


def test_hash_licencia():
    h1 = hash_licencia("mi_licencia")
    h2 = hash_licencia("mi_licencia")
    h3 = hash_licencia("otra_licencia")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA256 hex


def test_verificar_integridad():
    contenido = b"datos"
    h = hash_licencia  # SHA256 hex length
    import hashlib

    hash_correcto = hashlib.sha256(contenido).hexdigest()
    assert verificar_integridad(contenido, hash_correcto) is True
    assert verificar_integridad(contenido, "hash_incorrecto") is False


def test_roundtrip_publico():
    assert verificar_cifrado_roundtrip(CONTENIDO) is True


def test_roundtrip_privado():
    assert verificar_cifrado_roundtrip(CONTENIDO, es_privado=True, licencia="test") is True


def test_derivacion_clave():
    clave = derivar_clave_desde_licencia("test_licencia")
    assert isinstance(clave, bytes)
    assert len(clave) == 44  # base64 de 32 bytes
