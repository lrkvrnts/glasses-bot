"""Tests for PricesModule."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.prices import PricesModule
from bot.ozon.schemas.prices import PriceUpdateItem


@pytest.fixture
def module() -> PricesModule:
    client = OzonAPIClient(OzonCredentials("123", "abc"))
    return PricesModule(client)


async def test_base_path_is_v1_product(module: PricesModule):
    assert module.base_path == "/v1/product"


async def test_list_calls_v5_product_info_prices(module: PricesModule):
    """list() использует /v5/product/info/prices."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"items": [], "total": 0, "cursor": ""}),
    ) as mock_req:
        await module.list()

        mock_req.assert_awaited_once_with(
            "POST",
            "/v5/product/info/prices",
            json={"filter": {"visibility": "ALL"}, "limit": 100, "cursor": ""},
        )


async def test_list_with_filter(module: PricesModule):
    """list(filter) кладёт extra-поля в filter."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"items": [], "total": 0, "cursor": ""}),
    ) as mock_req:
        await module.list(filter={"offer_id": ["SKU-1"]}, limit=50, cursor="c1")

        payload = mock_req.await_args.kwargs["json"]
        assert payload["limit"] == 50
        assert payload["cursor"] == "c1"
        assert payload["filter"]["offer_id"] == ["SKU-1"]
        assert payload["filter"]["visibility"] == "ALL"


async def test_update_returns_results(module: PricesModule):
    """update() возвращает PriceUpdateResult для каждого элемента."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"task_id": "t-1"}),
    ):
        results = await module.update(
            [
                PriceUpdateItem(offer_id="SKU-1", price=Decimal("1500")),
                PriceUpdateItem(offer_id="SKU-2", price=Decimal("2000"), old_price=Decimal("2500")),
            ]
        )

        assert len(results) == 2
        assert all(r.updated for r in results)
        assert results[0].offer_id == "SKU-1"
        assert results[1].offer_id == "SKU-2"


async def test_update_payload_includes_old_price_zero_when_absent(
    module: PricesModule,
):
    """update() с одним item без old_price — old_price='0' в payload."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"task_id": "t-1"}),
    ) as mock_req:
        await module.update([PriceUpdateItem(offer_id="SKU-1", price=Decimal("500"))])

        payload = mock_req.await_args.kwargs["json"]
        assert payload["prices"][0]["old_price"] == "0"
        assert payload["prices"][0]["price"] == "500"


async def test_update_calls_v1_product_import_prices(module: PricesModule):
    """update() вызывает /v1/product/import/prices."""
    from bot.ozon.schemas.prices import PriceUpdateItem

    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"task_id": "t-1"}),
    ) as mock_req:
        await module.update([PriceUpdateItem(offer_id="SKU-1", price=Decimal("100"))])

        called_path = mock_req.await_args.args[1]
        assert called_path == "/v1/product/import/prices"
