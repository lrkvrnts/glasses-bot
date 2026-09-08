"""Price service: get/update prices via Ozon API."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.prices import PricesModule
from bot.ozon.schemas.prices import (
    PriceListResponse,
    PriceUpdateItem,
    PriceUpdateResult,
)
from bot.repositories.seller import SellerRepository
from bot.services.encryption import EncryptionService


class PriceService:
    """Бизнес-логика работы с ценами."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._seller_repo = SellerRepository(session, encryption=EncryptionService())

    def _client_for(self, seller) -> OzonAPIClient:
        api_key = self._seller_repo.decrypt_api_key(seller)
        return OzonAPIClient(
            credentials=OzonCredentials(client_id=seller.ozon_client_id, api_key=api_key)
        )

    async def get_prices(self, seller, limit: int = 100, cursor: str = "") -> PriceListResponse:
        """Получить цены кабинета."""
        client = self._client_for(seller)
        try:
            module = PricesModule(client)
            return await module.list(limit=limit, cursor=cursor)
        finally:
            await client.close()

    async def apply_updates(
        self, seller, updates: list[PriceUpdateItem]
    ) -> list[PriceUpdateResult]:
        """Применить batch-обновление цен через Ozon API."""
        client = self._client_for(seller)
        try:
            module = PricesModule(client)
            return await module.update(updates)
        finally:
            await client.close()
