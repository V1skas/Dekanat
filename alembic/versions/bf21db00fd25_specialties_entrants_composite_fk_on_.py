"""specialties_entrants: composite FK on speciality (code, id_department)

Revision ID: bf21db00fd25
Revises: 56fae3848e71
Create Date: 2026-05-15 00:12:41.324394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'bf21db00fd25'
down_revision: Union[str, Sequence[str], None] = '56fae3848e71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Drop and recreate `specialties_entrants` so that the FK to `specialties`
    becomes composite (code, id_department) and matches the composite PK of
    `specialties`. Safe: table is empty at the moment of migration.
    """
    op.drop_table('specialties_entrants')
    op.create_table(
        'specialties_entrants',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id']),
        sa.ForeignKeyConstraint(
            ['id_speciality_code', 'id_speciality_department'],
            ['specialties.code', 'specialties.id_department'],
        ),
        sa.PrimaryKeyConstraint('id_entrant', 'id_speciality_code', 'id_speciality_department'),
    )


def downgrade() -> None:
    """Downgrade schema.

    Restore the previous shape: single-column FK on `specialties.code`.
    """
    op.drop_table('specialties_entrants')
    op.create_table(
        'specialties_entrants',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_specialties', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id']),
        sa.ForeignKeyConstraint(['id_specialties'], ['specialties.code']),
        sa.PrimaryKeyConstraint('id_entrant', 'id_specialties'),
    )
