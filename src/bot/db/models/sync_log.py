"""SyncLog: audit trail of Ozon sync operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base
from bot.db.models.base import TimestampMixin
from bot.db.models.seller import SellerAccount


class SyncLog(Base, TimestampMixin):
    """Лог операции синхронизации с Ozon."""

    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("seller_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    items_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_success: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    seller: Mapped[SellerAccount] = relationship(lazy="joined")
