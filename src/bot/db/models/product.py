"""Product model."""

from __future__ import annotations

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base
from bot.db.models.base import TimestampMixin
from bot.db.models.seller import SellerAccount


class Product(Base, TimestampMixin):
    """Товар продавца."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("seller_id", "ozon_product_id", name="uq_product_seller_ozon"),
        UniqueConstraint("seller_id", "offer_id", name="uq_product_seller_offer"),
        Index("ix_product_seller_status", "seller_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("seller_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ozon_product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    offer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    sku: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    seller: Mapped[SellerAccount] = relationship(back_populates="products", lazy="joined")

    def __repr__(self) -> str:
        return f"<Product id={self.id} offer_id={self.offer_id!r}>"
