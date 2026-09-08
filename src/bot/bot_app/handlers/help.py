"""/help handler."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.bot_app.keyboards.main import BTN_HELP, main_keyboard

router = Router()


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    """Показывает список команд."""
    text = (
        "ℹ️ <b>Доступные команды</b>\n\n"
        "/start — Главное меню\n"
        "/bind — Привязать кабинет Ozon\n"
        "/sellers — Список кабинетов\n"
        "/products — Список товаров (страницы + Excel)\n"
        "/stocks — Остатки (страницы + Excel)\n"
        "/prices — Цены (страницы + Excel)\n"
        "/upload_products — Загрузить товары (XLSX)\n"
        "/upload_stocks — Обновить остатки (XLSX)\n"
        "/upload_prices — Обновить цены (XLSX)\n"
        "/status — История операций\n"
        "/help — Эта справка\n\n"
        "Те же действия доступны с кнопок внизу экрана."
    )
    await message.answer(text, reply_markup=main_keyboard())
