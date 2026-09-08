"""Tests for UserRepository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import TelegramUser
from bot.repositories.user import UserRepository


async def test_get_or_create_creates_new_user(session: AsyncSession):
    """get_or_create создаёт нового юзера, если его нет."""
    repo = UserRepository(session)

    user, created = await repo.get_or_create(
        telegram_id=12345, username="testuser", first_name="Test"
    )

    assert created is True
    assert user.telegram_id == 12345
    assert user.username == "testuser"
    assert user.first_name == "Test"


async def test_get_or_create_returns_existing(session: AsyncSession):
    """get_or_create возвращает существующего, created=False."""
    repo = UserRepository(session)
    await repo.get_or_create(telegram_id=12345, username="alice")
    await session.commit()

    user, created = await repo.get_or_create(telegram_id=12345, username="alice_new")

    assert created is False
    assert user.username == "alice"  # не перезаписали


async def test_get_by_telegram_id(session: AsyncSession):
    """get_by_telegram_id находит по telegram_id."""
    repo = UserRepository(session)
    created_user, _ = await repo.get_or_create(telegram_id=999)
    await session.commit()

    found = await repo.get_by_telegram_id(999)

    assert found is not None
    assert found.id == created_user.id


async def test_get_by_telegram_id_not_found(session: AsyncSession):
    """Возвращает None, если юзер не найден."""
    repo = UserRepository(session)
    found = await repo.get_by_telegram_id(404)
    assert found is None


async def test_get_returns_none_for_missing(session: AsyncSession):
    """BaseRepository.get возвращает None для несуществующего id."""
    repo = UserRepository(session)
    assert await repo.get(9999) is None


async def test_add_and_get(session: AsyncSession):
    """add() сохраняет, get() читает."""
    repo = UserRepository(session)
    user = TelegramUser(telegram_id=111, username="manual")
    added = await repo.add(user)
    await session.commit()

    fetched = await repo.get(added.id)
    assert fetched is not None
    assert fetched.telegram_id == 111
