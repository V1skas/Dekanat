"""DK-25 admission campaign reports

Revision ID: a3b4c5d6e7f8
Revises: f2b3c4d5e6f7
Create Date: 2026-05-24 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Створює таблицю `admission_campaign_reports` — знімок звіту по кампанії
    (числа за день/тиждень/період + серії + розподіл по специальностях у JSON-полі).
    """
    op.create_table(
        'admission_campaign_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_campaign', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('payload', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['id_campaign'], ['admission_campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('admission_campaign_reports')
