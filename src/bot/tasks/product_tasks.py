"""Product-related Celery tasks and sync helpers."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.exceptions import XLSXFormatError, XLSXValidationError
from bot.db.models import Product, SellerAccount
from bot.ozon.client import OzonAPIClient, OzonCredentials
from bot.repositories.product import ProductRepository
from bot.repositories.seller import SellerRepository
from bot.repositories.sync_log import SyncLogRepository
from bot.services.encryption import EncryptionService
from bot.tasks.base import DbTask
from bot.tasks.celery_app import celery_app
from bot.tasks.notifications import notify_user
from bot.utils.xlsx_errors import ProductError, generate_error_report
from bot.utils.xlsx_parser import parse_product_upload


async def process_bulk_upload(
    session: AsyncSession, sync_log_id: int, xlsx_path: str
) -> dict[str, Any]:
    """Парсит XLSX и загружает товары через Ozon API.

    Шаги:
    1. Загрузить SyncLog, получить seller
    2. Расшифровать API-ключ
    3. Распарсить XLSX
    4. Сохранить товары в БД как draft
    5. Chunks по 100 товаров → POST /v3/products/import
    6. Обновить SyncLog (success/failed)
    7. Вернуть summary
    """
    sync_repo = SyncLogRepository(session)
    sync_log = await sync_repo.get(sync_log_id)
    if sync_log is None:
        logger.error("SyncLog not found", sync_log_id=sync_log_id)
        return {"status": "error", "reason": "sync_log_not_found"}

    seller = (
        await session.execute(select(SellerAccount).where(SellerAccount.id == sync_log.seller_id))
    ).scalar_one()
    seller_repo = SellerRepository(session, encryption=EncryptionService())
    api_key = seller_repo.decrypt_api_key(seller)

    # Парсим XLSX
    try:
        xlsx_data = Path(xlsx_path).read_bytes()
        rows = parse_product_upload(xlsx_data)
    except XLSXFormatError as e:
        await sync_repo.mark_failed(sync_log, str(e))
        await session.commit()
        return {"status": "error", "reason": "xlsx_format", "message": str(e)}
    except XLSXValidationError as e:
        err_xlsx = generate_error_report([ProductError(row=e.row or 0, sku=None, error=str(e))])
        err_path = Path(tempfile.gettempdir()) / f"errors_{sync_log_id}.xlsx"
        err_path.write_bytes(err_xlsx)
        await sync_repo.mark_failed(sync_log, str(e), errors_file=str(err_path))
        await session.commit()
        return {
            "status": "validation_error",
            "message": str(e),
            "errors_file": str(err_path),
        }

    sync_log.items_total = len(rows)
    sync_log.status = "running"
    await session.commit()

    # Сохраняем все товары как draft в БД
    prod_repo = ProductRepository(session)
    for row in rows:
        existing = await prod_repo.get_by_offer_id(seller.id, row.sku)
        if existing is None:
            session.add(
                Product(
                    seller_id=seller.id,
                    offer_id=row.sku,
                    sku=0,
                    name=row.name,
                    category_id=row.category_id,
                    raw_data=row.model_dump(mode="json"),
                )
            )
    await session.flush()

    # Подключаемся к Ozon и загружаем chunks
    client = OzonAPIClient(credentials=OzonCredentials(seller.ozon_client_id, api_key))
    errors: list[ProductError] = []
    success_count = 0
    failed_count = 0

    try:
        CHUNK_SIZE = 100
        for i in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[i : i + CHUNK_SIZE]
            payload = {
                "items": [
                    {
                        "offer_id": r.sku,
                        "name": r.name,
                        "category_id": r.category_id,
                        "price": str(r.price),
                        "old_price": str(r.old_price) if r.old_price else "0",
                        "barcode": r.barcode,
                    }
                    for r in chunk
                ]
            }
            try:
                response = await client.request("POST", "/v3/product/import", json=payload)
                task_id = response.get("task_id")
                logger.info("Import task created", task_id=task_id, chunk=i // CHUNK_SIZE)
                success_count += len(chunk)
            except Exception as e:
                logger.exception("Chunk failed", chunk=i // CHUNK_SIZE)
                for r in chunk:
                    errors.append(ProductError(row=i + 2, sku=r.sku, error=str(e)))
                failed_count += len(chunk)
    finally:
        await client.close()

    # Итог
    sync_log.items_success = success_count
    sync_log.items_failed = failed_count
    sync_log.finished_at = datetime.now(UTC)
    sync_log.status = "completed" if failed_count == 0 else "partial"

    errors_file_path: str | None = None
    if errors:
        err_xlsx = generate_error_report(errors)
        err_path = Path(tempfile.gettempdir()) / f"errors_{sync_log_id}.xlsx"
        err_path.write_bytes(err_xlsx)
        sync_log.error = json.dumps([e.__dict__ for e in errors])
        errors_file_path = str(err_path)

    await session.commit()

    # Уведомляем пользователя
    try:
        emoji = "✅" if failed_count == 0 else "⚠️"
        await notify_user(
            sync_log.user_telegram_id,
            f"{emoji} <b>Загрузка завершена</b>\n\n"
            f"ID: <code>{sync_log.id}</code>\n"
            f"Всего: {len(rows)}\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {failed_count}\n"
            + (
                f"\n📎 Файл с ошибками: <code>{errors_file_path}</code>" if errors_file_path else ""
            ),
        )
        # Если есть файл ошибок — отправляем
        if errors_file_path:
            from aiogram.types import FSInputFile

            from bot.tasks.notifications import get_bot

            bot = get_bot()
            try:
                doc = FSInputFile(errors_file_path, filename="upload_errors.xlsx")
                await bot.send_document(chat_id=sync_log.user_telegram_id, document=doc)
            except Exception:
                logger.exception("Failed to send errors file")
            finally:
                await bot.session.close()
    except Exception:
        logger.exception("Failed to notify user")

    return {
        "status": sync_log.status,
        "total": len(rows),
        "success": success_count,
        "failed": failed_count,
        "errors_file": errors_file_path,
    }


@celery_app.task(
    name="bot.tasks.bulk_upload_products",
    bind=True,
    base=DbTask,
    max_retries=3,
)
def bulk_upload_products(self, sync_log_id: int, xlsx_path: str) -> dict[str, Any]:
    """Celery-обёртка: создаёт event loop и вызывает async process_bulk_upload.

    Принимаемые аргументы:
        sync_log_id: ID SyncLog в БД
        xlsx_path: путь к XLSX-файлу во временной директории
    """
    import asyncio

    from bot.db.session import get_session

    async def _run() -> dict[str, Any]:
        async for session in get_session():
            return await process_bulk_upload(session, sync_log_id, xlsx_path)
        return {"status": "error", "reason": "no_session"}  # pragma: no cover

    return asyncio.run(_run())
