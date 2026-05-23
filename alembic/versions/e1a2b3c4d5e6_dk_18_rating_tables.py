"""DK-18 rating tables

Revision ID: e1a2b3c4d5e6
Revises: c3d4e5f6a7b8
Create Date: 2026-05-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Створює таблиці для збереження сформованого рейтингового списку:
    `rating_snapshots` — мета інформація знімка (кампанія, дата),
    `rating_entries` — рядки рейтингу з позицією, балом і статусом.
    """
    op.create_table(
        'rating_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_campaign', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(['id_campaign'], ['admission_campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'rating_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_snapshot', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['id_snapshot'], ['rating_snapshots.id']),
        sa.ForeignKeyConstraint(
            ['id_speciality_code', 'id_speciality_department'],
            ['specialties.code', 'specialties.id_department'],
        ),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('rating_entries')
    op.drop_table('rating_snapshots')
