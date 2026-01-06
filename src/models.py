"""SQLAlchemy ORM models for database tables"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Market(Base):
    """Market metadata from Polymarket CLOB API"""

    __tablename__ = "markets"

    token_id = Column(String(255), primary_key=True)
    condition_id = Column(String(255), nullable=True)
    question = Column(Text, nullable=False)
    outcome = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    closed = Column(Boolean, default=False)
    end_date_iso = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_markets_active", "active"),
        Index("idx_markets_closed", "closed"),
    )


class MarketPrice(Base):
    """Unified time-series table for all market prices (midpoints)

    Stores both historical snapshots and real-time price data.
    - Historical: Initial snapshot of ALL markets at startup
    - Real-time: Ongoing collection of ACTIVE markets every hour
    """

    __tablename__ = "market_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token_id = Column(
        String(255), ForeignKey("markets.token_id", ondelete="CASCADE"), nullable=False, index=True
    )
    price = Column(Numeric(18, 16), nullable=False)  # Midpoint price in range [0, 1]
    timestamp = Column(BigInteger, nullable=False, index=True)  # Unix timestamp (seconds)
    collected_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("token_id", "timestamp", name="uq_token_timestamp"),
        Index("ix_timestamp_token", "timestamp", "token_id"),  # Time-series queries
        Index("ix_token_timestamp", "token_id", "timestamp"),  # Token-specific queries
    )
