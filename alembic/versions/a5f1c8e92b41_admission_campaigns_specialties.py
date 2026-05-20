"""admission_campaigns_specialties: per-campaign speciality quotas

Revision ID: a5f1c8e92b41
Revises: 56e978fcf807
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'a5f1c8e92b41'
down_revision: Union[str, Sequence[str], None] = '56e978fcf807'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('admission_campaigns_specialties')
