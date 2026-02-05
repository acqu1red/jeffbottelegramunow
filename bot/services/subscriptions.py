import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta

from bot.config import get_settings
from bot.db.models import SecurityLog, User
from bot.db.repository import add_security_log, get_user_by_hash, update_user_subscription
from bot.security.crypto import encrypt_text, telegram_id_hash
from bot.services.tariffs import Tariff, get_tariff


REMINDER_DAYS = [10, 5, 3, 1]


@dataclass(frozen=True)
class SubscriptionUpdate:
    user: User
    new_end: datetime
    tariff: Tariff


def add_months(start: datetime, months: int) -> datetime:
    year = start.year + (start.month - 1 + months) // 12
    month = (start.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(start.day, last_day)
    return start.replace(year=year, month=month, day=day)


def compute_new_end(current_end: datetime | None, months: int) -> datetime:
    if current_end and current_end > datetime.utcnow():
        base = current_end
    else:
        base = datetime.utcnow()
    return add_months(base, months)


def ensure_user(telegram_id: int, username: str | None) -> User:
    settings = get_settings()
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    user = get_user_by_hash(digest)
    if user:
        return user
    encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id))
    if username:
        encrypted_username = encrypt_text(settings.fernet_key, username)
    else:
        encrypted_username = None

    user = User(
        telegram_id=encrypted_id,
        telegram_id_hash=digest,
        username=encrypted_username,
        subscription_end=None,
        tariff=None,
        is_active=True,
    )
    from bot.db.repository import upsert_user

    return upsert_user(user)


def grant_subscription(
    telegram_id: int,
    username: str | None,
    tariff_code: str,
) -> SubscriptionUpdate:
    tariff = get_tariff(tariff_code)
    user = ensure_user(telegram_id, username)
    new_end = compute_new_end(user.subscription_end, tariff.months)
    update_user_subscrip
    telegram_id: int | None,
    action: str,
    meta: str | None = None,
) -> None:
    settings = get_settings()
    if telegram_id is not None:
        digest = telegram_id_hash(settings.app_secret, telegram_id)
        encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id))
    else:
        digest = None
        encrypted_id = None

    log = SecurityLog(
        telegram_id=encrypted_id,
        telegram_id_hash=digest,
        action=action,
        meta=meta,
    
    settings = get_settings()
    digest = telegram_id_hash(settings.app_secret, telegram_id) if telegram_id is not None else None
    encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id)) if telegram_id is not None else None
    log = SecurityLog(telegram_id=encrypted_id, telegram_id_hash=digest, action=action, meta=meta)
    add_security_log(log)


def days_left(subscription_end: datetime | None) -> int | None:
    if subscription_end is None:
        return None
    delta = subscription_end - datetime.utcnow()
    return max(0, delta.days)


def has_active_subscription(telegram_id: int) -> bool:
    settings = get_settings()
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    user = get_user_by_hash(digest)
    if user is None or user.subscription_end is None:
        return False
    return user.subscription_end > datetime.utcnow() and user.is_active


def reminder_window(days: int) -> tuple[datetime, datetime]:
    start = datetime.utcnow() + timedelta(days=days)
    end = start + timedelta(days=1)
    return start, end
