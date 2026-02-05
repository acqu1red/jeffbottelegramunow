from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def entry_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Продолжить", callback_data="pw:warmup")
    builder.button(text="Тарифы", callback_data="pw:pricing")
    builder.adjust(1)
    return builder.as_markup()


def warmup_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Показать, что внутри", callback_data="pw:offer")
    builder.button(text="Тарифы", callback_data="pw:pricing")
    builder.adjust(1)
    return builder.as_markup()


def offer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Выбрать тариф", callback_data="pw:pricing")
    builder.button(text="Назад", callback_data="pw:warmup")
    builder.adjust(1)
    return builder.as_markup()


def pricing_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="1 месяц — 250 Stars", callback_data="buy:1m")
    builder.button(text="3 месяца — 650 Stars", callback_data="buy:3m")
    builder.button(text="6 месяцев — 1200 Stars", callback_data="buy:6m")
    builder.button(text="12 месяцев — 2100 Stars", callback_data="buy:12m")
    builder.button(text="Назад", callback_data="pw:offer")
    builder.adjust(1)
    return builder.as_markup()
