"""/products — список товаров с пагинацией и выгрузкой XLSX."""

from __future__ import annotations

import html
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot_app.keyboards.catalog import CatalogNavCB, catalog_nav_keyboard
from bot.bot_app.keyboards.main import BTN_PRODUCTS
from bot.bot_app.utils.ozon import ozon_client_for_active
from bot.bot_app.utils.pagination import page_count, remember_next_cursor, safe_xlsx_stem
from bot.db.models import TelegramUser
from bot.ozon.modules.products import ProductsModule
from bot.ozon.schemas.products import ProductListItem, ProductListResponse
from bot.utils.xlsx_template import build_products_catalog_xlsx

router = Router()

KIND = "pl"
PAGE_SIZE = 25
_STATE_PAGE = "pl_page"
_STATE_CURSORS = "pl_cursors"


def format_products_page(
    seller_name: str,
    items: list[ProductListItem],
    *,
    page: int,
    total: int,
    page_size: int = PAGE_SIZE,
) -> str:
    pages = page_count(total, page_size)
    start = page * page_size + 1
    end = page * page_size + len(items)
    lines = [
        f"📦 <b>Товары в кабинете {html.escape(seller_name)}</b>",
        f"Показаны <b>{start}–{end}</b> из <b>{total}</b> · стр. {page + 1}/{pages}\n",
    ]
    for idx, item in enumerate(items, start=start):
        lines.append(f"{idx}. <code>{html.escape(item.offer_id)}</code>")
    lines.append("\nЛистай кнопками или скачай полный список в Excel.")
    return "\n".join(lines)


async def _load_page(
    session: AsyncSession, user: TelegramUser, last_id: str
) -> tuple[str, ProductListResponse]:
    seller, client = await ozon_client_for_active(session, user)
    try:
        response = await ProductsModule(client).list(limit=PAGE_SIZE, last_id=last_id)
    finally:
        await client.close()
    return seller.name, response


async def _save_and_render(
    state: FSMContext,
    seller_name: str,
    response: ProductListResponse,
    page: int,
    cursors: list[str],
) -> tuple[str, Any]:
    cursors = remember_next_cursor(cursors, page, response.last_id if response.has_next else "")
    await state.update_data({_STATE_PAGE: page, _STATE_CURSORS: cursors})
    pages = page_count(response.total, PAGE_SIZE)
    text = format_products_page(seller_name, response.result, page=page, total=response.total)
    markup = catalog_nav_keyboard(KIND, page=page, pages=pages, has_next=response.has_next)
    return text, markup


@router.message(Command("products"))
@router.message(F.text == BTN_PRODUCTS)
async def cmd_products(
    message: Message, session: AsyncSession, user: TelegramUser, state: FSMContext
) -> None:
    seller_name, response = await _load_page(session, user, last_id="")
    if not response.result:
        await message.answer("📦 В кабинете пока нет товаров.")
        return
    text, markup = await _save_and_render(state, seller_name, response, page=0, cursors=[""])
    await message.answer(text, reply_markup=markup)


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action == "noop")))
async def products_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action.in_({"prev", "next"}))))
async def products_page(
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
    seller_name, response = await _load_page(session, user, last_id=cursors[page])
    if not response.result:
        await callback.answer("Это последняя страница", show_alert=True)
        return
    text, markup = await _save_and_render(state, seller_name, response, page=page, cursors=cursors)
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(CatalogNavCB.filter((F.kind == KIND) & (F.action == "xlsx")))
async def products_xlsx(callback: CallbackQuery, session: AsyncSession, user: TelegramUser) -> None:
    await callback.answer("Собираю полный список…")
    seller, client = await ozon_client_for_active(session, user)
    try:
        catalog = await ProductsModule(client).iter_all()
    finally:
        await client.close()
    document = BufferedInputFile(
        build_products_catalog_xlsx(catalog.result),
        filename=f"products_{safe_xlsx_stem(seller.name)}.xlsx",
    )
    if callback.message:
        await callback.message.answer_document(
            document,
            caption=f"📦 Все товары кабинета {html.escape(seller.name)}: {catalog.total} шт.",
        )
