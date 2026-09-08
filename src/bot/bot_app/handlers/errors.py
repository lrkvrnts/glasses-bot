"""Global error handler."""

from __future__ import annotations

from uuid import uuid4

from aiogram import Router
from aiogram.types import ErrorEvent
from loguru import logger

from bot.bot_app.utils.humanize import format_error_text

router = Router(name="errors")


@router.errors()
async def on_error(event: ErrorEvent) -> None:
    """Глобальный обработчик ошибок."""
    correlation_id = uuid4().hex[:8]
    logger.opt(exception=event.exception).error(
        "Unhandled error in handler",
        correlation_id=correlation_id,
    )

    text = format_error_text(event.exception, correlation_id)

    update = event.update
    if update.message:
        try:
            await update.message.answer(text)
        except Exception:
            logger.exception("Failed to send error message to user")
    elif update.callback_query:
        try:
            await update.callback_query.answer("Произошла ошибка", show_alert=True)
        except Exception:
            pass
