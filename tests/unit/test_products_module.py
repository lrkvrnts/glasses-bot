"""Tests for ProductsModule."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.products import ProductsModule
from bot.ozon.schemas.products import ProductListFilter, ProductListResponse


@pytest.fixture
def module() -> ProductsModule:
    client = OzonAPIClient(OzonCredentials("123", "abc"))
    return ProductsModule(client)


async def test_list_calls_correct_endpoint(module: ProductsModule):
    """list() делает POST /v3/product/list."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(
            return_value={
                "result": [{"product_id": 1, "offer_id": "SKU-1", "sku": 100, "name": "Test"}],
                "total": 1,
            }
        ),
    ) as mock_req:
        response = await module.list()

        mock_req.assert_awaited_once_with(
            "POST",
            "/v3/product/list",
            json={"filter": {"visibility": "ALL"}, "limit": 100, "last_id": ""},
        )
        assert isinstance(response, ProductListResponse)
        assert len(response.result) == 1
        assert response.result[0].offer_id == "SKU-1"


async def test_list_with_filter(module: ProductsModule):
    """list(filter) передаёт параметры фильтра в payload."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(return_value={"result": [], "total": 0}),
    ) as mock_req:
        await module.list(ProductListFilter(visibility="VISIBLE"), limit=50, last_id="abc")

        mock_req.assert_awaited_once_with(
            "POST",
            "/v3/product/list",
            json={"filter": {"visibility": "VISIBLE"}, "limit": 50, "last_id": "abc"},
        )


async def test_base_path_is_v3_product(module: ProductsModule):
    assert module.base_path == "/v3/product"


async def test_list_validates_response(module: ProductsModule):
    """list() валидирует ответ через Pydantic."""
    with patch.object(
        module._client,
        "request",
        AsyncMock(
            return_value={
                "result": {
                    "items": [{"product_id": 1, "offer_id": "A"}],
                    "total": 5,
                    "last_id": "",
                }
            }
        ),
    ):
        response = await module.list()

    assert response.total == 5
    assert response.has_next is False
    assert response.result[0].display_name == "A"
