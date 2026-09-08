"""/stocks — остатки с пагинацией и выгрузкой XLSX."""

from __future__ import annotations

import html
from collections import OrderedDict
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.catalog import CatalogNavCB, catalog_nav_keyboard
from bot.bot_app.keyboards.main import BTN_STOCKS
from bot.bot_app.utils.ozon import ozon_client_for_active
from bot.bot_app.utils.pagination import page_count, remember_next_cursor, safe_xlsx_stem
from bot.db.models import TelegramUser
from bot.ozon.modules.stocks import StocksModule
from bot.ozon.schemas.stocks import StockItem, StocksResponse
from bot.utils.xlsx_template import build_stocks_catalog_xlsx

router = Router()

KIND = "st"
PAGE_SIZE = 25
_STATE_PAGE = "st_page"
_STATE_CURSORS = "st_cursors"


def format_stocks_page(
    seller_name: str,
    items: list[StockItem],
    *,
    page: int,
    total: int,
    page_size: int = PAGE_SIZE,
) -> str:
    grouped: OrderedDict[str, list[StockItem]] = OrderedDict()
    for item in items:
        grouped.setdefault(item.offer_id, []).append(item)
    pages = page_count(total, page_size)
    start = page * page_size + 1
    shown = len(grouped)
    end = page * page_size + shown
    lines = [
        f"📊 <b>Остатки ({html.escape(seller_name)})</b>",
        f"Показаны <b>{start}–{end}</b> из <b>{total}</b> · стр. {page + 1}/{pages}\n",
    ]
    for idx, (offer_id, rows) in enumerate(grouped.items(), start=start):
        qty = sum(r.present for r in rows)
        lines.append(f"{idx}. <code>{html.escape(offer_id)}</code> — {qty} шт.")
        for row in rows[:4]:
            lines.append(f"    └ {html.escape(row.warehouse_name)}: {row.present}")
    lines.append("\nЛистай кнопками или скачай полный список в Excel.")
    return "\n".join(lines)


async def _load_page(
    session: AsyncSession, user: TelegramUser, cursor: str
) -> tuple[str, StocksResponse]:
    seller, client = await ozon_client_for_active(session, user)
    try:
        response = await StocksModule(client).list(limit=PAGE_SIZE, cursor=cursor)
    finally:
        await client.close()
    return seller.name, response


async def _save_and_render(
    state: FSMContext,
    seller_name: str,
    response: StocksResponse,
    page: int,
    cursors: list[str],
) -> tuple[str, Any]:
    cursors = remember_next_cursor(cursors, page, response.cursor if response.has_next else "")
    await state.update_data({_STATE_PAGE: page, _STATE_CURSORS: cursors})
    pages = page_count(response.total, PAGE_SIZE)
    text = format_stocks_page(seller_name, response.result, page=page, total=response.total)
    markup = catalog_nav_keyboard(KIND, page=page, pages=pages, has_next=response.has_next)
    return text, markup


@router.message(Command("stocks"))
@router.message(F.text == BTN_STOCKS)
async def cmd_stocks(
    message: Message, session: AsyncSession, user: TelegramUser, state: FSMContext
) -> None:
    seller_name, response = await _load_page(session, user, cursor="")
    if not response.result:
        await message.answer("📊 Остатков пока нет.")
        return
    text, markup = await _save_and_render(state, seller_name, response, page=0, cursors=[""])
    await message.answer(text, reply_markup=markup)


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action == "noop")))
async def stocks_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action.in_({"prev", "next"}))))
async def stocks_page(
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
async def stocks_xlsx(callback: CallbackQuery, session: AsyncSession, user: TelegramUser) -> None:
    await callback.answer("Собираю полный список…")
    seller, client = await ozon_client_for_active(session, user)
    try:
        catalog = await StocksModule(client).iter_all()
    finally:
        await client.close()
    document = BufferedInputFile(
        build_stocks_catalog_xlsx(catalog.result),
        filename=f"stocks_{safe_xlsx_stem(seller.name)}.xlsx",
    )
    if callback.message:
        await callback.message.answer_document(
            document,
            caption=f"📊 Все остатки кабинета {html.escape(seller.name)}: {catalog.total} шт.",
        )
