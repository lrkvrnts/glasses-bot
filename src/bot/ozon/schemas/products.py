"""Schemas for Products module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ProductListFilter(BaseModel):
    """Фильтр GetProductListRequest.filter (обязателен в API)."""

    visibility: str = "ALL"
    offer_id: list[str] | None = None
    product_id: list[int] | None = None


class ProductListItem(BaseModel):
    """Товар из /v3/product/list (имя/SKU в list нет — они в info/list)."""

    product_id: int
    offer_id: str
    sku: int | None = None
    name: str | None = None
    status: str | None = None
    archived: bool | None = None

    @property
    def display_name(self) -> str:
        return self.name or self.offer_id


class ProductListResponse(BaseModel):
    """Ответ /v3/product/list (плоский вид после unwrap nested result)."""

    result: list[ProductListItem] = Field(default_factory=list)
    total: int = 0
    last_id: str = ""
    has_next: bool = False

    @model_validator(mode="before")
    @classmethod
    def _unwrap_ozon_result(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        inner = data.get("result")
        if isinstance(inner, dict):
            last_id = str(inner.get("last_id") or "")
            return {
                "result": inner.get("items", []),
                "total": inner.get("total", 0),
                "last_id": last_id,
                "has_next": bool(last_id),
            }
        return data


def product_list_payload(
    filt: ProductListFilter | None = None,
    *,
    limit: int = 100,
    last_id: str = "",
) -> dict[str, Any]:
    """Тело POST /v3/product/list: filter обязателен."""
    filt = filt or ProductListFilter()
    filter_body = filt.model_dump(exclude_none=True)
    if not filter_body.get("visibility"):
        filter_body["visibility"] = "ALL"
    return {
        "filter": filter_body,
        "limit": limit,
        "last_id": last_id,
    }
