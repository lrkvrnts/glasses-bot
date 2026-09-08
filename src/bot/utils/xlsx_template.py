"""XLSX template generator for product, stocks and prices uploads."""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PRODUCT_TEMPLATE_COLUMNS: list[dict[str, str]] = [
    {"name": "sku", "title": "SKU (артикул)", "required": "true", "width": 20},
    {"name": "name", "title": "Название", "required": "true", "width": 50},
    {"name": "category_id", "title": "Category ID", "required": "true", "width": 15},
    {"name": "price", "title": "Цена (₽)", "required": "true", "width": 12},
    {"name": "old_price", "title": "Старая цена (₽)", "required": "false", "width": 15},
    {"name": "barcode", "title": "Штрих-код", "required": "false", "width": 18},
    {"name": "weight", "title": "Вес (г)", "required": "false", "width": 10},
    {"name": "description", "title": "Описание", "required": "false", "width": 60},
]

STOCKS_TEMPLATE_COLUMNS: list[dict[str, str]] = [
    {"name": "sku", "title": "SKU (артикул)", "required": "true", "width": 20},
    {"name": "warehouse_id", "title": "Warehouse ID", "required": "true", "width": 18},
    {"name": "stock", "title": "Остаток (шт)", "required": "true", "width": 12},
]

PRICES_TEMPLATE_COLUMNS: list[dict[str, str]] = [
    {"name": "sku", "title": "SKU (артикул)", "required": "true", "width": 20},
    {"name": "price", "title": "Цена (₽)", "required": "true", "width": 12},
    {"name": "old_price", "title": "Старая цена (₽)", "required": "false", "width": 15},
]


def _style_header(cell: object) -> None:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="FF111111")
    cell.alignment = Alignment(horizontal="center", vertical="center")


def _write_columns(ws, columns: list[dict[str, str]]) -> None:
    for col_idx, col_def in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_def["title"])
        _style_header(cell)
        ws.column_dimensions[get_column_letter(col_idx)].width = int(col_def["width"])


def _add_instructions(wb: Workbook, lines: list[str]) -> None:
    instructions = wb.create_sheet("Инструкция")
    instructions["A1"] = "Как заполнять шаблон"
    instructions["A1"].font = Font(bold=True, size=14)
    for i, line in enumerate(["", *lines], start=2):
        instructions[f"A{i}"] = line
    instructions.column_dimensions["A"].width = 100


def generate_product_template() -> bytes:
    """Генерирует XLSX-шаблон для загрузки товаров."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Товары"

    _write_columns(ws, PRODUCT_TEMPLATE_COLUMNS)

    example = [
        "SKU-001",
        "Пример товара",
        123456,
        "1500",
        "2000",
        "4600000000000",
        "300",
        "Описание товара",
    ]
    example_fill = PatternFill("solid", fgColor="FFF5F5F5")
    for col_idx, value in enumerate(example, start=1):
        cell = ws.cell(row=2, column=col_idx, value=value)
        cell.fill = example_fill
        cell.alignment = Alignment(vertical="top", wrap_text=(col_idx == len(example)))

    _add_instructions(
        wb,
        [
            "1. Заполняйте только первый лист «Товары».",
            "2. Колонки с пометкой * обязательны.",
            "3. SKU — уникальный артикул продавца.",
            "4. Цена — целое число в рублях, без копеек.",
            "5. Category ID — id категории на Ozon.",
            "6. Сохраните файл в формате .xlsx и отправьте боту через /upload_products.",
        ],
    )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generate_stocks_template() -> bytes:
    """Генерирует XLSX-шаблон для обновления остатков."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Остатки"

    _write_columns(ws, STOCKS_TEMPLATE_COLUMNS)

    example_fill = PatternFill("solid", fgColor="FFF5F5F5")
    example = ["SKU-001", "wh-1", 100]
    for col_idx, value in enumerate(example, start=1):
        cell = ws.cell(row=2, column=col_idx, value=value)
        cell.fill = example_fill

    _add_instructions(
        wb,
        [
            "1. Заполняйте только первый лист «Остатки».",
            "2. Все колонки обязательны.",
            "3. SKU — артикул товара.",
            "4. Warehouse ID — id склада на Ozon.",
            "5. Остаток — целое число ≥ 0.",
            "6. Сохраните в .xlsx и отправьте боту через /upload_stocks.",
        ],
    )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generate_prices_template() -> bytes:
    """Генерирует XLSX-шаблон для обновления цен."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Цены"

    _write_columns(ws, PRICES_TEMPLATE_COLUMNS)

    example_fill = PatternFill("solid", fgColor="FFF5F5F5")
    example = ["SKU-001", "1500", "2000"]
    for col_idx, value in enumerate(example, start=1):
        cell = ws.cell(row=2, column=col_idx, value=value)
        cell.fill = example_fill

    _add_instructions(
        wb,
        [
            "1. Заполняйте только первый лист «Цены».",
            "2. Колонки SKU и Цена обязательны.",
            "3. Старая цена — опционально (для скидок).",
            "4. Цена — число > 0 в рублях.",
            "5. Сохраните в .xlsx и отправьте боту через /upload_prices.",
        ],
    )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def get_template_filename() -> str:
    return "products_template.xlsx"


def get_stocks_template_filename() -> str:
    return "stocks_template.xlsx"


def get_prices_template_filename() -> str:
    return "prices_template.xlsx"


def build_products_catalog_xlsx(items: list[object]) -> bytes:
    """Каталог из /v3/product/list: артикул + product_id."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Товары"
    _write_columns(
        ws,
        [
            {"name": "offer_id", "title": "Артикул (offer_id)", "required": "true", "width": 28},
            {"name": "product_id", "title": "Product ID", "required": "true", "width": 16},
            {"name": "archived", "title": "В архиве", "required": "false", "width": 12},
        ],
    )
    for row_idx, item in enumerate(items, start=2):
        ws.cell(row=row_idx, column=1, value=getattr(item, "offer_id", ""))
        ws.cell(row=row_idx, column=2, value=getattr(item, "product_id", None))
        archived = getattr(item, "archived", None)
        if archived is True:
            ws.cell(row=row_idx, column=3, value="да")
        elif archived is False:
            ws.cell(row=row_idx, column=3, value="нет")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_stocks_catalog_xlsx(items: list[object]) -> bytes:
    """Остатки из /v4/product/info/stocks."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Остатки"
    _write_columns(
        ws,
        [
            {"name": "offer_id", "title": "Артикул (offer_id)", "required": "true", "width": 28},
            {"name": "product_id", "title": "Product ID", "required": "true", "width": 16},
            {"name": "scheme", "title": "Схема", "required": "false", "width": 12},
            {"name": "present", "title": "Доступно", "required": "true", "width": 12},
            {"name": "reserved", "title": "Резерв", "required": "false", "width": 12},
            {"name": "sku", "title": "SKU Ozon", "required": "false", "width": 16},
        ],
    )
    for row_idx, item in enumerate(items, start=2):
        ws.cell(row=row_idx, column=1, value=getattr(item, "offer_id", ""))
        ws.cell(row=row_idx, column=2, value=getattr(item, "product_id", None))
        ws.cell(row=row_idx, column=3, value=getattr(item, "warehouse_name", ""))
        ws.cell(row=row_idx, column=4, value=getattr(item, "present", 0))
        ws.cell(row=row_idx, column=5, value=getattr(item, "reserved", 0))
        ws.cell(row=row_idx, column=6, value=getattr(item, "sku", None))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_prices_catalog_xlsx(items: list[object]) -> bytes:
    """Цены из /v5/product/info/prices."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Цены"
    _write_columns(
        ws,
        [
            {"name": "offer_id", "title": "Артикул (offer_id)", "required": "true", "width": 28},
            {"name": "product_id", "title": "Product ID", "required": "true", "width": 16},
            {"name": "price", "title": "Цена (₽)", "required": "true", "width": 14},
            {"name": "old_price", "title": "Старая цена (₽)", "required": "false", "width": 16},
            {"name": "currency", "title": "Валюта", "required": "false", "width": 10},
        ],
    )
    for row_idx, item in enumerate(items, start=2):
        ws.cell(row=row_idx, column=1, value=getattr(item, "offer_id", ""))
        ws.cell(row=row_idx, column=2, value=getattr(item, "product_id", None))
        price = getattr(item, "price", None)
        ws.cell(row=row_idx, column=3, value=str(price) if price is not None else "")
        old = getattr(item, "old_price", None)
        ws.cell(row=row_idx, column=4, value=str(old) if old is not None else "")
        ws.cell(row=row_idx, column=5, value=getattr(item, "currency", "RUB"))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
