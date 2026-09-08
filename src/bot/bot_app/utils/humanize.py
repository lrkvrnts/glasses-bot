"""Human-friendly error messages."""

from __future__ import annotations

from loguru import logger

from bot.core.exceptions import AppError


def humanize_error(exc: Exception) -> tuple[str, str | None]:
    """Возвращает (user_message, hint)."""
    if isinstance(exc, AppError):
        return exc.user_message, exc.hint

    logger.exception("Unhandled exception in handler")
    return (
        "Произошла непредвиденная ошибка.",
        "Попробуй позже или обратись к администратору.",
    )


def format_error_text(exc: Exception, correlation_id: str) -> str:
    msg, hint = humanize_error(exc)
    parts = ["🔴 <b>Ошибка</b>\n\n", msg]
    if hint:
        parts.append(f"\n💡 {hint}")
    parts.append(f"\n\nКод: <code>{correlation_id}</code>")
    return "".join(parts)
