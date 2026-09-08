"""Inline-клавиатура пагинации каталога (товары / остатки / цены)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CatalogNavCB(CallbackData, prefix="cat"):
    """kind: pl | st | pr; action: prev | next | xlsx | noop."""

    kind: str
    action: str


def catalog_nav_keyboard(
    kind: str,
    *,
    page: int,
    pages: int,
    has_next: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="← Назад", callback_data=CatalogNavCB(kind=kind, action="prev"))
    builder.button(
        text=f"{page + 1}/{pages}",
        callback_data=CatalogNavCB(kind=kind, action="noop"),
    )
    if has_next:
        builder.button(text="Вперёд →", callback_data=CatalogNavCB(kind=kind, action="next"))
    builder.button(
        text="⬇️ Скачать все (XLSX)",
        callback_data=CatalogNavCB(kind=kind, action="xlsx"),
    )
    builder.adjust(3, 1)
    return builder.as_markup()
