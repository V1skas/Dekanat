"""entrants_exams: full schema (date/time/description/workers M2M)

Revision ID: c3d4e5f6a7b8
Revises: a5f1c8e92b41
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a5f1c8e92b41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Drop and recreate `entrants_exams` so it gets a surrogate `id` PK plus the
    fields required by the exam schedule UI. Safe: table is empty at the moment
    of migration. Also create the M2M `entrants_exams_workers` link table.
    """
    op.drop_table('entrants_exams')
    op.create_table(
        'entrants_exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_group', sa.Integer(), nullable=False),
        sa.Column('id_item_zno', sa.Integer(), nullable=False),
        sa.Column('date', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('time_start', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('time_end', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['id_group'], ['entrants_groups.id']),
        sa.ForeignKeyConstraint(['id_item_zno'], ['item_zno.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'entrants_exams_workers',
        sa.Column('id_exam', sa.Integer(), nullable=False),
        sa.Column('id_worker', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_exam'], ['entrants_exams.id']),
        sa.ForeignKeyConstraint(['id_worker'], ['workers.id']),
        sa.PrimaryKeyConstraint('id_exam', 'id_worker'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('entrants_exams_workers')
    op.drop_table('entrants_exams')
    op.create_table(
        'entrants_exams',
        sa.Column('id_group', sa.Integer(), nullable=False),
        sa.Column('id_item_zno', sa.Integer(), nullable=False),
        sa.Column('date_time', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['id_group'], ['entrants_groups.id']),
        sa.ForeignKeyConstraint(['id_item_zno'], ['item_zno.id']),
        sa.PrimaryKeyConstraint('id_group', 'id_item_zno'),
    )
