import hashlib
import secrets

def generate_password_hash(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def generate_auth_token(length: int = 32) -> str:
    """
    Args:
    length (int): Длина токена в байтах. По умолчанию 32 байта,
                  что приводит к строке из 43 URL-safe символов.

    Returns:
        str: Строка с уникальным токеном.
    """
    return secrets.token_urlsafe(length)