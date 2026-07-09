"""DK-51 entrants.submitted_electronically

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-07 12:00:00.000000

Прапорець «заяву подано в електронному вигляді» (DK-51). Дефолт False.
Простий add_column через batch mode — SQLite (dev) і MySQL/MariaDB (prod).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('entrants', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('submitted_electronically', sa.Boolean(), server_default=sa.text('0'), nullable=False)
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('entrants', schema=None) as batch_op:
        batch_op.drop_column('submitted_electronically')
