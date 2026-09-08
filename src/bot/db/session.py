"""Session helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.engine import get_session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency-style session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
