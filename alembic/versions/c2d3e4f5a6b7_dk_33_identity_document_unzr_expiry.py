"""DK-33: optional unzr + date_of_expiry on identity_document

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-25 03:00:00.000000

Додає два необов'язкові поля до паспортних даних абітурієнта: УНЗР та дату
закінчення строку дії. Колонки nullable — застосовується без перестворення БД,
існуючі записи не зачіпаються.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('identity_document', sa.Column('unzr', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('identity_document', sa.Column('date_of_expiry', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('identity_document', 'date_of_expiry')
    op.drop_column('identity_document', 'unzr')
