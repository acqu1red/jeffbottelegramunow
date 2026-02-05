import json
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from sqlalchemy import func, select

from bot.config import get_settings
from bot.db.session import SessionLocal
from bot.db.models import User, Payment

router = Router()


@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    settings = get_settings()
    if message.from_user.id not in settings.admin_ids:
        # Silently ignore non-admins or say unknown command
        return

    # Fetch global stats
    with SessionLocal() as session:
        # Total Users
        total_users = session.scalar(select(func.count(User.id))) or 0
        
        # Active Subs (future end date and active flag)
        active_subs = session.scalar(
            select(func.count(User.id)).where(
                User.subscription_end > datetime.utcnow(),
                User.is_active.is_(True)
            )
        ) or 0
        
        # Revenue (Sum of 'paid' XTR payments)
        revenue = session.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.currency == 'XTR',
                Payment.status == 'paid'
            )
        ) or 0

        # Users Today (Created since midnight UTC)
        start_of_day = datetime.utcnow().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        users_today = session.scalar(
            select(func.count(User.id)).where(User.created_at >= start_of_day)
        ) or 0

    # formatting 'today' string
    today_sign = "+" if users_today > 0 else ""
    today_str = f"{today_sign}{users_today}"
    
    base_url = "https://acqu1red.github.io/jeffbottelegramunow/"
    # Embed stats into the URL query params
    webapp_url = (
        f"{base_url}"
        f"?users={total_users}"
        f"&subs={active_subs}"
        f"&revenue={revenue}"
        f"&today={today_str}"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Open Admin Console",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]
    ])

    await message.answer(
        "<b>Admin Panel Access</b>\n"
        "Click the button below to manage users and broadcasts.",
        reply_markup=markup,
        parse_mode="HTML"
    )


@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    settings = get_settings()
    if message.from_user.id not in settings.admin_ids:
        return

    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")

        if action == "broadcast":
            text = data.get("text")
            if text:
                await message.answer(
                    f"📢 <b>Broadcast Sent</b>\n\n{text}",
                    parse_mode="HTML"
                )
                # TODO: Implement actual broadcast logic here using DB users
                # e.g., iterate users and send.
                # For now, just confirming receipt.

    except json.JSONDecodeError:
        await message.answer("Invalid data received from WebApp.")
