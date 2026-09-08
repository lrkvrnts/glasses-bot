"""/upload_stocks + /upload_prices — загрузка XLSX для обновления остатков/цен."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Document, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.actions import UploadKindCB, uploads_inline_keyboard
from bot.bot_app.keyboards.main import BTN_UPLOADS
from bot.core.exceptions import SellerNotBoundError
from bot.db.models import SyncLog, TelegramUser
from bot.repositories.sync_log import SyncLogRepository
from bot.services.seller_service import SellerService
from bot.tasks.product_tasks import bulk_upload_products
from bot.utils.xlsx_template import (
    generate_prices_template,
    generate_product_template,
    generate_stocks_template,
    get_prices_template_filename,
    get_stocks_template_filename,
    get_template_filename,
)

router = Router()


async def send_upload_template(message: Message, kind: str) -> None:
    if kind == "products":
        await message.answer_document(
            document=BufferedInputFile(
                generate_product_template(), filename=get_template_filename()
            ),
            caption=(
                "📤 <b>Загрузка товаров</b>\n\n"
                "1. Скачай шаблон ниже\n"
                "2. Заполни (не меняй заголовки!)\n"
                "3. Отправь заполненный .xlsx файлом в этот чат\n\n"
                "Максимум 5000 товаров за раз."
            ),
        )
        return
    if kind == "stocks":
        await message.answer_document(
            document=BufferedInputFile(
                generate_stocks_template(), filename=get_stocks_template_filename()
            ),
            caption=(
                "📤 <b>Обновление остатков</b>\n\n"
                "1. Скачай шаблон\n"
                "2. Заполни (SKU, Warehouse ID, Остаток)\n"
                "3. Отправь .xlsx файл в этот чат"
            ),
        )
        return
    await message.answer_document(
        document=BufferedInputFile(
            generate_prices_template(), filename=get_prices_template_filename()
        ),
        caption=(
            "📤 <b>Обновление цен</b>\n\n"
            "1. Скачай шаблон\n"
            "2. Заполни (SKU, Цена, [Старая цена])\n"
            "3. Отправь .xlsx файл в этот чат"
        ),
    )


@router.message(Command("upload_stocks"))
async def cmd_upload_stocks(message: Message) -> None:
    await send_upload_template(message, "stocks")


@router.message(Command("upload_prices"))
async def cmd_upload_prices(message: Message) -> None:
    await send_upload_template(message, "prices")


@router.message(F.text == BTN_UPLOADS)
async def cmd_uploads_menu(message: Message) -> None:
    await message.answer(
        "📤 <b>Загрузки</b>\n\nВыбери, какой шаблон отправить:",
        reply_markup=uploads_inline_keyboard(),
    )


@router.callback_query(UploadKindCB.filter())
async def uploads_kind(callback: CallbackQuery, callback_data: UploadKindCB) -> None:
    await callback.answer()
    if callback.message:
        await send_upload_template(callback.message, callback_data.kind)


@router.message(F.document)
async def handle_document_upload(
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

    file = await bot.get_file(doc.file_id)
    if file.file_path is None:
        await message.answer("❌ Не удалось скачать файл")
        return

    tmp_dir = Path(tempfile.gettempdir())
    xlsx_path = tmp_dir / f"upload_{user.id}_{datetime.now(UTC).timestamp()}.xlsx"
    await bot.download_file(file.file_path, destination=xlsx_path)

    # Определяем операцию по имени файла
    fname = doc.file_name.lower()
    if "stock" in fname:
        operation = "bulk_update_stocks"
    elif "price" in fname:
        operation = "bulk_update_prices"
    else:
        operation = "bulk_upload_products"

    sync_repo = SyncLogRepository(session)
    sync_log = SyncLog(
        seller_id=seller.id,
        user_telegram_id=user.telegram_id,
        operation=operation,
        status="pending",
    )
    await sync_repo.add(sync_log)
    await session.commit()

    bulk_upload_products.delay(sync_log.id, str(xlsx_path))

    await message.answer(
        f"⏳ <b>Файл принят в обработку</b>\n\n"
        f"Операция: {operation}\n"
        f"ID: <code>{sync_log.id}</code>\n"
        "Результат придёт по завершении."
    )
