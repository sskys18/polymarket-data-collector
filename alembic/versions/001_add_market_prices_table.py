"""Add market_prices unified time-series table

Revision ID: 001_market_prices
Revises:
Create Date: 2026-01-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import BigInteger, String, Numeric, DateTime, Index, UniqueConstraint, ForeignKey

# revision identifiers, used by Alembic.
revision = '001_market_prices'
down_revision = '000_markets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create market_prices unified time-series table"""
    op.create_table(
        'market_prices',
        sa.Column('id', BigInteger(), autoincrement=True, nullable=False),
        sa.Column('token_id', String(length=255), nullable=False),
        sa.Column('price', Numeric(precision=18, scale=16), nullable=False),
        sa.Column('timestamp', BigInteger(), nullable=False),
        sa.Column('collected_at', DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['token_id'], ['markets.token_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_id', 'timestamp', name='uq_token_timestamp'),
    )

    # Create indexes for time-series queries
    op.create_index('ix_market_prices_token_id', 'market_prices', ['token_id'])
    op.create_index('ix_market_prices_timestamp', 'market_prices', ['timestamp'])
    op.create_index('ix_timestamp_token', 'market_prices', ['timestamp', 'token_id'])
    op.create_index('ix_token_timestamp', 'market_prices', ['token_id', 'timestamp'])


def downgrade() -> None:
    """Drop market_prices table"""
    op.drop_index('ix_token_timestamp', table_name='market_prices')
    op.drop_index('ix_timestamp_token', table_name='market_prices')
    op.drop_index('ix_market_prices_timestamp', table_name='market_prices')
    op.drop_index('ix_market_prices_token_id', table_name='market_prices')
    op.drop_table('market_prices')
