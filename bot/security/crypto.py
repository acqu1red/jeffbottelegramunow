import base64
import hashlib
import hmac
from cryptography.fernet import Fernet


def get_fernet(key: str) -> Fernet:
    return Fernet(key.encode("utf-8"))


def encrypt_text(key: str, value: str | None) -> str | None:
    if value is None:
        return None
    return get_fernet(key).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(key: str, value: str | None) -> str | None:
    if value is None:
        return None
    return get_fernet(key).decrypt(value.encode("utf-8")).decode("utf-8")


def telegram_id_hash(secret: str, telegram_id: int) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        str(telegram_id).encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")
