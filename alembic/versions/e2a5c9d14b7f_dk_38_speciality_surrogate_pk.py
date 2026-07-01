"""DK-38 speciality surrogate PK

Revision ID: e2a5c9d14b7f
Revises: c3f1a7d2b9e4
Create Date: 2026-07-01 00:00:00.000000

Переводить specialties на сурогатний PK `id` (замість складеного (code, id_department))
і схлопує складені FK у дочірніх таблицях (specialties_entrants,
admission_campaigns_specialties, rating_entries) в один стовпець id_speciality.

Стратегія — переносиме перестворення таблиць (create *_new + INSERT..SELECT з JOIN +
drop old + rename), однакове для SQLite (dev) і MySQL/MariaDB (prod). Дані переносяться
через JOIN за старим ключем (code, id_department), який був унікальним. FK на
specialties.id у дочірніх таблицях додається наприкінці лише на MySQL (SQLite не вміє
ALTER ADD FK; на рівні ORM звʼязок працює через метадані стовпця).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'e2a5c9d14b7f'
down_revision: Union[str, Sequence[str], None] = 'c3f1a7d2b9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _str():
    return sqlmodel.sql.sqltypes.AutoString()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    is_mysql = bind.dialect.name == "mysql"

    # 1. specialties -> сурогатний id.
    op.create_table(
        'specialties__new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', _str(), nullable=False),
        sa.Column('id_department', sa.Integer(), nullable=False),
        sa.Column('title', _str(), nullable=False),
        sa.Column('educational_and_professional_program', sa.Text(), nullable=True),
        sa.Column('tag', _str(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['id_department'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(sa.text(
        "INSERT INTO specialties__new "
        "(code, id_department, title, educational_and_professional_program, tag, is_deleted) "
        "SELECT code, id_department, title, educational_and_professional_program, tag, is_deleted "
        "FROM specialties"
    ))

    # 2. Дочірні таблиці з id_speciality (FK на specialties.id додамо в кінці на MySQL).
    op.create_table(
        'specialties_entrants__new',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_speciality', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id'], ),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id'], ),
        sa.PrimaryKeyConstraint('id_entrant', 'id_speciality', 'id_form_of_study'),
    )
    op.execute(sa.text(
        "INSERT INTO specialties_entrants__new (id_entrant, id_speciality, id_form_of_study, priority) "
        "SELECT se.id_entrant, sn.id, se.id_form_of_study, se.priority "
        "FROM specialties_entrants se "
        "JOIN specialties__new sn ON sn.code = se.id_speciality_code "
        "AND sn.id_department = se.id_speciality_department"
    ))

    op.create_table(
        'admission_campaigns_specialties__new',
        sa.Column('id_admission_campaign', sa.Integer(), nullable=False),
        sa.Column('id_speciality', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('budget_places', sa.Integer(), nullable=False),
        sa.Column('contract_places', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_admission_campaign'], ['admission_campaigns.id'], ),
        sa.ForeignKeyConstraint(['id_entry_base'], ['entry_base.id'], ),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id'], ),
        sa.PrimaryKeyConstraint('id_admission_campaign', 'id_speciality', 'id_entry_base', 'id_form_of_study'),
    )
    op.execute(sa.text(
        "INSERT INTO admission_campaigns_specialties__new "
        "(id_admission_campaign, id_speciality, id_entry_base, id_form_of_study, budget_places, contract_places) "
        "SELECT acs.id_admission_campaign, sn.id, acs.id_entry_base, acs.id_form_of_study, "
        "acs.budget_places, acs.contract_places "
        "FROM admission_campaigns_specialties acs "
        "JOIN specialties__new sn ON sn.code = acs.id_speciality_code "
        "AND sn.id_department = acs.id_speciality_department"
    ))

    op.create_table(
        'rating_entries__new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_snapshot', sa.Integer(), nullable=False),
        sa.Column('id_speciality', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('status', _str(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id'], ),
        sa.ForeignKeyConstraint(['id_snapshot'], ['rating_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(sa.text(
        "INSERT INTO rating_entries__new "
        "(id, id_snapshot, id_speciality, id_entry_base, id_form_of_study, id_entrant, position, total_points, status) "
        "SELECT re.id, re.id_snapshot, sn.id, re.id_entry_base, re.id_form_of_study, re.id_entrant, "
        "re.position, re.total_points, re.status "
        "FROM rating_entries re "
        "JOIN specialties__new sn ON sn.code = re.id_speciality_code "
        "AND sn.id_department = re.id_speciality_department"
    ))

    # 3. Видаляємо старі таблиці (спочатку дочірні, потім specialties).
    op.drop_table('rating_entries')
    op.drop_table('specialties_entrants')
    op.drop_table('admission_campaigns_specialties')
    op.drop_table('specialties')

    # 4. Перейменовуємо *_new у канонічні імена.
    op.rename_table('specialties__new', 'specialties')
    op.rename_table('specialties_entrants__new', 'specialties_entrants')
    op.rename_table('admission_campaigns_specialties__new', 'admission_campaigns_specialties')
    op.rename_table('rating_entries__new', 'rating_entries')

    # 5. FK на specialties.id — лише MySQL/MariaDB (SQLite не має ALTER ADD FK).
    if is_mysql:
        op.create_foreign_key(None, 'specialties_entrants', 'specialties', ['id_speciality'], ['id'])
        op.create_foreign_key(None, 'admission_campaigns_specialties', 'specialties', ['id_speciality'], ['id'])
        op.create_foreign_key(None, 'rating_entries', 'specialties', ['id_speciality'], ['id'])


def downgrade() -> None:
    """Downgrade schema — повертає складений ключ (code, id_department)."""
    op.create_table(
        'specialties_entrants__old',
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', _str(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id'], ),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id'], ),
        sa.PrimaryKeyConstraint('id_entrant', 'id_speciality_code', 'id_speciality_department', 'id_form_of_study'),
    )
    op.execute(sa.text(
        "INSERT INTO specialties_entrants__old "
        "(id_entrant, id_speciality_code, id_speciality_department, id_form_of_study, priority) "
        "SELECT se.id_entrant, s.code, s.id_department, se.id_form_of_study, se.priority "
        "FROM specialties_entrants se JOIN specialties s ON s.id = se.id_speciality"
    ))

    op.create_table(
        'admission_campaigns_specialties__old',
        sa.Column('id_admission_campaign', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', _str(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('budget_places', sa.Integer(), nullable=False),
        sa.Column('contract_places', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_admission_campaign'], ['admission_campaigns.id'], ),
        sa.ForeignKeyConstraint(['id_entry_base'], ['entry_base.id'], ),
        sa.ForeignKeyConstraint(['id_form_of_study'], ['forms_of_study.id'], ),
        sa.PrimaryKeyConstraint('id_admission_campaign', 'id_speciality_code', 'id_speciality_department', 'id_entry_base', 'id_form_of_study'),
    )
    op.execute(sa.text(
        "INSERT INTO admission_campaigns_specialties__old "
        "(id_admission_campaign, id_speciality_code, id_speciality_department, id_entry_base, id_form_of_study, budget_places, contract_places) "
        "SELECT acs.id_admission_campaign, s.code, s.id_department, acs.id_entry_base, acs.id_form_of_study, "
        "acs.budget_places, acs.contract_places "
        "FROM admission_campaigns_specialties acs JOIN specialties s ON s.id = acs.id_speciality"
    ))

    op.create_table(
        'rating_entries__old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_snapshot', sa.Integer(), nullable=False),
        sa.Column('id_speciality_code', _str(), nullable=False),
        sa.Column('id_speciality_department', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('id_entrant', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('status', _str(), nullable=False),
        sa.ForeignKeyConstraint(['id_entrant'], ['entrants.id'], ),
        sa.ForeignKeyConstraint(['id_snapshot'], ['rating_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(sa.text(
        "INSERT INTO rating_entries__old "
        "(id, id_snapshot, id_speciality_code, id_speciality_department, id_entry_base, id_form_of_study, id_entrant, position, total_points, status) "
        "SELECT re.id, re.id_snapshot, s.code, s.id_department, re.id_entry_base, re.id_form_of_study, re.id_entrant, "
        "re.position, re.total_points, re.status "
        "FROM rating_entries re JOIN specialties s ON s.id = re.id_speciality"
    ))

    op.create_table(
        'specialties__old',
        sa.Column('code', _str(), nullable=False),
        sa.Column('id_department', sa.Integer(), nullable=False),
        sa.Column('title', _str(), nullable=False),
        sa.Column('educational_and_professional_program', sa.Text(), nullable=True),
        sa.Column('tag', _str(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['id_department'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('code', 'id_department'),
    )
    op.execute(sa.text(
        "INSERT INTO specialties__old "
        "(code, id_department, title, educational_and_professional_program, tag, is_deleted) "
        "SELECT code, id_department, title, educational_and_professional_program, tag, is_deleted FROM specialties"
    ))

    op.drop_table('rating_entries')
    op.drop_table('specialties_entrants')
    op.drop_table('admission_campaigns_specialties')
    op.drop_table('specialties')

    op.rename_table('specialties__old', 'specialties')
    op.rename_table('specialties_entrants__old', 'specialties_entrants')
    op.rename_table('admission_campaigns_specialties__old', 'admission_campaigns_specialties')
    op.rename_table('rating_entries__old', 'rating_entries')
