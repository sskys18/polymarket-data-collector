"""Create markets table

Revision ID: 000_markets
Revises:
Create Date: 2026-01-05 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, String, Text, DateTime, Index

# revision identifiers, used by Alembic.
revision = '000_markets'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create markets table"""
    op.create_table(
        'markets',
        sa.Column('token_id', String(length=255), nullable=False),
        sa.Column('condition_id', String(length=255), nullable=True),
        sa.Column('question', Text(), nullable=False),
        sa.Column('outcome', Text(), nullable=True),
        sa.Column('active', Boolean(), default=True, nullable=True),
        sa.Column('closed', Boolean(), default=False, nullable=True),
        sa.Column('end_date_iso', DateTime(), nullable=True),
        sa.Column('created_at', DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('token_id'),
    )

    # Create indexes
    op.create_index('idx_markets_active', 'markets', ['active'])
    op.create_index('idx_markets_closed', 'markets', ['closed'])


def downgrade() -> None:
    """Drop markets table"""
    op.drop_index('idx_markets_closed', table_name='markets')
    op.drop_index('idx_markets_active', table_name='markets')
    op.drop_table('markets')
