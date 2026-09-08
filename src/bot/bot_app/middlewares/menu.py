"""Сброс FSM при нажатии кнопки главного меню."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from bot.bot_app.keyboards.main import MENU_BUTTONS


class MenuResetFSMMiddleware(BaseMiddleware):
    """Кнопка меню прерывает привязку кабинета и другие FSM."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text in MENU_BUTTONS:
            state: FSMContext | None = data.get("state")
            if state is not None:
                await state.clear()
        return await handler(event, data)
