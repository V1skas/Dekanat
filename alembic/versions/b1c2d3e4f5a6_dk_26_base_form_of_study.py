"""DK-26: forms of study + base/form in campaign quotas, entrant priorities, rating

Revision ID: b1c2d3e4f5a6
Revises: a3b4c5d6e7f8
Create Date: 2026-06-25 00:00:00.000000

Додає облік форм навчання та протягує базу вступу + форму навчання через систему:
- довідник `forms_of_study` (+ `prefix` у `entry_base`);
- база вступу та форма навчання входять до ключа квоти кампанії;
- форма навчання на кожному пріоритеті абітурієнта;
- база/форма у записах рейтингу.

БД пересоздаётся при деплої — таблиці на момент міграції порожні, тож додавання
NOT NULL колонок із server_default та drop/recreate таблиці квот безпечні.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Префікс бази вступу
    op.add_column(
        'entry_base',
        sa.Column('prefix', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''),
    )

    # Довідник форм навчання
    op.create_table(
        'forms_of_study',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('prefix', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Квоти кампанії: база вступу + форма навчання входять до PK. Drop/recreate —
    # таблиця порожня на момент міграції.
    op.drop_table('admission_campaigns_specialties')
    op.create_table(
        'admission_campaigns_specialties',
        sa.Column('id_admission_campaign', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('budget_places', sa.Integer(), nullable=False),
        sa.Column('contract_places', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_admission_campaign'], ['admission_campaigns.id']),
        sa.ForeignKeyConstraint(['id_entry_base'], ['entry_base.id']),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id']),
        sa.ForeignKeyConstraint(
            ['id_speciality_code', 'id_speciality_department'],
            ['specialties.code', 'specialties.id_department'],
        ),
        sa.PrimaryKeyConstraint(
            'id_admission_campaign', 'id_speciality_code', 'id_speciality_department',
            'id_entry_base', 'id_form_of_study',
        ),
    )

    # Форма навчання на кожному пріоритеті абітурієнта; входить до PK, щоб дозволити
    # ту саму спеціальність з різними формами. Drop/recreate — таблиця порожня.
    op.drop_table('specialties_entrants')
    op.create_table(
        'specialties_entrants',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id']),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id']),
        sa.ForeignKeyConstraint(
            ['id_speciality_code', 'id_speciality_department'],
            ['specialties.code', 'specialties.id_department'],
        ),
        sa.PrimaryKeyConstraint(
            'id_entrant', 'id_speciality_code', 'id_speciality_department', 'id_form_of_study'
        ),
    )

    # База/форма у записах рейтингу
    op.add_column(
        'rating_entries',
        sa.Column('id_entry_base', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'rating_entries',
        sa.Column('id_form_of_study', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rating_entries', 'id_form_of_study')
    op.drop_column('rating_entries', 'id_entry_base')

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

    op.drop_table('admission_campaigns_specialties')
    op.create_table(
        'admission_campaigns_specialties',
        sa.Column('id_admission_campaign', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('budget_places', sa.Integer(), nullable=False),
        sa.Column('contract_places', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_admission_campaign'], ['admission_campaigns.id']),
        sa.ForeignKeyConstraint(
            ['id_speciality_code', 'id_speciality_department'],
            ['specialties.code', 'specialties.id_department'],
        ),
        sa.PrimaryKeyConstraint(
            'id_admission_campaign', 'id_speciality_code', 'id_speciality_department'
        ),
    )

    op.drop_table('forms_of_study')
    op.drop_column('entry_base', 'prefix')
