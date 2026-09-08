"""Schemas for Stocks module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class StockFilter(BaseModel):
    """Фильтр v4 GetProductInfoStocksRequest.filter."""

    visibility: str = "ALL"
    offer_id: list[str] | None = None
    product_id: list[int] | None = None
    warehouse_id: list[str] | None = None


class StockItem(BaseModel):
    """Остаток одного товара (одна схема/склад)."""

    product_id: int
    offer_id: str
    sku: int | None = None
    warehouse_name: str = "склад"
    warehouse_id: str | None = None
    present: int = 0
    reserved: int = 0


class StocksResponse(BaseModel):
    """Ответ /v4/product/info/stocks, развёрнутый в плоский result."""

    result: list[StockItem] = Field(default_factory=list)
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
        rows: list[dict[str, Any]] = []
        for item in items:
            stocks = item.get("stocks") or []
            if not stocks:
                rows.append(
                    {
                        "product_id": item.get("product_id"),
                        "offer_id": item.get("offer_id"),
                        "warehouse_name": "—",
                        "present": 0,
                    }
                )
                continue
            for stock in stocks:
                rows.append(
                    {
                        "product_id": item.get("product_id"),
                        "offer_id": item.get("offer_id"),
                        "sku": stock.get("sku"),
                        "warehouse_name": stock.get("type") or "склад",
                        "present": stock.get("present", 0),
                        "reserved": stock.get("reserved", 0),
                    }
                )
        cursor = str(data.get("cursor") or "")
        return {
            "result": rows,
            "total": data.get("total", 0),
            "has_next": bool(cursor),
            "cursor": cursor,
        }


class StockUpdate(BaseModel):
    """Запись обновления остатков."""

    offer_id: str
    warehouse_id: str
    stock: int = Field(ge=0)


def stocks_list_payload(
    filt: StockFilter | None = None,
    *,
    limit: int = 100,
    cursor: str = "",
) -> dict[str, Any]:
    filt = filt or StockFilter()
    filter_body = filt.model_dump(exclude_none=True)
    if not filter_body.get("visibility"):
        filter_body["visibility"] = "ALL"
    return {"filter": filter_body, "limit": limit, "cursor": cursor}
