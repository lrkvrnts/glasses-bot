"""E2E: /bind FSM start."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from bot.bot_app.handlers.seller.bind import cmd_bind
from bot.bot_app.states import SellerBindFSM
from bot.db.models import TelegramUser


@pytest.mark.asyncio
async def test_cmd_bind_starts_fsm():
    """Команда /bind переводит в состояние waiting_for_name."""
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key="test")

    message = MagicMock()
    message.answer = AsyncMock()

    user = MagicMock(spec=TelegramUser)
    user.id = 1

    await cmd_bind(message=message, state=state, user=user)

    current = await state.get_state()
    assert current == SellerBindFSM.waiting_for_name.state
    message.answer.assert_awaited_once()
    call_args = message.answer.await_args
    text = call_args.kwargs.get("text") or call_args.args[0]
    assert "Привязка" in text
    assert "Шаг 1" in text


@pytest.mark.asyncio
async def test_cmd_bind_passes_correct_user():
    """cmd_bind принимает user и передаёт его в message."""
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key="test-key-2")

    message = MagicMock()
    message.answer = AsyncMock()

    user = MagicMock(spec=TelegramUser)
    user.id = 42

    await cmd_bind(message=message, state=state, user=user)

    state_after = await state.get_state()
    assert state_after is not None
