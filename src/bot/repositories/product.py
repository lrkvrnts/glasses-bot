"""ProductRepository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from bot.db.models import Product
from bot.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def list_for_seller(self, seller_id: int) -> Sequence[Product]:
        result = await self._session.execute(select(Product).where(Product.seller_id == seller_id))
        return result.scalars().all()

    async def get_by_offer_id(self, seller_id: int, offer_id: str) -> Product | None:
        result = await self._session.execute(
            select(Product).where(Product.seller_id == seller_id, Product.offer_id == offer_id)
        )
        return result.scalar_one_or_none()

    async def bulk_create(self, products: list[Product]) -> list[Product]:
        self._session.add_all(products)
        await self._session.flush()
        return products
