import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import get_settings

router = Router()

@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    settings = get_settings()
    if message.from_user.id not in settings.admin_ids:
        # Silently ignore non-admins or say unknown command
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Open Admin Console",
                web_app=WebAppInfo(url="https://acqu1red.github.io/jeffbottelegramunow/")
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
                await message.answer(f"📢 <b>Broadcast Sent</b>\n\n{text}", parse_mode="HTML")
                # TODO: Implement actual broadcast logic here using DB users
                # e.g., iterate users and send.
                # For now, just confirming receipt.
        
    except json.JSONDecodeError:
        await message.answer("Invalid data received from WebApp.")
