"""
Utilidades de hashing de passwords con bcrypt.

Centraliza la lógica para evitar duplicación entre adaptadores.
"""

import bcrypt

# Bcrypt trunca a 72 bytes; hacemos explícito el límite
BCRYPT_MAX_BYTES = 72

# Hash dummy para mitigar timing attacks
# (se genera una vez al importar el módulo)
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt()).decode("utf-8")


def hash_password(password: str) -> str:
    """
    Hashea una contraseña con bcrypt + salt aleatorio.

    Returns:
        String con formato `$2b$12$<salt><hash>`.
    """
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica una contraseña contra su hash.

    Returns:
        True si coincide, False si no.
    """
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def verify_dummy_password(password: str) -> None:
    """
    Verifica la contraseña contra un hash dummy.

    Uso: mitigar timing attacks cuando el usuario no existe.
    Siempre tarda lo mismo (~250ms) independiente del resultado.

    Returns:
        None (siempre). El resultado se descarta.
    """
    verify_password(password, _DUMMY_HASH)
