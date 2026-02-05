from datetime import datetime

from bot.config import get_settings
from bot.db.models import User
from bot.db.repository import get_user_by_hash, upsert_user
from bot.security.crypto import encrypt_text, telegram_id_hash


def get_or_create_user(telegram_id: int, username: str | None) -> User:
    settings = get_settings()
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    existing = get_user_by_hash(digest)
    if existing:
        return existing
    encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id))
    encrypted_username = (
        encrypt_text(settings.fernet_key, username)
        if username
        else None
    )
    user = User(
        telegram_id=encrypted_id,
        telegram_id_hash=digest,
        username=encrypted_username,
        subscription_end=None,
        tariff=None,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    return upsert_user(user)
