"""Tests for StockService and PriceService."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from bot.ozon.schemas.prices import (
    PriceListResponse,
    PriceUpdateItem,
    PriceUpdateResult,
)
from bot.ozon.schemas.stocks import StocksResponse, StockUpdate
from bot.services.encryption import EncryptionService
from bot.services.price_service import PriceService
from bot.services.stock_service import StockService


def make_seller(api_key_encrypted: str, client_id: str = "CID") -> MagicMock:
    seller = MagicMock()
    seller.ozon_client_id = client_id
    seller.ozon_api_key_encrypted = api_key_encrypted
    return seller


@pytest.fixture
def enc() -> EncryptionService:
    return EncryptionService(Fernet.generate_key().decode())


@pytest.fixture(autouse=True)
def use_test_encryption_key(monkeypatch, enc: EncryptionService):
    """Подменяем ENCRYPTION_KEY чтобы StockService/PriceService могли расшифровать."""
    from bot.config.settings import get_settings

    # EncryptionService инстанс у нас уже есть — нужно передать тот же ключ
    # в settings. Генерируем новый Fernet-ключ, пересоздаём enc и seller.
    test_key = Fernet.generate_key().decode()
    # Перезаписываем key в нашем enc-сервисе
    enc._fernet = Fernet(test_key.encode())
    monkeypatch.setenv("ENCRYPTION_KEY", test_key)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_stock_service_uses_correct_client(enc: EncryptionService):
    """StockService использует OzonAPIClient с расшифрованным ключом."""
    api_key = "plain-key-1234567890"
    seller = make_seller(enc.encrypt(api_key))

    session = MagicMock()
    service = StockService(session)

    with patch("bot.services.stock_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.close = AsyncMock()
        mock_module = AsyncMock()
        mock_module.list = AsyncMock(return_value=StocksResponse(result=[], total=0))
        with patch(
            "bot.services.stock_service.StocksModule",
            return_value=mock_module,
        ):
            result = await service.get_stocks(seller)

        # Проверяем что client создан с расшифрованным ключом
        call_kwargs = MockClient.call_args.kwargs
        assert call_kwargs["credentials"].client_id == "CID"
        assert call_kwargs["credentials"].api_key == api_key
        mock_instance.close.assert_awaited_once()
    assert result.total == 0


async def test_stock_service_apply_updates(enc: EncryptionService):
    """apply_updates вызывает module.update_stocks."""
    seller = make_seller(enc.encrypt("k"))
    session = MagicMock()
    service = StockService(session)

    updates = [StockUpdate(offer_id="SKU-1", warehouse_id="wh-1", stock=10)]

    with patch("bot.services.stock_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.close = AsyncMock()
        mock_module = AsyncMock()
        mock_module.update_stocks = AsyncMock(return_value={"task_id": "t-1"})
        with patch(
            "bot.services.stock_service.StocksModule",
            return_value=mock_module,
        ):
            result = await service.apply_updates(seller, updates)

        mock_module.update_stocks.assert_awaited_once_with(updates)
        assert result == {"task_id": "t-1"}


async def test_price_service_get_prices(enc: EncryptionService):
    """PriceService.get_prices возвращает PriceListResponse."""
    seller = make_seller(enc.encrypt("k"))
    session = MagicMock()
    service = PriceService(session)

    with patch("bot.services.price_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.close = AsyncMock()
        mock_module = AsyncMock()
        mock_module.list = AsyncMock(return_value=PriceListResponse(result=[], total=0))
        with patch(
            "bot.services.price_service.PricesModule",
            return_value=mock_module,
        ):
            result = await service.get_prices(seller, limit=50, cursor="c1")

        mock_module.list.assert_awaited_once_with(limit=50, cursor="c1")
    assert isinstance(result, PriceListResponse)


async def test_price_service_apply_updates_returns_results(enc: EncryptionService):
    """PriceService.apply_updates возвращает PriceUpdateResult для каждого."""
    seller = make_seller(enc.encrypt("k"))
    session = MagicMock()
    service = PriceService(session)

    updates = [
        PriceUpdateItem(offer_id="SKU-1", price=Decimal("1500")),
        PriceUpdateItem(offer_id="SKU-2", price=Decimal("2000")),
    ]

    with patch("bot.services.price_service.OzonAPIClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.close = AsyncMock()
        mock_module = AsyncMock()
        mock_module.update = AsyncMock(
            return_value=[
                PriceUpdateResult(offer_id="SKU-1", updated=True),
                PriceUpdateResult(offer_id="SKU-2", updated=True),
            ]
        )
        with patch(
            "bot.services.price_service.PricesModule",
            return_value=mock_module,
        ):
            results = await service.apply_updates(seller, updates)

        assert len(results) == 2
        assert all(r.updated for r in results)
