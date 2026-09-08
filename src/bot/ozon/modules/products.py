"""Products module."""

from __future__ import annotations

from bot.ozon.modules.base import BaseOzonModule
from bot.ozon.schemas.products import (
    ProductListFilter,
    ProductListItem,
    ProductListResponse,
    product_list_payload,
)


class ProductsModule(BaseOzonModule):
    """https://api-seller.ozon.ru/v3/product/*"""

    base_path = "/v3/product"

    async def list(
        self,
        filter: ProductListFilter | None = None,
        *,
        limit: int = 100,
        last_id: str = "",
    ) -> ProductListResponse:
        """POST /v3/product/list — список товаров с курсорной пагинацией."""
        payload = product_list_payload(filter, limit=limit, last_id=last_id)
        data = await self._post("/list", json=payload)
        return ProductListResponse.model_validate(data)

    async def iter_all(
        self, *, page_size: int = 1000, max_items: int = 50_000
    ) -> ProductListResponse:
        """Все страницы /v3/product/list (курсор last_id)."""
        items: list[ProductListItem] = []
        last_id = ""
        total = 0
        while len(items) < max_items:
            page = await self.list(limit=min(page_size, max_items - len(items)), last_id=last_id)
            total = page.total
            if not page.result:
                break
            items.extend(page.result)
            if not page.has_next:
                break
            last_id = page.last_id
        return ProductListResponse(
            result=items, total=total or len(items), last_id="", has_next=False
        )
