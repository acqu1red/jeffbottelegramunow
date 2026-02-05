import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.db.session import init_db
from bot.handlers.access import router as access_router
from bot.handlers.admin import router as admin_router
from bot.handlers.payments import router as payments_router
from bot.handlers.paywall import router as paywall_router
from bot.handlers.system import router as system_router
from bot.scheduler.jobs import start_scheduler

logging.basicConfig(level=logging.INFO)


def build_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.bot_token)


async def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)

    bot = build_bot()
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(system_router)
    dp.include_router(paywall_router)
    dp.include_router(payments_router)
    dp.include_router(access_router)

    start_scheduler(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
