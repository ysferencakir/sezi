"""add watch_logs table

Revision ID: 9927be202ed6
Revises: 396de40585cb
Create Date: 2026-07-20 14:11:47.982505

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9927be202ed6'
down_revision: Union[str, None] = '396de40585cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('watch_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('day', sa.Date(), nullable=False),
    sa.Column('raw_text', sa.String(length=255), nullable=False),
    sa.Column('season', sa.Integer(), nullable=True),
    sa.Column('episode', sa.Integer(), nullable=True),
    sa.Column('matched', sa.Boolean(), nullable=False),
    sa.Column('tmdb_id', sa.Integer(), nullable=True),
    sa.Column('media_type', sa.String(length=10), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('overview', sa.String(length=1000), nullable=True),
    sa.Column('poster_path', sa.String(length=255), nullable=True),
    sa.Column('release_date', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watch_logs_day'), 'watch_logs', ['day'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_watch_logs_day'), table_name='watch_logs')
    op.drop_table('watch_logs')
