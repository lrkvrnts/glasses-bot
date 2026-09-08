"""Tests for humanize_error."""

from bot.bot_app.utils.humanize import format_error_text, humanize_error
from bot.core.exceptions import AppError, OzonAuthError


def test_humanize_app_error():
    """AppError → использует свой user_message и hint."""
    e = OzonAuthError()
    msg, hint = humanize_error(e)
    assert msg == e.user_message
    assert hint == e.hint
    assert "/bind" in hint


def test_humanize_generic_exception():
    """Обычный Exception → generic message."""
    e = RuntimeError("boom")
    msg, hint = humanize_error(e)
    assert "непредвиденная" in msg.lower()
    assert hint is not None


def test_format_error_text_contains_correlation_id():
    """format_error_text содержит correlation_id."""
    e = OzonAuthError()
    text = format_error_text(e, "abc12345")
    assert "abc12345" in text
    assert "🔴" in text
    assert "/bind" in text  # hint


def test_format_error_text_no_hint_for_generic():
    """У обычного Exception есть generic hint."""
    e = RuntimeError("oops")
    text = format_error_text(e, "xyz")
    assert "xyz" in text
    assert "💡" in text


def test_custom_app_error_user_message():
    """AppError с явным message использует его."""
    e = AppError("Custom error text")
    assert e.user_message == "Custom error text"
