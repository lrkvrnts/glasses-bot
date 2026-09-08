"""/sellers — список привязанных кабинетов."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.actions import cabinet_inline_keyboard
from bot.bot_app.keyboards.main import BTN_CABINET
from bot.db.models import TelegramUser
from bot.services.seller_service import SellerService

router = Router()


@router.message(Command("sellers"))
@router.message(F.text == BTN_CABINET)
async def cmd_sellers(message: Message, session: AsyncSession, user: TelegramUser) -> None:
    service = SellerService(session)
    sellers = await service.list_for_user(user.id)

    if not sellers:
        await message.answer(
            "У тебя пока нет привязанных кабинетов.",
            reply_markup=cabinet_inline_keyboard(),
        )
        return

    lines = ["📋 <b>Твои кабинеты:</b>\n"]
    for i, s in enumerate(sellers, 1):
        status = "🟢 активен" if s.is_active else "🔴 отключён"
        lines.append(f"{i}. {s.name} — {status}\n" f"   Client ID: {s.ozon_client_id}")

    await message.answer("\n\n".join(lines), reply_markup=cabinet_inline_keyboard())
