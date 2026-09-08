"""Seller service: bind, list, validate Ozon credentials."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import SellerAccount
from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.schemas.products import ProductListResponse, product_list_payload
from bot.repositories.seller import SellerRepository


class SellerService:
    """Бизнес-логика работы с кабинетами Ozon."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SellerRepository(session)

    async def verify_credentials(self, client_id: str, api_key: str) -> dict[str, int]:
        """Проверяет валидность кредов через лёгкий запрос к Ozon API.

        Возвращает dict с минимальной инфой: {'products_total': int}.
        Бросает OzonAuthError если креды невалидны.
        """
        client = OzonAPIClient(credentials=OzonCredentials(client_id=client_id, api_key=api_key))
        try:
            # Пробуем получить список товаров — лёгкий endpoint для проверки
            raw = await client.request(
                "POST",
                "/v3/product/list",
                json=product_list_payload(limit=1),
            )
            parsed = ProductListResponse.model_validate(raw)
            return {"products_total": parsed.total}
        finally:
            await client.close()

    async def bind(
        self,
        user_id: int,
        name: str,
        client_id: str,
        api_key: str,
    ) -> SellerAccount:
        """Проверяет креды, создаёт SellerAccount, возвращает его."""
        await self.verify_credentials(client_id, api_key)
        seller = await self._repo.create(
            user_id=user_id,
            name=name,
            ozon_client_id=client_id,
            ozon_api_key=api_key,
        )
        await self._session.commit()
        return seller

    async def list_for_user(self, user_id: int) -> list[SellerAccount]:
        return list(await self._repo.list_for_user(user_id))

    async def get_active(self, user_id: int) -> SellerAccount | None:
        return await self._repo.get_active_for_user(user_id)
