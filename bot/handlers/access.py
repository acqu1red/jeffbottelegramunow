from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message

from bot.services.invites import (
    issue_invite_link,
    log_join,
    log_leave,
    mark_invite_used_by_link,
)

router = Router()


@router.message(Command("access"))
async def access_command(message: Message, bot: Bot) -> None:
    try:
        invite = await issue_invite_link(
            bot,
            message.from_user.id,
            message.from_user.username,
        )
    except ValueError:
        await message.answer("Нет активной подписки. Сначала оформи доступ.")
        return
    await message.answer(
        "Вот твоя одноразовая ссылка. Она действует ограниченное время:\n%s"
        % invite
    )


@router.chat_member(F.new_chat_member)
async def on_chat_member_update(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    invite_link = None
    if event.invite_link:
        invite_link = event.invite_link.invite_link
        mark_invite_used_by_link(invite_link)
    log_join(user.id, invite_link)


@router.chat_member(F.left_chat_member)
async def on_left(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    log_leave(user.id)
