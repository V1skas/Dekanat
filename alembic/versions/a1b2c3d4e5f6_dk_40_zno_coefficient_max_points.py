"""DK-40 ZNO coefficient, raw points, max total points setting

Revision ID: a1b2c3d4e5f6
Revises: 5edaaf840f39
Create Date: 2026-07-02 00:00:00.000000

Зміни у розрахунку рейтингу (DK-40):
* item_zno.coefficient — ваговий коефіцієнт предмета (дефолт 1.0). Бал домножається
  на нього при збереженні оцінки.
* results_zno.points_raw — сирий бал, введений оператором (до множення). Бекфіл із
  points (історично там був саме сирий бал, коефіцієнти = 1.0).
* app_settings — сідиться дефолтний запис max_total_points=200 через
  AppSettingService.ensure_defaults() (deploy.py / on_load), тут не чіпаємо.

Прості add_column через batch mode — переносимо для SQLite (dev) і MySQL/MariaDB
(prod).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5edaaf840f39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. item_zno.coefficient (default 1.0 для існуючих рядків через server_default).
    with op.batch_alter_table('item_zno', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('coefficient', sa.Float(), nullable=False, server_default='1.0')
        )

    # 2. results_zno.points_raw + бекфіл із points.
    with op.batch_alter_table('results_zno', schema=None) as batch_op:
        batch_op.add_column(sa.Column('points_raw', sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE results_zno SET points_raw = points"))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('results_zno', schema=None) as batch_op:
        batch_op.drop_column('points_raw')
    with op.batch_alter_table('item_zno', schema=None) as batch_op:
        batch_op.drop_column('coefficient')
