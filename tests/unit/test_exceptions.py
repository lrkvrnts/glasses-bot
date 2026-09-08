"""Tests for exception hierarchy."""

from bot.core.exceptions import (
    AppError,
    OzonAuthError,
    OzonError,
    OzonNotFoundError,
    OzonRateLimitError,
    OzonValidationError,
    XLSXValidationError,
)


def test_app_error_inherits_exception():
    assert issubclass(AppError, Exception)


def test_ozon_auth_error_has_hint():
    e = OzonAuthError()
    assert e.hint is not None
    assert "/bind" in e.hint


def test_ozon_rate_limit_error_message():
    e = OzonRateLimitError(retry_after=30)
    assert e.retry_after == 30
    assert "30" in e.user_message


def test_ozon_validation_error_with_field():
    e = OzonValidationError(field="sku")
    assert e.field == "sku"
    assert "sku" in e.user_message


def test_xlsx_validation_error_with_row():
    e = XLSXValidationError("Empty SKU", row=5, column="sku")
    assert e.row == 5
    assert e.column == "sku"
    assert "5" in e.user_message
    assert "sku" in e.user_message


def test_all_ozon_errors_inherit_ozon_error():
    for cls in (OzonAuthError, OzonRateLimitError, OzonValidationError, OzonNotFoundError):
        assert issubclass(cls, OzonError)
        assert issubclass(cls, AppError)


def test_seller_not_bound_default_message():
    from bot.core.exceptions import SellerNotBoundError

    e = SellerNotBoundError()
    assert e.hint is not None
    assert "/bind" in e.hint
