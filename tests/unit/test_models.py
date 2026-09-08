"""Tests for ORM models."""

from __future__ import annotations

from bot.db.models import TelegramUser
from bot.db.models.base import TimestampMixin


def test_telegram_user_tablename():
    """TelegramUser маппится в правильную таблицу."""
    assert TelegramUser.__tablename__ == "telegram_users"


def test_telegram_user_has_timestamps():
    """TelegramUser наследует TimestampMixin."""
    assert hasattr(TelegramUser, "created_at")
    assert hasattr(TelegramUser, "updated_at")
    assert issubclass(TelegramUser, TimestampMixin)


def test_telegram_user_required_fields():
    """TelegramUser.telegram_id обязателен."""
    col = TelegramUser.__table__.c.telegram_id
    assert col.nullable is False
    assert col.unique is True


def test_telegram_user_optional_fields():
    """Username/first/last name — nullable."""
    for field in ("username", "first_name", "last_name"):
        col = TelegramUser.__table__.c[field]
        assert col.nullable is True


def test_telegram_user_repr():
    """__repr__ информативен."""
    user = TelegramUser(id=1, telegram_id=12345)
    assert "telegram_id=12345" in repr(user)


def test_telegram_user_columns_exist():
    """Все ожидаемые колонки на месте."""
    cols = {c.name for c in TelegramUser.__table__.columns}
    assert cols == {
        "id",
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "created_at",
        "updated_at",
    }


def test_telegram_user_telegram_id_indexed():
    """telegram_id имеет индекс."""
    col = TelegramUser.__table__.c.telegram_id
    assert col.index is True


def test_seller_account_tablename():
    """SellerAccount маппится в правильную таблицу."""
    from bot.db.models import SellerAccount

    assert SellerAccount.__tablename__ == "seller_accounts"


def test_seller_account_required_fields():
    """SellerAccount: user_id, name, ozon_client_id, ozon_api_key_encrypted — required."""
    from bot.db.models import SellerAccount

    for field in ("user_id", "name", "ozon_client_id", "ozon_api_key_encrypted"):
        col = SellerAccount.__table__.c[field]
        assert col.nullable is False, field


def test_seller_account_user_fk_cascade():
    """user_id FK с ON DELETE CASCADE."""
    from bot.db.models import SellerAccount

    fk = list(SellerAccount.__table__.c.user_id.foreign_keys)[0]
    assert fk.ondelete == "CASCADE"


def test_seller_account_is_active_default_true():
    """is_active default = True."""
    from bot.db.models import SellerAccount

    col = SellerAccount.__table__.c.is_active
    assert col.default.arg is True


def test_seller_account_user_relationship():
    """SellerAccount.user — relationship to TelegramUser."""
    from bot.db.models import SellerAccount

    assert hasattr(SellerAccount, "user")
    assert hasattr(TelegramUser, "sellers")
