from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import get_settings
from bot.db.repository import (
    list_expired_users,
    list_users_for_reminder,
    update_user_status,
)
from bot.security.crypto import decrypt_text
from bot.services.subscriptions import (
    REMINDER_DAYS,
    log_security_action,
    reminder_window,
)


async def run_expiration_job(bot: Bot) -> None:
    settings = get_settings()
    expired_users = list_expired_users(datetime.utcnow())
    for user in expired_users:
        try:
            telegram_id = int(
                decrypt_text(settings.fernet_key, user.telegram_id)
            )
        except Exception:
            log_security_action(None, "decrypt_failed", "user_id=%s" % user.id)
            continue
        try:
            await bot.ban_chat_member(settings.admin_channel_id, telegram_id)
        except Exception:
            log_security_action(
                telegram_id,
                "kick_failed",
                "channel_id=%s" % settings.admin_channel_id,
            )
        update_user_status(user.id, False)
        log_security_action(telegram_id, "subscription_expired_kick", None)


async def run_reminder_job(bot: Bot) -> None:
    settings = get_settings()
    for days in REMINDER_DAYS:
        window_start, window_end = reminder_window(days)
        users = list_users_for_reminder(window_start, window_end)
        for user in users:
            try:
                telegram_id = int(
                    decrypt_text(settings.fernet_key, user.telegram_id)
                )
            except Exception:
                log_security_action(
                    None,
                    "decrypt_failed",
                    "user_id=%s" % user.id,
                )
                continue
            try:
                await bot.send_message(
                    telegram_id,
                    (
                        "Напоминание: доступ закончится через %s дней. "
                        "Нажми, чтобы продлить."
                    )
                    % days,
                )
            except Exception:
                log_security_action(
                    telegram_id,
                    "reminder_send_failed",
                    "days=%s" % days,
                )


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_expiration_job, "interval", minutes=30, args=[bot])
    scheduler.add_job(run_reminder_job, "interval", hours=24, args=[bot])
    scheduler.start()
    return scheduler
