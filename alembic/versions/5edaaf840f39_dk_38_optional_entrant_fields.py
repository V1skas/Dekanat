"""DK-38 optional entrant fields

Revision ID: 5edaaf840f39
Revises: e2a5c9d14b7f
Create Date: 2026-07-02 00:00:00.000000

ІПН абітурієнта (persons.mokpp) стає необов'язковим — електронні заяви часто його
не містять. Документ про освіту (document_about_education) отримує сурогатний PK
`id` замість складеного (title, number), бо number і date_of_issue теж стають
необов'язковими і більше не годяться на роль природного ключа.

Стратегія для document_about_education — переносиме перестворення таблиці
(create *_new + INSERT..SELECT + drop old + rename), однакове для SQLite (dev) і
MySQL/MariaDB (prod). Для persons.mokpp — ALTER COLUMN nullable через batch mode.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '5edaaf840f39'
down_revision: Union[str, Sequence[str], None] = 'e2a5c9d14b7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _str():
    return sqlmodel.sql.sqltypes.AutoString()


def upgrade() -> None:
    """Upgrade schema."""
    # 1. persons.mokpp -> nullable.
    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column('mokpp', existing_type=_str(), nullable=True)

    # 2. document_about_education -> сурогатний id, number/date_of_issue nullable.
    op.create_table(
        'document_about_education__new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', _str(), nullable=False),
        sa.Column('number', _str(), nullable=True),
        sa.Column('series', _str(), nullable=True),
        sa.Column('issued_by', sa.Text(), nullable=True),
        sa.Column('date_of_issue', _str(), nullable=True),
        sa.Column('id_person', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_person'], ['persons.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(sa.text(
        "INSERT INTO document_about_education__new "
        "(title, number, series, issued_by, date_of_issue, id_person) "
        "SELECT title, number, series, issued_by, date_of_issue, id_person "
        "FROM document_about_education"
    ))
    op.drop_table('document_about_education')
    op.rename_table('document_about_education__new', 'document_about_education')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'document_about_education__old',
        sa.Column('title', _str(), nullable=False),
        sa.Column('number', _str(), nullable=False),
        sa.Column('series', _str(), nullable=True),
        sa.Column('issued_by', sa.Text(), nullable=True),
        sa.Column('date_of_issue', _str(), nullable=False),
        sa.Column('id_person', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_person'], ['persons.id'], ),
        sa.PrimaryKeyConstraint('title', 'number'),
    )
    op.execute(sa.text(
        "INSERT INTO document_about_education__old "
        "(title, number, series, issued_by, date_of_issue, id_person) "
        "SELECT title, COALESCE(number, ''), series, issued_by, COALESCE(date_of_issue, ''), id_person "
        "FROM document_about_education"
    ))
    op.drop_table('document_about_education')
    op.rename_table('document_about_education__old', 'document_about_education')

    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column('mokpp', existing_type=_str(), nullable=False)
