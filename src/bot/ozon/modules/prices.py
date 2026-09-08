"""Prices module."""

from __future__ import annotations

from bot.ozon.modules.base import BaseOzonModule
from bot.ozon.schemas.prices import (
    PriceInfo,
    PriceListResponse,
    PriceUpdateItem,
    PriceUpdateResult,
    prices_list_payload,
)


class PricesModule(BaseOzonModule):
    """https://api-seller.ozon.ru/v5/product/info/prices + /v1/product/import/prices"""

    base_path = "/v1/product"

    async def list(
        self,
        filter: dict | None = None,
        limit: int = 100,
        cursor: str = "",
    ) -> PriceListResponse:
        """POST /v5/product/info/prices — цены с курсорной пагинацией."""
        payload = prices_list_payload(filter, limit=limit, cursor=cursor)
        data = await self._client.request("POST", "/v5/product/info/prices", json=payload)
        return PriceListResponse.model_validate(data)

    async def update(self, updates: list[PriceUpdateItem]) -> list[PriceUpdateResult]:
        """POST /v1/product/import/prices — обновление цен."""
        payload = {
            "prices": [
                {
                    "offer_id": u.offer_id,
                    "price": str(u.price),
                    "old_price": str(u.old_price) if u.old_price else "0",
                }
                for u in updates
            ]
        }
        await self._client.request("POST", "/v1/product/import/prices", json=payload)
        return [PriceUpdateResult(offer_id=u.offer_id, updated=True) for u in updates]

    async def iter_all(
        self, *, page_size: int = 1000, max_items: int = 50_000
    ) -> PriceListResponse:
        """Все страницы /v5/product/info/prices."""
        items: list[PriceInfo] = []
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
        return PriceListResponse(result=items, total=total or len(items), has_next=False, cursor="")
