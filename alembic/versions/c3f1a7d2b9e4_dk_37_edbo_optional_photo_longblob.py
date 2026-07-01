"""DK-37 edbo optional + photo LONGBLOB

Revision ID: c3f1a7d2b9e4
Revises: 68b699f7abfc
Create Date: 2026-07-01 00:00:00.000000

Робить persons.edbo необов'язковим і переводить persons.photo з BLOB у LONGBLOB
на MySQL/MariaDB (на BLOB не влазить фото > 64 КБ). Обидві зміни — ALTER існуючої
таблиці, дані не втрачаються.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'c3f1a7d2b9e4'
down_revision: Union[str, Sequence[str], None] = '68b699f7abfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # edbo -> nullable (працює і на SQLite через batch, і на MySQL/MariaDB).
    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column(
            'edbo',
            existing_type=sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        )

    # photo: BLOB -> LONGBLOB лише на MySQL/MariaDB. На SQLite тип BLOB без ліміту.
    if bind.dialect.name == 'mysql':
        op.alter_column(
            'persons', 'photo',
            existing_type=sa.LargeBinary(),
            type_=mysql.LONGBLOB(),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if bind.dialect.name == 'mysql':
        op.alter_column(
            'persons', 'photo',
            existing_type=mysql.LONGBLOB(),
            type_=sa.LargeBinary(),
            existing_nullable=True,
        )

    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column(
            'edbo',
            existing_type=sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
        )
