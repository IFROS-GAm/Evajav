"""Hash de contraseñas con PBKDF2-SHA256 (solo librería estándar, sin dependencias)."""
import hashlib
import hmac
import secrets
from base64 import b64decode, b64encode

ITERACIONES = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${b64encode(salt).decode()}${b64encode(dk).decode()}"


def verify_password(password: str, guardado: str) -> bool:
    try:
        algoritmo, iteraciones, salt, dk = guardado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculado = hashlib.pbkdf2_hmac("sha256", password.encode(), b64decode(salt), int(iteraciones))
        return hmac.compare_digest(calculado, b64decode(dk))
    except (ValueError, AttributeError, TypeError):
        return False


def password_debil(password: str) -> str | None:
    """Devuelve el motivo si la contraseña no sirve, o None si está bien."""
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if password.isdigit() or password.isalpha():
        return "Combina letras y números."
    return None
