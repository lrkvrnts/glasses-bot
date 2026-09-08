"""/start handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards import main_keyboard
from bot.repositories.user import UserRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Регистрирует юзера и приветствует."""
    repo = UserRepository(session)
    user, created = await repo.get_or_create(
        telegram_id=message.from_user.id,  # type: ignore[union-attr]
        username=message.from_user.username,  # type: ignore[union-attr]
        first_name=message.from_user.first_name,  # type: ignore[union-attr]
        last_name=message.from_user.last_name,  # type: ignore[union-attr]
    )
    await session.commit()

    greeting = "Привет" if created else "С возвращением"
    text = (
        f"{greeting}, {user.first_name or 'друг'}! 👋\n\n"
        "Я — бот для работы с Ozon Seller API.\n\n"
        "📦 <b>Товары</b> — загрузка и управление\n"
        "📊 <b>Остатки</b> — проверка и обновление\n"
        "💰 <b>Цены</b> — просмотр и изменение\n"
        "⚙️ <b>Кабинет</b> — привязка магазина Ozon\n\n"
        "Нажми кнопку или введи /help"
    )
    await message.answer(text, reply_markup=main_keyboard())
