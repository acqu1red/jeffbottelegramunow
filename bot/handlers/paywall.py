from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import FSInputFile

from bot.keyboards.paywall import (
    entry_keyboard,
    offer_keyboard,
    pricing_keyboard,
    warmup_keyboard,
)
from bot.config import get_settings
from bot.services.copy import entry_text, offer_text, pricing_text, warmup_text
from bot.services.invites import issue_invite_link
from bot.services.payments import build_stars_invoice
from bot.services.subscriptions import grant_subscription
from bot.services.tariffs import get_tariff

router = Router()
PHOTO_PATH = Path(__file__).resolve().parents[2] / "start.jpg"


def _photo() -> FSInputFile:
    return FSInputFile(PHOTO_PATH)


async def _send_photo_message(
    message: Message,
    text: str,
    keyboard,
) -> None:
    await message.answer_photo(
        _photo(),
        caption=text,
        reply_markup=keyboard,
    )


@router.message(Command("start"))
async def start_paywall(message: Message) -> None:
    await _send_photo_message(
        message,
        entry_text(),
        entry_keyboard(),
    )


@router.callback_query(F.data == "pw:warmup")
async def show_warmup(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await _send_photo_message(
        callback.message,
        warmup_text(),
        warmup_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "pw:offer")
async def show_offer(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await _send_photo_message(
        callback.message,
        offer_text(),
        offer_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "pw:pricing")
async def show_pricing(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await _send_photo_message(
        callback.message,
        pricing_text(),
        pricing_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_tariff(callback: CallbackQuery, bot: Bot) -> None:
    tariff_code = callback.data.replace("buy:", "")
    tariff = get_tariff(tariff_code)
    settings = get_settings()
    if settings.admin1_id and callback.from_user.id == settings.admin1_id:
        grant_subscription(callback.from_user.id, callback.from_user.username, tariff.code)
        try:
            invite = await issue_invite_link(
                bot,
                callback.from_user.id,
                callback.from_user.username,
            )
        except ValueError:
            invite = None
        if invite:
            await callback.message.answer(
                "Админ-тест: доступ активирован. Инвайт:\n%s" % invite
            )
        else:
            await callback.message.answer(
                "Админ-тест: доступ активирован. Инвайт через /access."
            )
        await callback.answer()
        return
    invoice = build_stars_invoice(tariff)
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=invoice.title,
        description=invoice.description,
        payload=invoice.payload,
        currency=invoice.currency,
        prices=invoice.prices,
        provider_token=invoice.provider_token,
    )
    await callback.answer()
