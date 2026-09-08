"""Stocks module."""

from __future__ import annotations

from bot.ozon.modules.base import BaseOzonModule
from bot.ozon.schemas.stocks import (
    StockFilter,
    StockItem,
    StocksResponse,
    StockUpdate,
    stocks_list_payload,
)


class StocksModule(BaseOzonModule):
    """https://api-seller.ozon.ru/v4/product/info/stocks + /v2/products/stocks"""

    base_path = "/v4/product"

    async def list(
        self,
        filter: StockFilter | None = None,
        *,
        limit: int = 100,
        cursor: str = "",
    ) -> StocksResponse:
        """POST /v4/product/info/stocks."""
        payload = stocks_list_payload(filter, limit=limit, cursor=cursor)
        data = await self._post("/info/stocks", json=payload)
        return StocksResponse.model_validate(data)

    async def by_offers(self, offer_ids: list[str]) -> StocksResponse:
        """POST /v4/product/info/stocks с фильтром по offer_id."""
        limit = min(1000, max(1, len(offer_ids)))
        return await self.list(StockFilter(offer_id=offer_ids), limit=limit)

    async def update_stocks(self, updates: list[StockUpdate]) -> dict:
        """POST /v2/products/stocks — обновление остатков."""
        payload = {
            "stocks": [
                {
                    "offer_id": u.offer_id,
                    "warehouse_id": u.warehouse_id,
                    "stock": u.stock,
                }
                for u in updates
            ]
        }
        return await self._client.request("POST", "/v2/products/stocks", json=payload)

    async def iter_all(
        self, *, page_size: int = 1000, max_items: int = 50_000
    ) -> StocksResponse:
        """Все страницы /v4/product/info/stocks."""
        items: list[StockItem] = []
        cursor = ""
        total = 0
        while len(items) < max_items:
            page = await self.list(limit=min(page_size, max_items - len(items)), cursor=cursor)
            total = page.total
            if not page.result:
                break
            items.extend(page.result)
            if not page.has_next:
                break
            cursor = page.cursor
        return StocksResponse(result=items, total=total or len(items), has_next=False, cursor="")
