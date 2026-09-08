"""Main reply keyboard."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_PRODUCTS = "📦 Товары"
BTN_STOCKS = "📊 Остатки"
BTN_PRICES = "💰 Цены"
BTN_CABINET = "⚙️ Кабинет"
BTN_UPLOADS = "📤 Загрузки"
BTN_STATUS = "📋 Статус"
BTN_HELP = "❓ Помощь"

MENU_BUTTONS: frozenset[str] = frozenset(
    {
        BTN_PRODUCTS,
        BTN_STOCKS,
        BTN_PRICES,
        BTN_CABINET,
        BTN_UPLOADS,
        BTN_STATUS,
        BTN_HELP,
    }
)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PRODUCTS), KeyboardButton(text=BTN_STOCKS)],
            [KeyboardButton(text=BTN_PRICES), KeyboardButton(text=BTN_CABINET)],
            [KeyboardButton(text=BTN_UPLOADS), KeyboardButton(text=BTN_STATUS)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
