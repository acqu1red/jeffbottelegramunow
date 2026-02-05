from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram import Bot

from bot.config import get_settings
from bot.services.invites import issue_invite_link
from bot.services.payments import process_tinkoff_webhook

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/tinkoff")
async def tinkoff_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    result = process_tinkoff_webhook(payload)
    if not result.ok:
        return JSONResponse(
            {"ok": False, "message": result.message},
            status_code=400,
        )

    if result.telegram_id and result.tariff:
        settings = get_settings()
        bot = Bot(token=settings.bot_token)
        try:
            invite = await issue_invite_link(bot, result.telegram_id, None)
            await bot.send_message(
                result.telegram_id,
                (
                    "Оплата принята. Доступ активирован на %s месяцев. "
                    "Вот твой инвайт:\n%s"
                )
                % (result.tariff.months, invite),
            )
        finally:
            await bot.session.close()

    return JSONResponse({"ok": True})
