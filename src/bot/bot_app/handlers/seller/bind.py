"""/bind FSM — привязка кабинета Ozon."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.actions import CabinetActionCB
from bot.bot_app.states import SellerBindFSM
from bot.db.models import TelegramUser
from bot.services.seller_service import SellerService

router = Router()


async def start_bind_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(SellerBindFSM.waiting_for_name)
    await message.answer(
        "🔗 <b>Привязка кабинета Ozon</b>\n\n"
        "Шаг 1 из 3. Введите название магазина "
        "(например, «Основной магазин»):"
    )


@router.message(Command("bind"))
async def cmd_bind(message: Message, state: FSMContext, user: TelegramUser) -> None:
    """Старт привязки кабинета."""
    await start_bind_flow(message, state)


@router.callback_query(CabinetActionCB.filter(F.action == "bind"))
async def cab_bind(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await start_bind_flow(callback.message, state)


@router.message(SellerBindFSM.waiting_for_name, F.text)
async def bind_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name or len(name) > 128:
        await message.answer("❌ Название должно быть от 1 до 128 символов. Попробуй ещё:")
        return
    await state.update_data(name=name)
    await state.set_state(SellerBindFSM.waiting_for_client_id)
    await message.answer("Шаг 2 из 3. Введите <b>Client ID</b> из настроек Ozon Seller:")


@router.message(SellerBindFSM.waiting_for_client_id, F.text)
async def bind_client_id(message: Message, state: FSMContext) -> None:
    client_id = (message.text or "").strip()
    if not client_id.isdigit():
        await message.answer("❌ Client ID должен быть числом. Попробуй ещё:")
        return
    await state.update_data(client_id=client_id)
    await state.set_state(SellerBindFSM.waiting_for_api_key)
    await message.answer(
        "Шаг 3 из 3. Введите <b>API-ключ</b> " "(будет зашифрован и сохранён безопасно):"
    )


@router.message(SellerBindFSM.waiting_for_api_key, F.text)
async def bind_api_key(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user: TelegramUser,
) -> None:
    api_key = (message.text or "").strip()
    if len(api_key) < 16:
        await message.answer("❌ API-ключ слишком короткий. Попробуй ещё:")
        return

    data = await state.get_data()
    client_id = data["client_id"]

    # Сразу удаляем сообщение с ключом для безопасности
    try:
        await message.delete()
    except Exception:
        pass

    # Проверяем и сохраняем
    service = SellerService(session)
    try:
        seller = await service.bind(
            user_id=user.id,
            name=data["name"],
            client_id=client_id,
            api_key=api_key,
        )
    except Exception as e:
        await state.clear()
        user_msg = getattr(e, "user_message", None) or str(e)
        await message.answer(f"🔴 <b>Не удалось привязать кабинет</b>\n\n{user_msg}")
        return

    await state.clear()
    await message.answer(
        f"✅ <b>Кабинет привязан!</b>\n\n"
        f"Название: {seller.name}\n"
        f"Client ID: {seller.ozon_client_id}\n\n"
        "Теперь можно работать с товарами. /products"
    )
