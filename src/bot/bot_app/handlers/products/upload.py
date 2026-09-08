"""/upload_products — загрузка XLSX с товарами."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Document, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.handlers.uploads import send_upload_template
from bot.core.exceptions import SellerNotBoundError
from bot.db.models import SyncLog, TelegramUser
from bot.repositories.sync_log import SyncLogRepository
from bot.services.seller_service import SellerService
from bot.tasks.product_tasks import bulk_upload_products

router = Router()


@router.message(Command("upload_products"))
async def cmd_upload_products(message: Message) -> None:
    await send_upload_template(message, "products")


@router.message(F.document)
async def handle_document(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    user: TelegramUser,
) -> None:
    """Приём XLSX-файла → постановка в Celery."""
    doc: Document = message.document  # type: ignore[assignment]
    if not doc.file_name or not doc.file_name.lower().endswith(".xlsx"):
        await message.answer("❌ Пришли файл в формате .xlsx")
        return

    seller_service = SellerService(session)
    seller = await seller_service.get_active(user.id)
    if seller is None:
        raise SellerNotBoundError()

    # Скачиваем файл
    file = await bot.get_file(doc.file_id)
    if file.file_path is None:
        await message.answer("❌ Не удалось скачать файл")
        return

    tmp_dir = Path(tempfile.gettempdir())
    xlsx_path = tmp_dir / f"upload_{user.id}_{datetime.now(UTC).timestamp()}.xlsx"
    await bot.download_file(file.file_path, destination=xlsx_path)

    # SyncLog
    sync_repo = SyncLogRepository(session)
    sync_log = SyncLog(
        seller_id=seller.id,
        user_telegram_id=user.telegram_id,
        operation="bulk_upload_products",
        status="pending",
    )
    await sync_repo.add(sync_log)
    await session.commit()

    # Celery
    bulk_upload_products.delay(sync_log.id, str(xlsx_path))

    await message.answer(
        f"⏳ <b>Файл принят в обработку</b>\n\n"
        f"ID задачи: <code>{sync_log.id}</code>\n"
        "Я пришлю результат, как только загрузка завершится."
    )
