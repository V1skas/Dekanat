"""DK-47 item_zno.is_counted_in_rating + fractional points

Revision ID: d4e5f6a7b8c9
Revises: b7c4e1f9a2d3
Create Date: 2026-07-06 15:00:00.000000

Зміни у формуванні рейтингу (DK-47):
* item_zno.is_counted_in_rating — чи входить оцінка предмета у суму балів рейтингу
  та у колонки DOCX. Дефолт False (server_default '0'), бекфіл existing = False
  (окремий UPDATE не потрібен) — після міграції предмети треба явно вмикати.
* results_zno.points / points_raw та rating_entries.total_points → Float: оцінки
  тепер дробні (напр. середнє за компоненти НМТ).

Через batch mode: SQLite (dev — recreate) і MySQL/MariaDB (prod — MODIFY COLUMN).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'b7c4e1f9a2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. item_zno.is_counted_in_rating (дефолт/бекфіл False).
    with op.batch_alter_table('item_zno', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_counted_in_rating', sa.Boolean(), server_default=sa.text('0'), nullable=False)
        )

    # 2. Дробні бали.
    with op.batch_alter_table('results_zno', schema=None) as batch_op:
        batch_op.alter_column('points', existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=False)
        batch_op.alter_column('points_raw', existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=True)

    with op.batch_alter_table('rating_entries', schema=None) as batch_op:
        batch_op.alter_column('total_points', existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('rating_entries', schema=None) as batch_op:
        batch_op.alter_column('total_points', existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=False)

    with op.batch_alter_table('results_zno', schema=None) as batch_op:
        batch_op.alter_column('points_raw', existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=True)
        batch_op.alter_column('points', existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=False)

    with op.batch_alter_table('item_zno', schema=None) as batch_op:
        batch_op.drop_column('is_counted_in_rating')
