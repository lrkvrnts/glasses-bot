"""Stock service: get/update stocks via Ozon API."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.stocks import StocksModule
from bot.ozon.schemas.stocks import StocksResponse, StockUpdate
from bot.repositories.seller import SellerRepository
from bot.services.encryption import EncryptionService


class StockService:
    """Бизнес-логика работы с остатками."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._seller_repo = SellerRepository(session, encryption=EncryptionService())

    def _client_for(self, seller) -> OzonAPIClient:
        api_key = self._seller_repo.decrypt_api_key(seller)
        return OzonAPIClient(
            credentials=OzonCredentials(client_id=seller.ozon_client_id, api_key=api_key)
        )

    async def get_stocks(self, seller) -> StocksResponse:
        """Получить все остатки кабинета."""
        client = self._client_for(seller)
        try:
            module = StocksModule(client)
            return await module.list()
        finally:
            await client.close()

    async def apply_updates(self, seller, updates: list[StockUpdate]) -> dict:
        """Применить batch-обновление остатков через Ozon API."""
        client = self._client_for(seller)
        try:
            module = StocksModule(client)
            return await module.update_stocks(updates)
        finally:
            await client.close()
