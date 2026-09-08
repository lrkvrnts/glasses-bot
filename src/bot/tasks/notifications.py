"""Уведомления пользователю о завершении задач."""

from __future__ import annotations

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot.config.settings import get_settings

_bot: Bot | None = None


def get_bot() -> Bot:
    """Singleton Bot для Celery worker'а."""
    global _bot
    if _bot is None:
        settings = get_settings()
        _bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


async def notify_user(telegram_id: int, text: str) -> None:
    """Отправляет сообщение юзеру от бота."""
    bot = get_bot()
    try:
        await bot.send_message(chat_id=telegram_id, text=text)
    except Exception:
        logger.exception("Failed to notify user", telegram_id=telegram_id)
        raise
    finally:
        await bot.session.close()
