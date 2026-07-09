"""DK-57 special_conditions_person surrogate PK

Revision ID: b8abb96cbdb9
Revises: f6a7b8c9d0e1
Create Date: 2026-07-09 12:00:00.000000

Переводить special_conditions_person на сурогатний PK `id` (замість складеного
(id_person, id_special_condition)) — особа тепер може мати кілька документів по
одній і тій самій пільзі (різні номер/дата видачі, DK-57). Той самий клас
проблеми, що вирішувався в DK-38 для specialties, але простіше: жодна інша
таблиця не посилається на special_conditions_person як на FK-ціль (листова
таблиця), тож без каскаду дочірніх перестворень.

Стратегія — create __new (з id PK) + INSERT..SELECT зі старої + drop old +
rename, однаково для SQLite (dev) і MySQL/MariaDB (prod): FK усередині
create_table працює на обох діалектах напряму, дочірніх ALTER не потрібно.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'b8abb96cbdb9'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _str():
    return sqlmodel.sql.sqltypes.AutoString()


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'special_conditions_person__new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_person', sa.Integer(), nullable=False),
        sa.Column('id_special_condition', _str(), nullable=False),
        sa.Column('title', _str(), nullable=True),
        sa.Column('number', _str(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_of_issue', _str(), nullable=False),
        sa.ForeignKeyConstraint(['id_person'], ['persons.id'], ),
        sa.ForeignKeyConstraint(['id_special_condition'], ['special_conditions.subcategory_code'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(sa.text(
        "INSERT INTO special_conditions_person__new "
        "(id_person, id_special_condition, title, number, description, date_of_issue) "
        "SELECT id_person, id_special_condition, title, number, description, date_of_issue "
        "FROM special_conditions_person"
    ))

    op.drop_table('special_conditions_person')
    op.rename_table('special_conditions_person__new', 'special_conditions_person')


def downgrade() -> None:
    """Downgrade schema — повертає складений PK (id_person, id_special_condition).

    УВАГА: якщо після DK-57 в особи з'явилося кілька документів по одній
    пільзі, вони більше не влізуть у складений ключ — зберігається лише
    найстаріший запис (мінімальний `id`) на кожну пару, решта втрачається.
    """
    op.create_table(
        'special_conditions_person__old',
        sa.Column('id_person', sa.Integer(), nullable=False),
        sa.Column('id_special_condition', _str(), nullable=False),
        sa.Column('title', _str(), nullable=True),
        sa.Column('number', _str(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date_of_issue', _str(), nullable=False),
        sa.ForeignKeyConstraint(['id_person'], ['persons.id'], ),
        sa.ForeignKeyConstraint(['id_special_condition'], ['special_conditions.subcategory_code'], ),
        sa.PrimaryKeyConstraint('id_person', 'id_special_condition'),
    )
    op.execute(sa.text(
        "INSERT INTO special_conditions_person__old "
        "(id_person, id_special_condition, title, number, description, date_of_issue) "
        "SELECT id_person, id_special_condition, title, number, description, date_of_issue "
        "FROM special_conditions_person scp "
        "WHERE scp.id = ("
        "  SELECT MIN(scp2.id) FROM special_conditions_person scp2 "
        "  WHERE scp2.id_person = scp.id_person AND scp2.id_special_condition = scp.id_special_condition"
        ")"
    ))

    op.drop_table('special_conditions_person')
    op.rename_table('special_conditions_person__old', 'special_conditions_person')
