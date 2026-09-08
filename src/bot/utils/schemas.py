"""Schemas for parsed XLSX data."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ProductUploadRow(BaseModel):
    """Строка из XLSX-файла загрузки товаров."""

    sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=512)
    category_id: int = Field(gt=0)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    old_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    barcode: str | None = Field(default=None, max_length=32)
    weight: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("sku")
    @classmethod
    def _validate_sku(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SKU не может быть пустым")
        return v.strip()


class StockUploadRow(BaseModel):
    """Строка из XLSX-файла обновления остатков."""

    sku: str = Field(min_length=1, max_length=128)
    warehouse_id: str = Field(min_length=1, max_length=64)
    stock: int = Field(ge=0)

    @field_validator("sku")
    @classmethod
    def _validate_sku(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SKU не может быть пустым")
        return v.strip()


class PriceUploadRow(BaseModel):
    """Строка из XLSX-файла обновления цен."""

    sku: str = Field(min_length=1, max_length=128)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    old_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    @field_validator("sku")
    @classmethod
    def _validate_sku(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SKU не может быть пустым")
        return v.strip()
