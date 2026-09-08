"""Schemas for Prices module."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PriceUpdateItem(BaseModel):
    """Запись обновления цены одного товара."""

    offer_id: str
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    old_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class PriceInfo(BaseModel):
    """Текущая цена товара (/v5/product/info/prices)."""

    model_config = ConfigDict(extra="ignore")

    offer_id: str
    product_id: int | None = None
    price: Decimal
    old_price: Decimal | None = None
    premium_price: Decimal | None = None
    currency: str = "RUB"

    @model_validator(mode="before")
    @classmethod
    def _flatten_nested_price(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        nested = data.get("price")
        if not isinstance(nested, dict):
            return data
        old = nested.get("old_price")
        if old in (None, "", "0", "0.00"):
            old = None
        return {
            **data,
            "price": nested.get("price") or "0",
            "old_price": old,
            "premium_price": nested.get("marketing_seller_price") or nested.get("premium_price"),
            "currency": nested.get("currency_code") or data.get("currency") or "RUB",
        }


class PriceListResponse(BaseModel):
    """Ответ /v5/product/info/prices."""

    result: list[PriceInfo] = Field(default_factory=list)
    total: int = 0
    has_next: bool = False
    cursor: str = ""

    @model_validator(mode="before")
    @classmethod
    def _unwrap_ozon(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        items = data.get("items")
        if items is None and isinstance(data.get("result"), list):
            return data
        if not isinstance(items, list):
            return data
        cursor = str(data.get("cursor") or "")
        return {
            "result": items,
            "total": data.get("total", 0),
            "has_next": bool(cursor),
            "cursor": cursor,
        }


class PriceUpdateResult(BaseModel):
    """Результат обновления цены."""

    offer_id: str
    updated: bool
    error: str | None = None


def prices_list_payload(
    extra_filter: dict[str, Any] | None = None,
    *,
    limit: int = 100,
    cursor: str = "",
) -> dict[str, Any]:
    filter_body: dict[str, Any] = {"visibility": "ALL"}
    if extra_filter:
        filter_body.update(extra_filter)
    return {"filter": filter_body, "limit": limit, "cursor": cursor}
