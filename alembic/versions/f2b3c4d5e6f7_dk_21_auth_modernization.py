"""DK-21 auth modernization

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-05-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Додає:
    - `workers.permissions_version` — лічильник, який бампиться при зміні прав/ролей
      користувача; AppState порівнює його зі своїм кешованим значенням і
      перечитує `actions_worker` при невідповідності.
    - `auth_tokens.expires_at`, `auth_tokens.last_activity_at` — підтримка
      ковзаючого вікна сесії; протермінований токен видаляється ліниво.
    - `app_settings` — типізована таблиця ключ-значення для адмін-настройок,
      розбита на категорії (наразі лише «auth» з ключем session_timeout_minutes).
    """
    with op.batch_alter_table('workers') as batch_op:
        batch_op.add_column(sa.Column('permissions_version', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('auth_tokens') as batch_op:
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))
        batch_op.add_column(sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))

    op.create_table(
        'app_settings',
        sa.Column('key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('value', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('value_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('app_settings')
    with op.batch_alter_table('auth_tokens') as batch_op:
        batch_op.drop_column('last_activity_at')
        batch_op.drop_column('expires_at')
    with op.batch_alter_table('workers') as batch_op:
        batch_op.drop_column('permissions_version')
