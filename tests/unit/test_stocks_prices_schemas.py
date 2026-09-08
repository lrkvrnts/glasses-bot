"""Tests for stocks & prices schemas."""

from decimal import Decimal


def test_stock_item_default_values():
    """StockItem имеет дефолты для present/reserved."""
    from bot.ozon.schemas.stocks import StockItem

    item = StockItem(product_id=1, offer_id="SKU-1", warehouse_name="Main")
    assert item.present == 0
    assert item.reserved == 0
    assert item.sku is None


def test_stock_update_validates_non_negative():
    """StockUpdate.stock >= 0."""
    import pytest
    from pydantic import ValidationError

    from bot.ozon.schemas.stocks import StockUpdate

    with pytest.raises(ValidationError):
        StockUpdate(offer_id="SKU-1", warehouse_id="wh-1", stock=-1)


def test_price_info_currency_default():
    """PriceInfo.currency по умолчанию RUB."""
    from bot.ozon.schemas.prices import PriceInfo

    info = PriceInfo(offer_id="SKU-1", price=Decimal("1000.00"))
    assert info.currency == "RUB"
    assert info.old_price is None
    assert info.premium_price is None


def test_price_update_item_validates_positive_price():
    """PriceUpdateItem.price > 0."""
    import pytest
    from pydantic import ValidationError

    from bot.ozon.schemas.prices import PriceUpdateItem

    with pytest.raises(ValidationError):
        PriceUpdateItem(offer_id="SKU-1", price=Decimal("0"))


def test_stocks_response_default_empty():
    """StocksResponse дефолт — пустой список."""
    from bot.ozon.schemas.stocks import StocksResponse

    resp = StocksResponse()
    assert resp.result == []
    assert resp.total == 0
    assert resp.has_next is False


def test_stocks_response_unwraps_v4_items():
    from bot.ozon.schemas.stocks import StocksResponse

    resp = StocksResponse.model_validate(
        {
            "items": [
                {
                    "product_id": 1,
                    "offer_id": "A",
                    "stocks": [
                        {"type": "fbo", "present": 2, "reserved": 1, "sku": 11},
                        {"type": "fbs", "present": 5, "reserved": 0},
                    ],
                }
            ],
            "total": 1,
            "cursor": "next",
        }
    )
    assert resp.total == 1
    assert resp.has_next is True
    assert [row.present for row in resp.result] == [2, 5]
    assert resp.result[0].warehouse_name == "fbo"


def test_price_info_flattens_nested_price():
    from bot.ozon.schemas.prices import PriceInfo

    info = PriceInfo.model_validate(
        {
            "offer_id": "SKU-1",
            "product_id": 9,
            "price": {"price": "1290.00", "old_price": "0", "currency_code": "RUB"},
        }
    )
    assert info.price == Decimal("1290.00")
    assert info.old_price is None
    assert info.currency == "RUB"


def test_price_list_response_default_empty():
    from bot.ozon.schemas.prices import PriceListResponse

    resp = PriceListResponse()
    assert resp.result == []
    assert resp.total == 0
