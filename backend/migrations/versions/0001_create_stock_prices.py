"""Create stock_prices table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_prices",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("high_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("low_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("close_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="alpha_vantage"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("symbol", "trading_date", "source", name="uq_stock_price_identity"),
    )
    op.create_index("ix_stock_prices_symbol", "stock_prices", ["symbol"])
    op.create_index("ix_stock_prices_trading_date", "stock_prices", ["trading_date"])


def downgrade() -> None:
    op.drop_index("ix_stock_prices_trading_date", table_name="stock_prices")
    op.drop_index("ix_stock_prices_symbol", table_name="stock_prices")
    op.drop_table("stock_prices")
