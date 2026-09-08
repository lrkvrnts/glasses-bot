"""Tests for bulk upload processing."""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from openpyxl import Workbook

from bot.core.exceptions import XLSXFormatError
from bot.db.models import SyncLog
from bot.repositories.seller import SellerRepository
from bot.repositories.sync_log import SyncLogRepository
from bot.repositories.user import UserRepository
from bot.services.encryption import EncryptionService
from bot.tasks.product_tasks import process_bulk_upload


def _make_xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Товары"
    headers = ["SKU (артикул)", "Название", "Category ID", "Цена (₽)"]
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def enc() -> EncryptionService:
    """Используем тот же ключ, что и в process_bulk_upload (из settings)."""
    return EncryptionService()  # читает ENCRYPTION_KEY из settings/env


async def test_process_bulk_upload_returns_xlsx_format_error(session, enc):
    """Если файл не парсится, возвращается ошибка формата."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    seller = await seller_repo.create(user.id, "S", "C", "K")
    await session.commit()

    sync_log = SyncLog(
        seller_id=seller.id,
        user_telegram_id=1,
        operation="bulk_upload_products",
    )
    sync_repo = SyncLogRepository(session)
    await sync_repo.add(sync_log)
    await session.commit()

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        f.write(b"not-an-xlsx")
        xlsx_path = f.name

    try:
        with patch(
            "bot.tasks.product_tasks.parse_product_upload",
            side_effect=XLSXFormatError("bad"),
        ):
            result = await process_bulk_upload(session, sync_log.id, xlsx_path)
    finally:
        Path(xlsx_path).unlink(missing_ok=True)

    assert result["status"] == "error"
    assert result["reason"] == "xlsx_format"


async def test_process_bulk_upload_saves_products_as_drafts(session, enc):
    """Валидные строки сохраняются как Product draft в БД."""
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    await session.commit()

    seller_repo = SellerRepository(session, encryption=enc)
    seller = await seller_repo.create(user.id, "S", "C", "K")
    await session.commit()

    sync_log = SyncLog(
        seller_id=seller.id,
        user_telegram_id=1,
        operation="bulk_upload_products",
    )
    sync_repo = SyncLogRepository(session)
    await sync_repo.add(sync_log)
    await session.commit()

    xlsx_data = _make_xlsx(
        [
            ["SKU-A", "Product A", 100, 1000],
            ["SKU-B", "Product B", 200, 2000],
        ]
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        f.write(xlsx_data)
        xlsx_path = f.name

    try:
        # Мокаем Ozon клиент + notify_user, чтобы не слать реальные сообщения
        with (
            patch("bot.tasks.product_tasks.OzonAPIClient") as MockClient,
            patch("bot.tasks.product_tasks.notify_user", AsyncMock()) as mock_notify,
        ):
            mock_instance = MockClient.return_value
            mock_instance.request = AsyncMock(return_value={"task_id": "fake-task"})
            mock_instance.close = AsyncMock()

            result = await process_bulk_upload(session, sync_log.id, xlsx_path)

            mock_notify.assert_awaited_once()
    finally:
        Path(xlsx_path).unlink(missing_ok=True)

    assert result["status"] == "completed"
    assert result["total"] == 2
    assert result["success"] == 2
    assert result["failed"] == 0

    # Проверяем что продукты сохранены
    from bot.repositories.product import ProductRepository

    prod_repo = ProductRepository(session)
    products = await prod_repo.list_for_seller(seller.id)
    assert {p.offer_id for p in products} == {"SKU-A", "SKU-B"}
    assert all(p.status == "draft" for p in products)
