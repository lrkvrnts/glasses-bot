"""Tests for main reply keyboard."""

from bot.bot_app.keyboards.main import MENU_BUTTONS, main_keyboard


def test_main_keyboard_covers_all_menu_buttons():
    kb = main_keyboard()
    labels = {btn.text for row in kb.keyboard for btn in row}
    assert labels == set(MENU_BUTTONS)


def test_main_keyboard_has_core_actions():
    kb = main_keyboard()
    labels = {btn.text for row in kb.keyboard for btn in row}
    assert "📦 Товары" in labels
    assert "📊 Остатки" in labels
    assert "💰 Цены" in labels
    assert "⚙️ Кабинет" in labels
    assert "📤 Загрузки" in labels
    assert "📋 Статус" in labels
    assert "❓ Помощь" in labels
