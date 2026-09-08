"""/prices — цены с пагинацией и выгрузкой XLSX."""

from __future__ import annotations

import html
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.catalog import CatalogNavCB, catalog_nav_keyboard
from bot.bot_app.keyboards.main import BTN_PRICES
from bot.bot_app.utils.ozon import ozon_client_for_active
from bot.bot_app.utils.pagination import page_count, remember_next_cursor, safe_xlsx_stem
from bot.db.models import TelegramUser
from bot.ozon.modules.prices import PricesModule
from bot.ozon.schemas.prices import PriceInfo, PriceListResponse
from bot.utils.xlsx_template import build_prices_catalog_xlsx

router = Router()

KIND = "pr"
PAGE_SIZE = 25
_STATE_PAGE = "pr_page"
_STATE_CURSORS = "pr_cursors"


def format_prices_page(
    seller_name: str,
    items: list[PriceInfo],
    *,
    page: int,
    total: int,
    page_size: int = PAGE_SIZE,
) -> str:
    pages = page_count(total, page_size)
    start = page * page_size + 1
    end = page * page_size + len(items)
    lines = [
        f"💰 <b>Цены ({html.escape(seller_name)})</b>",
        f"Показаны <b>{start}–{end}</b> из <b>{total}</b> · стр. {page + 1}/{pages}\n",
    ]
    for idx, item in enumerate(items, start=start):
        old = f" (старая: {item.old_price})" if item.old_price else ""
        lines.append(f"{idx}. <code>{html.escape(item.offer_id)}</code> — {item.price} ₽{old}")
    lines.append("\nЛистай кнопками или скачай полный список в Excel.")
    return "\n".join(lines)


async def _load_page(
    session: AsyncSession, user: TelegramUser, cursor: str
) -> tuple[str, PriceListResponse]:
    seller, client = await ozon_client_for_active(session, user)
    try:
        response = await PricesModule(client).list(limit=PAGE_SIZE, cursor=cursor)
    finally:
        await client.close()
    return seller.name, response


async def _save_and_render(
    state: FSMContext,
    seller_name: str,
    response: PriceListResponse,
    page: int,
    cursors: list[str],
) -> tuple[str, Any]:
    cursors = remember_next_cursor(cursors, page, response.cursor if response.has_next else "")
    await state.update_data({_STATE_PAGE: page, _STATE_CURSORS: cursors})
    pages = page_count(response.total, PAGE_SIZE)
    text = format_prices_page(seller_name, response.result, page=page, total=response.total)
    markup = catalog_nav_keyboard(KIND, page=page, pages=pages, has_next=response.has_next)
    return text, markup


@router.message(Command("prices"))
@router.message(F.text == BTN_PRICES)
async def cmd_prices(
    message: Message, session: AsyncSession, user: TelegramUser, state: FSMContext
) -> None:
    seller_name, response = await _load_page(session, user, cursor="")
    if not response.result:
        await message.answer("💰 Цен пока нет.")
        return
    text, markup = await _save_and_render(state, seller_name, response, page=0, cursors=[""])
    await message.answer(text, reply_markup=markup)


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action == "noop")))
async def prices_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action.in_({"prev", "next"}))))
async def prices_page(
    callback: CallbackQuery,
    callback_data: CatalogNavCB,
    session: AsyncSession,
    user: TelegramUser,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    cursors: list[str] = list(data.get(_STATE_CURSORS) or [""])
    page = int(data.get(_STATE_PAGE) or 0) + (1 if callback_data.action == "next" else -1)
    page = max(0, page)
    if page >= len(cursors):
        await callback.answer("Дальше страниц нет", show_alert=True)
        return
    seller_name, response = await _load_page(session, user, cursor=cursors[page])
    if not response.result:
        await callback.answer("Это последняя страница", show_alert=True)
        return
    text, markup = await _save_and_render(state, seller_name, response, page=page, cursors=cursors)
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action == "xlsx")))
async def prices_xlsx(callback: CallbackQuery, session: AsyncSession, user: TelegramUser) -> None:
    await callback.answer("Собираю полный список…")
    seller, client = await ozon_client_for_active(session, user)
    try:
        catalog = await PricesModule(client).iter_all()
    finally:
        await client.close()
    document = BufferedInputFile(
        build_prices_catalog_xlsx(catalog.result),
        filename=f"prices_{safe_xlsx_stem(seller.name)}.xlsx",
    )
    if callback.message:
        await callback.message.answer_document(
            document,
            caption=f"💰 Все цены кабинета {html.escape(seller.name)}: {catalog.total} шт.",
        )
