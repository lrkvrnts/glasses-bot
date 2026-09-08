"""Inline-кнопки кабинета и загрузок."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CabinetActionCB(CallbackData, prefix="cab"):
    action: str  # bind


class UploadKindCB(CallbackData, prefix="up"):
    kind: str  # products | stocks | prices


def cabinet_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Привязать кабинет", callback_data=CabinetActionCB(action="bind"))
    return builder.as_markup()


def uploads_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Товары", callback_data=UploadKindCB(kind="products"))
    builder.button(text="📊 Остатки", callback_data=UploadKindCB(kind="stocks"))
    builder.button(text="💰 Цены", callback_data=UploadKindCB(kind="prices"))
    builder.adjust(1)
    return builder.as_markup()
