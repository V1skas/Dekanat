"""DK-32 app_updates + workers.last_seen_update_id

Revision ID: c7d8e9f0a1b2
Revises: a3d8f1c2b4e6
Create Date: 2026-07-14 00:00:00.000000

Історія оновлень (changelog, DK-32): таблиця `app_updates` (тексти оголошуються
в коді `Dekanat/declared/updates.py` і синхронізуються скриптом `update.py`,
за зразком `sync_actions`) + high-watermark `workers.last_seen_update_id` для
відмітки «до якого запису користувач уже бачив оновлення».
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a3d8f1c2b4e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'app_updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
    )

    with op.batch_alter_table('workers', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('last_seen_update_id', sa.Integer(), server_default=sa.text('0'), nullable=False)
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workers', schema=None) as batch_op:
        batch_op.drop_column('last_seen_update_id')

    op.drop_table('app_updates')
