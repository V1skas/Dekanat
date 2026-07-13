"""DK-59 accepted funding sources per entrant specialty priority

Revision ID: a3d8f1c2b4e6
Revises: cf50e0fe0c8a
Create Date: 2026-07-13 00:00:00.000000

Нова довідкова таблиця `specialties_entrants_sources`: позначає, на які саме
ресурси фінансування (`source_of_funding`) абітурієнт згоден для конкретного
пріоритету зі свого списку спеціальностей (напр. лише "бюджет", хоча за
ланцюжком eligibility з DK-52 його могли б розглядати і на "контракт").
Суто довідкова інформація — на формування рейтингового списку не впливає.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3d8f1c2b4e6'
down_revision: Union[str, Sequence[str], None] = 'cf50e0fe0c8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'specialties_entrants_sources',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_speciality', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('id_source_of_funding', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_entrant', 'id_speciality', 'id_form_of_study'],
            [
                'specialties_entrants.id_entrant',
                'specialties_entrants.id_speciality',
                'specialties_entrants.id_form_of_study',
            ],
        ),
        sa.ForeignKeyConstraint(['id_source_of_funding'], ['source_of_funding.id']),
        sa.PrimaryKeyConstraint('id_entrant', 'id_speciality', 'id_form_of_study', 'id_source_of_funding'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('specialties_entrants_sources')
