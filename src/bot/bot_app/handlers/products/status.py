"""/status — статус последних синхронизаций."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.main import BTN_STATUS
from bot.db.models import TelegramUser
from bot.repositories.sync_log import SyncLogRepository

router = Router()


@router.message(Command("status"))
@router.message(F.text == BTN_STATUS)
async def cmd_status(message: Message, session: AsyncSession, user: TelegramUser) -> None:
    repo = SyncLogRepository(session)
    logs = await repo.list_for_user(user.telegram_id, limit=10)

    if not logs:
        await message.answer("У тебя пока нет операций. Начни с /bind и /upload_products")
        return

    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "partial": "⚠️",
        "failed": "🔴",
    }
    lines = ["📋 <b>Последние операции:</b>\n"]
    for log in logs:
        emoji = status_emoji.get(log.status, "❓")
        lines.append(
            f"{emoji} <code>#{log.id}</code> {log.operation}\n"
            f"   {log.items_success}/{log.items_total} ок, {log.items_failed} ошибок\n"
            f"   {log.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
    await message.answer("\n\n".join(lines))
