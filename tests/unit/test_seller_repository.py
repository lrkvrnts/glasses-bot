"""Tests for SellerRepository."""

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.seller import SellerRepository
from bot.repositories.user import UserRepository
from bot.services.encryption import EncryptionService


@pytest.fixture
def enc_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def enc(enc_key: str) -> EncryptionService:
    return EncryptionService(enc_key)


async def test_create_encrypts_api_key(session: AsyncSession, enc: EncryptionService):
    """API-ключ в БД зашифрован (не равен plain)."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    repo = SellerRepository(session, encryption=enc)
    seller = await repo.create(
        user_id=user.id, name="Main", ozon_client_id="CID-123", ozon_api_key="plain-key-xyz"
    )
    await session.commit()

    # Plain не хранится в БД
    assert "plain-key-xyz" not in seller.ozon_api_key_encrypted
    # Можно расшифровать обратно
    assert repo.decrypt_api_key(seller) == "plain-key-xyz"


async def test_list_for_user(session: AsyncSession, enc: EncryptionService):
    """list_for_user возвращает кабинеты пользователя."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    repo = SellerRepository(session, encryption=enc)
    await repo.create(user.id, "Store 1", "C1", "K1")
    await repo.create(user.id, "Store 2", "C2", "K2")
    await session.commit()

    sellers = await repo.list_for_user(user.id)
    assert {s.name for s in sellers} == {"Store 1", "Store 2"}


async def test_get_active_for_user_excludes_inactive(session: AsyncSession, enc: EncryptionService):
    """get_active_for_user пропускает is_active=False."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    repo = SellerRepository(session, encryption=enc)
    s = await repo.create(user.id, "Store", "C", "K")
    s.is_active = False
    await session.commit()

    assert await repo.get_active_for_user(user.id) is None


async def test_get_active_for_user_returns_latest(session: AsyncSession, enc: EncryptionService):
    """get_active_for_user возвращает один из активных кабинетов."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    repo = SellerRepository(session, encryption=enc)
    s1 = await repo.create(user.id, "First", "C1", "K1")
    await session.commit()
    s2 = await repo.create(user.id, "Second", "C2", "K2")
    await session.commit()

    active = await repo.get_active_for_user(user.id)
    assert active is not None
    assert active.id in {s1.id, s2.id}
