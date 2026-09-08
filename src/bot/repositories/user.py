"""UserRepository."""

from __future__ import annotations

from sqlalchemy import select

from bot.db.models import TelegramUser
from bot.repositories.base import BaseRepository


class UserRepository(BaseRepository[TelegramUser]):
    model = TelegramUser

    async def get_by_telegram_id(self, telegram_id: int) -> TelegramUser | None:
        result = await self._session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[TelegramUser, bool]:
        """Возвращает (user, created)."""
        existing = await self.get_by_telegram_id(telegram_id)
        if existing is not None:
            return existing, False
        user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self._session.add(user)
        await self._session.flush()
        return user, True
