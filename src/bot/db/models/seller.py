"""SellerAccount model (Ozon cabinet)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base
from bot.db.models.base import TimestampMixin
from bot.db.models.user import TelegramUser

if TYPE_CHECKING:
    from bot.db.models.product import Product


class SellerAccount(Base, TimestampMixin):
    """Привязанный кабинет Ozon."""

    __tablename__ = "seller_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    ozon_client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ozon_api_key_encrypted: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[TelegramUser] = relationship(back_populates="sellers", lazy="joined")
    products: Mapped[list[Product]] = relationship(
        back_populates="seller",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SellerAccount id={self.id} name={self.name!r}>"
