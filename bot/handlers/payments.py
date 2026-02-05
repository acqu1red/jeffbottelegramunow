from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.invites import issue_invite_link
from bot.services.payments import (
    build_stars_invoice,
    handle_successful_payment,
)
from bot.services.tariffs import get_tariff

router = Router()


@router.message(Command("buy_3m"))
async def buy_3_months(message: Message, bot: Bot) -> None:
    tariff = get_tariff("3m")
    invoice = build_stars_invoice(tariff)
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=invoice.title,
        description=invoice.description,
        payload=invoice.payload,
        currency=invoice.currency,
        prices=invoice.prices,
        provider_token=invoice.provider_token,
    )


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    payment = message.successful_payment
    tariff = handle_successful_payment(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        payload=payment.invoice_payload,
        total_amount=payment.total_amount,
    )
    try:
        invite = await issue_invite_link(
            bot,
            message.from_user.id,
            message.from_user.username,
        )
    except ValueError:
        invite = None
    if invite:
        await message.answer(
            (
                "Оплата принята. Доступ активирован на %s месяцев. "
                "Вот твой инвайт:\n%s"
            )
            % (tariff.months, invite)
        )
    else:
        await message.answer(
            (
                "Оплата принята. Доступ активирован на %s месяцев. "
                "Инвайт будет выдан через /access."
            )
            % tariff.months
        )
