"""Tests for ProductRepository."""

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Product
from bot.repositories.product import ProductRepository
from bot.repositories.seller import SellerRepository
from bot.repositories.user import UserRepository
from bot.services.encryption import EncryptionService


@pytest.fixture
def enc() -> EncryptionService:
    return EncryptionService(Fernet.generate_key().decode())


async def test_create_and_get_by_offer_id(session: AsyncSession, enc: EncryptionService):
    """Создаём Product, ищем по offer_id."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    seller = await seller_repo.create(user.id, "S", "C", "K")
    await session.commit()

    prod_repo = ProductRepository(session)
    product = Product(
        seller_id=seller.id, offer_id="OFFER-1", sku=12345, name="Test", category_id=42
    )
    await prod_repo.add(product)
    await session.commit()

    found = await prod_repo.get_by_offer_id(seller.id, "OFFER-1")
    assert found is not None
    assert found.name == "Test"
    assert found.category_id == 42


async def test_list_for_seller(session: AsyncSession, enc: EncryptionService):
    """list_for_seller возвращает только товары продавца."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    s1 = await seller_repo.create(user.id, "S1", "C1", "K1")
    s2 = await seller_repo.create(user.id, "S2", "C2", "K2")
    await session.commit()

    prod_repo = ProductRepository(session)
    await prod_repo.add(Product(seller_id=s1.id, offer_id="A", sku=1, name="A"))
    await prod_repo.add(Product(seller_id=s1.id, offer_id="B", sku=2, name="B"))
    await prod_repo.add(Product(seller_id=s2.id, offer_id="C", sku=3, name="C"))
    await session.commit()

    s1_products = await prod_repo.list_for_seller(s1.id)
    assert {p.offer_id for p in s1_products} == {"A", "B"}


async def test_bulk_create(session: AsyncSession, enc: EncryptionService):
    """bulk_create сохраняет пачку товаров за раз."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    seller = await seller_repo.create(user.id, "S", "C", "K")
    await session.commit()

    products = [
        Product(seller_id=seller.id, offer_id=f"OFFER-{i}", sku=i, name=f"P{i}") for i in range(5)
    ]
    prod_repo = ProductRepository(session)
    await prod_repo.bulk_create(products)
    await session.commit()

    all_p = await prod_repo.list_for_seller(seller.id)
    assert len(all_p) == 5


async def test_get_by_offer_id_returns_none_for_missing(
    session: AsyncSession, enc: EncryptionService
):
    """Несуществующий offer_id → None."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    seller = await seller_repo.create(user.id, "S", "C", "K")
    await session.commit()

    prod_repo = ProductRepository(session)
    found = await prod_repo.get_by_offer_id(seller.id, "NONEXISTENT")
    assert found is None
