"""DK-55 audit_log

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-08 10:00:00.000000

Журнал дій користувачів (audit_log, DK-55): хто (id_worker), коли (created_at),
що (action + table_name + record_id) і як саме змінив (changes — JSON payload
декларативної дії з Dekanat/audit). record_id — рядок, бо в проєкті є
composite/строкові PK. Індекс по (table_name, record_id) — під запит історії
конкретного запису, по created_at — під хронологічне сортування.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_worker', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('table_name', sa.String(length=255), nullable=False),
        sa.Column('record_id', sa.String(length=255), nullable=False),
        sa.Column('changes', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['id_worker'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_record', 'audit_log', ['table_name', 'record_id'], unique=False)
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_record', table_name='audit_log')
    op.drop_table('audit_log')
