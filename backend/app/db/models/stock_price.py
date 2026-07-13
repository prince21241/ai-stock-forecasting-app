from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "trading_date", "source", name="uq_stock_price_identity"),
        Index("ix_stock_prices_symbol", "symbol"),
        Index("ix_stock_prices_trading_date", "trading_date"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="alpha_vantage", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
