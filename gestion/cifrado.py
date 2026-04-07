"""
Módulo de cifrado para plantillas Sage50BI.

Reutiliza el sistema de cifrado Fernet de libwertyconfig.py para plantillas públicas.
Para plantillas privadas, deriva la clave desde la licencia del cliente.
"""

import hashlib
import base64
from pathlib import Path
from typing import Union
from cryptography.fernet import Fernet, InvalidToken


# === CLAVE PÚBLICA (reutiliza FERNET_KEY_COMPILED de libwertyconfig) ===
# Esta clave se embebe en Sage50BI compilado. No es secreto — es barrera de conveniencia.
# IMPORTANTE: Reemplazar con la clave real de libwertyconfig.FERNET_KEY_COMPILED

FERNET_KEY_PUBLIC = (
    b"TU_CLAVE_FERNET_AQUI"  # TODO: Importar de libwertyconfig cuando esté disponible
)


class CifradoError(Exception):
    """Error durante cifrado/descifrado."""

    pass


# === CIFRADO PÚBLICO (plantillas gratuitas) ===


def get_cifrador_publico() -> Fernet:
    """
    Devuelve el cifrador Fernet para plantillas públicas.
    Reutiliza la clave de libwertyconfig.
    """
    try:
        # Intentar importar la clave real de libwertyconfig
        from libwertyconfig import FERNET_KEY_COMPILED

        return Fernet(FERNET_KEY_COMPILED)
    except ImportError:
        # Fallback a la clave embebida
        return Fernet(FERNET_KEY_PUBLIC)


def cifrar_contenido_publico(contenido: bytes) -> bytes:
    """Cifra contenido para una plantilla pública."""
    cifrador = get_cifrador_publico()
    return cifrador.encrypt(contenido)


def descifrar_contenido_publico(contenido_cifrado: bytes) -> bytes:
    """Descifra contenido de una plantilla pública."""
    cifrador = get_cifrador_publico()
    try:
        return cifrador.decrypt(contenido_cifrado)
    except InvalidToken:
        raise CifradoError("No se pudo descifrar: token inválido o clave incorrecta")


def cifrar_archivo_publico(input_path: Path, output_path: Path) -> str:
    """
    Cifra un archivo para publicación pública.

    Args:
        input_path: Ruta al archivo en claro
        output_path: Ruta donde guardar el archivo cifrado

    Returns:
        Hash SHA256 del contenido original (para verificación)
    """
    with open(input_path, "rb") as f:
        contenido = f.read()

    # Calcular hash del original
    hash_sha256 = hashlib.sha256(contenido).hexdigest()

    # Cifrar
    contenido_cifrado = cifrar_contenido_publico(contenido)

    # Guardar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(contenido_cifrado)

    return hash_sha256


def descifrar_archivo_publico(input_path: Path, output_path: Path) -> str:
    """
    Descifra un archivo público.

    Args:
        input_path: Ruta al archivo cifrado
        output_path: Ruta donde guardar el archivo descifrado

    Returns:
        Hash SHA256 del contenido descifrado
    """
    with open(input_path, "rb") as f:
        contenido_cifrado = f.read()

    contenido = descifrar_contenido_publico(contenido_cifrado)

    # Calcular hash
    hash_sha256 = hashlib.sha256(contenido).hexdigest()

    # Guardar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(contenido)

    return hash_sha256


# === CIFRADO PRIVADO (plantillas por cliente) ===


def derivar_clave_desde_licencia(licencia_cliente: str) -> bytes:
    """
    Deriva una clave Fernet válida desde la licencia del cliente.

    La licencia se hashea con SHA256 y se codifica en base64 URL-safe
    para crear una clave Fernet de 32 bytes.
    """
    if not licencia_cliente:
        raise CifradoError("Licencia de cliente vacía")

    digest = hashlib.sha256(licencia_cliente.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_cifrador_privado(licencia_cliente: str) -> Fernet:
    """Devuelve un cifrador Fernet para la licencia del cliente."""
    clave = derivar_clave_desde_licencia(licencia_cliente)
    return Fernet(clave)


def hash_licencia(licencia_cliente: str) -> str:
    """
    Calcula el hash SHA256 de la licencia para guardar en template.json.
    Esto permite verificar la licencia sin almacenar la clave real.
    """
    return hashlib.sha256(licencia_cliente.encode("utf-8")).hexdigest()


def cifrar_contenido_privado(contenido: bytes, licencia_cliente: str) -> bytes:
    """Cifra contenido para una plantilla privada."""
    cifrador = get_cifrador_privado(licencia_cliente)
    return cifrador.encrypt(contenido)


def descifrar_contenido_privado(contenido_cifrado: bytes, licencia_cliente: str) -> bytes:
    """Descifra contenido de una plantilla privada."""
    cifrador = get_cifrador_privado(licencia_cliente)
    try:
        return cifrador.decrypt(contenido_cifrado)
    except InvalidToken:
        raise CifradoError("No se pudo descifrar: licencia incorrecta o archivo corrupto")


def cifrar_archivo_privado(input_path: Path, output_path: Path, licencia_cliente: str) -> str:
    """
    Cifra un archivo para un cliente específico.

    Args:
        input_path: Ruta al archivo en claro
        output_path: Ruta donde guardar el archivo cifrado
        licencia_cliente: Licencia del cliente para derivar la clave

    Returns:
        Hash SHA256 del contenido original
    """
    with open(input_path, "rb") as f:
        contenido = f.read()

    hash_sha256 = hashlib.sha256(contenido).hexdigest()
    contenido_cifrado = cifrar_contenido_privado(contenido, licencia_cliente)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(contenido_cifrado)

    return hash_sha256


def descifrar_archivo_privado(input_path: Path, output_path: Path, licencia_cliente: str) -> str:
    """
    Descifra un archivo privado con la licencia del cliente.

    Args:
        input_path: Ruta al archivo cifrado
        output_path: Ruta donde guardar el archivo descifrado
        licencia_cliente: Licencia del cliente

    Returns:
        Hash SHA256 del contenido descifrado
    """
    with open(input_path, "rb") as f:
        contenido_cifrado = f.read()

    contenido = descifrar_contenido_privado(contenido_cifrado, licencia_cliente)
    hash_sha256 = hashlib.sha256(contenido).hexdigest()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(contenido)

    return hash_sha256


# === UTILIDADES ===


def verificar_integridad(contenido: bytes, hash_esperado: str) -> bool:
    """Verifica que el contenido coincida con el hash esperado."""
    hash_calculado = hashlib.sha256(contenido).hexdigest()
    return hash_calculado == hash_esperado


def verificar_cifrado_roundtrip(
    contenido_original: bytes, es_privado: bool = False, licencia: str = ""
) -> bool:
    """
    Verifica que cifrar → descifrar devuelve el contenido original.
    Útil para validación antes de publicar.
    """
    try:
        if es_privado:
            cifrado = cifrar_contenido_privado(contenido_original, licencia)
            descifrado = descifrar_contenido_privado(cifrado, licencia)
        else:
            cifrado = cifrar_contenido_publico(contenido_original)
            descifrado = descifrar_contenido_publico(cifrado)

        return descifrado == contenido_original
    except Exception:
        return False
