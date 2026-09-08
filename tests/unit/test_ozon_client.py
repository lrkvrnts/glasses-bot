"""Tests for OzonAPIClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.core.exceptions import OzonAuthError, OzonError, OzonRateLimitError
from bot.ozon.client import OzonAPIClient, OzonCredentials


def make_response(status: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.headers = {}
    resp.content = b"" if json_data is None else b"x"
    resp.json = MagicMock(return_value=json_data or {})
    resp.text = text
    return resp


@pytest.fixture
def client() -> OzonAPIClient:
    return OzonAPIClient(
        credentials=OzonCredentials(client_id="123", api_key="abc"),
        base_url="https://test.api",
    )


async def test_sends_client_id_and_api_key_headers(client: OzonAPIClient):
    """Headers содержат Client-Id и Api-Key."""
    headers = client._client.headers
    assert headers["Client-Id"] == "123"
    assert headers["Api-Key"] == "abc"


async def test_401_raises_ozon_auth_error(client: OzonAPIClient):
    """401 → OzonAuthError."""
    with patch.object(
        client._client,
        "request",
        AsyncMock(return_value=make_response(401, text="Unauthorized")),
    ):
        with pytest.raises(OzonAuthError):
            await client.request("POST", "/test")


async def test_429_raises_rate_limit_with_retry_after(client: OzonAPIClient):
    """429 → OzonRateLimitError с retry_after из header."""
    resp = make_response(429)
    resp.headers = {"Retry-After": "120"}
    with patch.object(client._client, "request", AsyncMock(return_value=resp)):
        with pytest.raises(OzonRateLimitError) as exc_info:
            await client.request("GET", "/test")
        assert exc_info.value.retry_after == 120


async def test_500_raises_ozon_error(client: OzonAPIClient):
    """500 → OzonError."""
    with patch.object(
        client._client,
        "request",
        AsyncMock(return_value=make_response(500, text="oops")),
    ):
        with pytest.raises(OzonError):
            await client.request("GET", "/test")


async def test_200_returns_json(client: OzonAPIClient):
    """200 + JSON → dict."""
    with patch.object(
        client._client,
        "request",
        AsyncMock(return_value=make_response(200, {"result": "ok"})),
    ):
        result = await client.request("GET", "/test")
        assert result == {"result": "ok"}


async def test_204_returns_empty_dict(client: OzonAPIClient):
    """204 без тела → {}."""
    with patch.object(client._client, "request", AsyncMock(return_value=make_response(204))):
        result = await client.request("GET", "/test")
        assert result == {}


async def test_close_releases_httpx_client(client: OzonAPIClient):
    """close() вызывает aclose()."""
    with patch.object(client._client, "aclose", AsyncMock()) as mock_aclose:
        await client.close()
        mock_aclose.assert_awaited_once()
