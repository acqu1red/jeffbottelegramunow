from datetime import datetime, timedelta

from aiogram import Bot

from bot.config import get_settings
from bot.db.models import Invite
from bot.db.repository import (
    get_active_invite_for_user,
    mark_invite_used,
    save_invite,
)
from bot.security.crypto import encrypt_text, telegram_id_hash
from bot.services.subscriptions import (
    has_active_subscription,
    log_security_action,
)

INVITE_TTL_MINUTES = 30


def _build_invite_expires() -> datetime:
    return datetime.utcnow() + timedelta(minutes=INVITE_TTL_MINUTES)


async def issue_invite_link(
    bot: Bot,
    telegram_id: int,
    username: str | None,
) -> str:
    settings = get_settings()
    if not has_active_subscription(telegram_id):
        log_security_action(telegram_id, "invite_denied_no_subscription", None)
        raise ValueError("No active subscription")

    active_invite = get_active_invite_for_user(telegram_id)
    if active_invite and not active_invite.is_used:
        try:
            await bot.revoke_chat_invite_link(
                settings.admin_channel_id,
                active_invite.invite_link,
            )
        except Exception:
            log_security_action(telegram_id, "invite_revoke_failed", None)

    expires_at = _build_invite_expires()
    invite = await bot.create_chat_invite_link(
        chat_id=settings.admin_channel_id,
        member_limit=1,
        expire_date=expires_at,
    )

    encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id))
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    record = Invite(
        telegram_id=encrypted_id,
        telegram_id_hash=digest,
        invite_link=invite.invite_link,
        is_used=False,
        expires_at=expires_at,
    )
    save_invite(record)
    log_security_action(
        telegram_id,
        "invite_issued",
        "username=%s" % (username or ""),
    )
    return invite.invite_link


def mark_invite_used_by_link(invite_link: str) -> None:
    mark_invite_used(invite_link)


def log_join(telegram_id: int, invite_link: str | None) -> None:
    meta = (
        "invite_link=%s" % invite_link
        if invite_link
        else "invite_link=unknown"
    )
    log_security_action(telegram_id, "channel_join", meta)


def log_leave(telegram_id: int) -> None:
    log_security_action(telegram_id, "channel_leave", None)
