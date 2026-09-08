"""Tests for StocksModule."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.stocks import StocksModule
from bot.ozon.schemas.stocks import StockFilter, StockUpdate


@pytest.fixture
def module() -> StocksModule:
    client = OzonAPIClient(OzonCredentials("123", "abc"))
    return StocksModule(client)


async def test_base_path_is_v4_product(module: StocksModule):
    assert module.base_path == "/v4/product"


async def test_list_calls_stocks_endpoint(module: StocksModule):
    """list() делает POST /v4/product/info/stocks с обязательным filter."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(
            return_value={
                "items": [
                    {
                        "product_id": 1,
                        "offer_id": "SKU-1",
                        "stocks": [{"type": "fbs", "present": 10, "reserved": 1}],
                    }
                ],
                "total": 1,
                "cursor": "",
            }
        ),
    ) as mock_req:
        response = await module.list()

        mock_req.assert_awaited_once_with(
            "POST",
            "/v4/product/info/stocks",
            json={"filter": {"visibility": "ALL"}, "limit": 100, "cursor": ""},
        )
        assert len(response.result) == 1
        assert response.result[0].offer_id == "SKU-1"
        assert response.result[0].present == 10
        assert response.result[0].warehouse_name == "fbs"


async def test_list_with_warehouse_filter(module: StocksModule):
    """Фильтр по warehouse_id передаётся в filter."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"items": [], "total": 0, "cursor": ""}),
    ) as mock_req:
        await module.list(StockFilter(visibility="ALL", warehouse_id=["wh-1"]), limit=50)

        payload = mock_req.await_args.kwargs["json"]
        assert payload["limit"] == 50
        assert payload["filter"]["warehouse_id"] == ["wh-1"]


async def test_by_offers_calls_correct_endpoint(module: StocksModule):
    """by_offers() — POST /v4/product/info/stocks с offer_id."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"items": [], "total": 0, "cursor": ""}),
    ) as mock_req:
        await module.by_offers(["SKU-1", "SKU-2"])

        payload = mock_req.await_args.kwargs["json"]
        assert mock_req.await_args.args[1] == "/v4/product/info/stocks"
        assert payload["filter"]["offer_id"] == ["SKU-1", "SKU-2"]


async def test_update_stocks_builds_payload(module: StocksModule):
    """update_stocks формирует payload с stocks list."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"task_id": "t-1"}),
    ) as mock_req:
        result = await module.update_stocks(
            [
                StockUpdate(offer_id="SKU-1", warehouse_id="wh-1", stock=10),
                StockUpdate(offer_id="SKU-2", warehouse_id="wh-1", stock=5),
            ]
        )

        assert result == {"task_id": "t-1"}
        payload = mock_req.await_args.kwargs["json"]
        assert len(payload["stocks"]) == 2
        assert payload["stocks"][0]["offer_id"] == "SKU-1"
        assert payload["stocks"][1]["stock"] == 5


async def test_update_stocks_calls_v2_products_stocks(module: StocksModule):
    """update_stocks вызывает /v2/products/stocks (а не /v1/warehouse/last-mile/movement)."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"task_id": "t-1"}),
    ) as mock_req:
        await module.update_stocks([StockUpdate(offer_id="SKU-1", warehouse_id="wh-1", stock=1)])

        called_path = mock_req.await_args.args[1]
        assert called_path == "/v2/products/stocks"
