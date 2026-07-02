"""DK-43 application_statuses.is_allowed_in_rating

Revision ID: b7c4e1f9a2d3
Revises: a1b2c3d4e5f6
Create Date: 2026-07-02 12:00:00.000000

Прапорець «статус допускає абітурієнта до рейтингового списку» (DK-43). Дефолт
False — картка з таким статусом у рейтингу не бере участі і йде в самий низ.
Простий add_column через batch mode — SQLite (dev) і MySQL/MariaDB (prod).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7c4e1f9a2d3'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('application_statuses', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_allowed_in_rating', sa.Boolean(), server_default=sa.text('0'), nullable=False)
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('application_statuses', schema=None) as batch_op:
        batch_op.drop_column('is_allowed_in_rating')
