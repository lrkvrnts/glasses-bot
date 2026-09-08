"""add products table

Revision ID: 0002_products
Revises: 0001_initial
Create Date: 2026-09-02 13:30:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_products"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), nullable=False),
        sa.Column("ozon_product_id", sa.BigInteger(), nullable=True),
        sa.Column("offer_id", sa.String(length=128), nullable=False),
        sa.Column("sku", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("seller_id", "ozon_product_id", name="uq_product_seller_ozon"),
        sa.UniqueConstraint("seller_id", "offer_id", name="uq_product_seller_offer"),
    )
    op.create_index("ix_products_seller_id", "products", ["seller_id"])
    op.create_index("ix_products_ozon_product_id", "products", ["ozon_product_id"])
    op.create_index("ix_product_seller_status", "products", ["seller_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_product_seller_status", table_name="products")
    op.drop_index("ix_products_ozon_product_id", table_name="products")
    op.drop_index("ix_products_seller_id", table_name="products")
    op.drop_table("products")
