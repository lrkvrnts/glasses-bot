"""Base repository."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic CRUD."""

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id_: int) -> T | None:
        return await self._session.get(self.model, id_)

    async def list(self) -> Sequence[T]:
        result = await self._session.execute(select(self.model))
        return result.scalars().all()

    async def add(self, instance: T) -> T:
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        await self._session.execute(sa_delete(self.model).where(self.model.id == instance.id))
        await self._session.flush()
