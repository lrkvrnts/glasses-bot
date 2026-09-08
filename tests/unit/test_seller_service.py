"""Tests for SellerService."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.core.exceptions import OzonAuthError
from bot.services.seller_service import SellerService


async def test_verify_credentials_returns_total():
    """verify_credentials возвращает products_total."""
    service = SellerService(session=AsyncMock())
    with patch("bot.services.seller_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.request = AsyncMock(
            return_value={"result": {"items": [], "total": 42, "last_id": ""}}
        )
        mock_instance.close = AsyncMock()

        result = await service.verify_credentials("CID", "KEY")

    assert result == {"products_total": 42}
    mock_instance.close.assert_awaited_once()


async def test_verify_credentials_calls_correct_endpoint():
    """verify_credentials дёргает /v3/product/list с limit=1."""
    service = SellerService(session=AsyncMock())
    with patch("bot.services.seller_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.request = AsyncMock(return_value={"total": 0})
        mock_instance.close = AsyncMock()

        await service.verify_credentials("CID", "KEY")

        mock_instance.request.assert_awaited_once_with(
            "POST",
            "/v3/product/list",
            json={"filter": {"visibility": "ALL"}, "limit": 1, "last_id": ""},
        )


async def test_verify_credentials_propagates_auth_error():
    """OzonAuthError пробрасывается наверх."""
    service = SellerService(session=AsyncMock())
    with patch("bot.services.seller_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.request = AsyncMock(side_effect=OzonAuthError())
        mock_instance.close = AsyncMock()

        with pytest.raises(OzonAuthError):
            await service.verify_credentials("BAD", "BAD")


async def test_bind_calls_verify_first():
    """bind сначала верифицирует, потом создаёт."""
    mock_session = AsyncMock()
    service = SellerService(session=mock_session)

    with (
        patch.object(service, "verify_credentials", AsyncMock()) as mock_verify,
        patch.object(service._repo, "create", AsyncMock()) as mock_create,
    ):
        mock_create.return_value = "fake-seller"

        result = await service.bind(user_id=1, name="S", client_id="C", api_key="K")

    mock_verify.assert_awaited_once_with("C", "K")
    mock_create.assert_awaited_once()
    assert result == "fake-seller"


async def test_bind_does_not_create_if_verify_fails():
    """bind не создаёт кабинет, если verify падает."""
    mock_session = AsyncMock()
    service = SellerService(session=mock_session)

    with (
        patch.object(service, "verify_credentials", AsyncMock(side_effect=OzonAuthError())),
        patch.object(service._repo, "create", AsyncMock()) as mock_create,
    ):
        import pytest

        with pytest.raises(OzonAuthError):
            await service.bind(user_id=1, name="S", client_id="C", api_key="K")

    mock_create.assert_not_awaited()
