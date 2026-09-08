"""Tests for products list pagination helpers."""

from unittest.mock import AsyncMock, patch

from bot.bot_app.handlers.products.list import format_products_page
from bot.bot_app.utils.pagination import remember_next_cursor
from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.ozon.modules.products import ProductsModule
from bot.ozon.schemas.products import ProductListItem


def test_remember_next_cursor_appends():
    assert remember_next_cursor([""], 0, "abc") == ["", "abc"]


def test_remember_next_cursor_trims_when_no_next():
    assert remember_next_cursor(["", "abc", "stale"], 1, "") == ["", "abc"]


def test_format_products_page_escapes_html():
    items = [ProductListItem(product_id=1, offer_id="A<B>")]
    text = format_products_page("каб1", items, page=0, total=3201, page_size=25)
    assert "1–1" in text
    assert "3201" in text
    assert "<code>A&lt;B&gt;</code>" in text


async def test_iter_all_follows_last_id():
    module = ProductsModule(OzonAPIClient(OzonCredentials("123", "abc")))
    pages = [
        {
            "result": {
                "items": [{"product_id": 1, "offer_id": "A"}],
                "total": 2,
                "last_id": "c1",
            }
        },
        {
            "result": {
                "items": [{"product_id": 2, "offer_id": "B"}],
                "total": 2,
                "last_id": "",
            }
        },
    ]

    with patch.object(module._client, "request", AsyncMock(side_effect=pages)):
        catalog = await module.iter_all(page_size=1)

    assert [i.offer_id for i in catalog.result] == ["A", "B"]
    assert catalog.total == 2
    assert catalog.has_next is False
