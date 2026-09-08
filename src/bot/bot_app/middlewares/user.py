"""User middleware: get_or_create TelegramUser, inject as data['user']."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.db.models import TelegramUser
from bot.repositories.user import UserRepository


class UserMiddleware(BaseMiddleware):
    """Регистрирует/получает TelegramUser и кладёт в data['user']."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        session = data.get("session")
        if session is None:
            return await handler(event, data)

        repo = UserRepository(session)
        user, _ = await repo.get_or_create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        data["user"] = user
        return await handler(event, data)


__all__ = ["TelegramUser", "UserMiddleware"]
