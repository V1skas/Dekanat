"""DK-52 dynamic financing resources

Revision ID: cf50e0fe0c8a
Revises: b8abb96cbdb9
Create Date: 2026-07-09 13:00:00.000000

Прибирає жорстко прописану бінарну "бюджет/контракт" і робить ресурс
фінансування повноцінним динамічним довідником (`source_of_funding`):

1. `source_of_funding` — нові поля `sequence` (пріоритет у конкурсі) і `color`
   (підсвітка в рейтингу). Бекфіл на проді: id=1 "Державне замовлення" -> 1,
   id=2 "Кошти фізичних осіб" -> 2 (той самий порядок, що й budget/contract
   раніше).
2. `source_of_funding_eligibility` — нова M2M-таблиця (самопосилання): у
   конкурс яких ще ресурсів може претендувати власник ресурсу. Бекфіл: ресурс
   1 ("бюджет") також конкурує за 2 ("контракт") — один в один як і було
   раніше (бюджет -> контракт по лічильниках).
3. `admission_campaigns_specialties_funding` — нова дочірня таблиця квоти:
   кількість місць по кожному ресурсу фінансування замість двох жорстких
   колонок. Бекфіл із `budget_places`/`contract_places` під id=1/id=2.
4. `admission_campaigns_specialties.budget_places`/`.contract_places` —
   видаляються (перенесені у (3)).
5. `rating_entries` — замість `status IN ('budget','contract',...)`: нові
   `id_source_of_funding` (група/таблиця рейтингу) та
   `id_assigned_source_of_funding` (фактичний ресурс, у конкурс якого
   потрапив абітурієнт). Бекфіл існуючих рядків:
   - status='budget'   -> id_source_of_funding=1, id_assigned=1, status='assigned'
   - status='contract' -> id_source_of_funding=2, id_assigned=2, status='assigned'
   - status='kvota'    -> id_source_of_funding=1, id_assigned=1 (status лишається 'kvota')
   - status IN ('rejected','excluded') -> id_source_of_funding з
     `persons.id_source_of_funding` абітурієнта (join), id_assigned=NULL.

Мапінг id=1/id=2 підтверджений вручну на проді (MariaDB): у
`source_of_funding` там рівно два записи — 1 "Державне замовлення",
2 "Кошти фізичних осіб" — саме вони відповідають старим budget/contract.

Перед прогоном на проді — обов'язково бекап БД.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cf50e0fe0c8a'
down_revision: Union[str, Sequence[str], None] = 'b8abb96cbdb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1. source_of_funding: sequence + color.
    with op.batch_alter_table('source_of_funding', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('color', sa.String(length=20), nullable=False, server_default='#22c55e'))
    op.execute(sa.text("UPDATE source_of_funding SET sequence = 1, color = '#22c55e' WHERE id = 1"))
    op.execute(sa.text("UPDATE source_of_funding SET sequence = 2, color = '#f97316' WHERE id = 2"))

    # 2. source_of_funding_eligibility — нова M2M-таблиця (self-join).
    op.create_table(
        'source_of_funding_eligibility',
        sa.Column('id_source_of_funding', sa.Integer(), nullable=False),
        sa.Column('id_eligible_source_of_funding', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_source_of_funding'], ['source_of_funding.id']),
        sa.ForeignKeyConstraint(['id_eligible_source_of_funding'], ['source_of_funding.id']),
        sa.PrimaryKeyConstraint('id_source_of_funding', 'id_eligible_source_of_funding'),
    )
    op.execute(sa.text(
        "INSERT INTO source_of_funding_eligibility (id_source_of_funding, id_eligible_source_of_funding) "
        "SELECT 1, 2 WHERE EXISTS (SELECT 1 FROM source_of_funding WHERE id = 1) "
        "AND EXISTS (SELECT 1 FROM source_of_funding WHERE id = 2)"
    ))

    # 3. admission_campaigns_specialties_funding — дочірня таблиця квоти.
    op.create_table(
        'admission_campaigns_specialties_funding',
        sa.Column('id_admission_campaign', sa.Integer(), nullable=False),
        sa.Column('id_speciality', sa.Integer(), nullable=False),
        sa.Column('id_entry_base', sa.Integer(), nullable=False),
        sa.Column('id_form_of_study', sa.Integer(), nullable=False),
        sa.Column('id_source_of_funding', sa.Integer(), nullable=False),
        sa.Column('places', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['id_admission_campaign', 'id_speciality', 'id_entry_base', 'id_form_of_study'],
            [
                'admission_campaigns_specialties.id_admission_campaign',
                'admission_campaigns_specialties.id_speciality',
                'admission_campaigns_specialties.id_entry_base',
                'admission_campaigns_specialties.id_form_of_study',
            ],
        ),
        sa.ForeignKeyConstraint(['id_source_of_funding'], ['source_of_funding.id']),
        sa.PrimaryKeyConstraint(
            'id_admission_campaign', 'id_speciality', 'id_entry_base', 'id_form_of_study', 'id_source_of_funding'
        ),
    )
    op.execute(sa.text(
        "INSERT INTO admission_campaigns_specialties_funding "
        "(id_admission_campaign, id_speciality, id_entry_base, id_form_of_study, id_source_of_funding, places) "
        "SELECT id_admission_campaign, id_speciality, id_entry_base, id_form_of_study, 1, budget_places "
        "FROM admission_campaigns_specialties"
    ))
    op.execute(sa.text(
        "INSERT INTO admission_campaigns_specialties_funding "
        "(id_admission_campaign, id_speciality, id_entry_base, id_form_of_study, id_source_of_funding, places) "
        "SELECT id_admission_campaign, id_speciality, id_entry_base, id_form_of_study, 2, contract_places "
        "FROM admission_campaigns_specialties"
    ))

    # 4. Прибираємо старі жорсткі колонки квоти.
    with op.batch_alter_table('admission_campaigns_specialties', schema=None) as batch_op:
        batch_op.drop_column('budget_places')
        batch_op.drop_column('contract_places')

    # 5. rating_entries: нові колонки ресурсу + бекфіл існуючих рядків.
    with op.batch_alter_table('rating_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_source_of_funding', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('id_assigned_source_of_funding', sa.Integer(), nullable=True))

    op.execute(sa.text(
        "UPDATE rating_entries SET id_source_of_funding = 1, id_assigned_source_of_funding = 1, "
        "status = 'assigned' WHERE status = 'budget'"
    ))
    op.execute(sa.text(
        "UPDATE rating_entries SET id_source_of_funding = 2, id_assigned_source_of_funding = 2, "
        "status = 'assigned' WHERE status = 'contract'"
    ))
    op.execute(sa.text(
        "UPDATE rating_entries SET id_source_of_funding = 1, id_assigned_source_of_funding = 1 "
        "WHERE status = 'kvota'"
    ))
    op.execute(sa.text(
        "UPDATE rating_entries SET id_source_of_funding = ("
        "  SELECT p.id_source_of_funding FROM persons p "
        "  WHERE p.id = rating_entries.id_entrant"
        ") WHERE status IN ('rejected', 'excluded')"
    ))
    # Рядки без визначеного ресурсу (не мали відповідного абітурієнта чи
    # особи) — прив'язуємо до ресурсу з sequence=1, щоб задовольнити NOT NULL.
    op.execute(sa.text(
        "UPDATE rating_entries SET id_source_of_funding = "
        "(SELECT id FROM source_of_funding ORDER BY sequence LIMIT 1) "
        "WHERE id_source_of_funding IS NULL"
    ))

    with op.batch_alter_table('rating_entries', schema=None) as batch_op:
        batch_op.alter_column('id_source_of_funding', existing_type=sa.Integer(), nullable=False)
        if dialect == 'sqlite':
            batch_op.create_foreign_key(
                'fk_rating_entries_source_of_funding', 'source_of_funding', ['id_source_of_funding'], ['id']
            )
            batch_op.create_foreign_key(
                'fk_rating_entries_assigned_source_of_funding', 'source_of_funding',
                ['id_assigned_source_of_funding'], ['id'],
            )
    if dialect != 'sqlite':
        op.create_foreign_key(
            'fk_rating_entries_source_of_funding', 'rating_entries', 'source_of_funding',
            ['id_source_of_funding'], ['id'],
        )
        op.create_foreign_key(
            'fk_rating_entries_assigned_source_of_funding', 'rating_entries', 'source_of_funding',
            ['id_assigned_source_of_funding'], ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect != 'sqlite':
        op.drop_constraint('fk_rating_entries_assigned_source_of_funding', 'rating_entries', type_='foreignkey')
        op.drop_constraint('fk_rating_entries_source_of_funding', 'rating_entries', type_='foreignkey')

    op.execute(sa.text(
        "UPDATE rating_entries SET status = 'budget' WHERE status = 'assigned' AND id_assigned_source_of_funding = 1"
    ))
    op.execute(sa.text(
        "UPDATE rating_entries SET status = 'contract' WHERE status = 'assigned' AND id_assigned_source_of_funding = 2"
    ))

    with op.batch_alter_table('rating_entries', schema=None) as batch_op:
        batch_op.drop_column('id_assigned_source_of_funding')
        batch_op.drop_column('id_source_of_funding')

    with op.batch_alter_table('admission_campaigns_specialties', schema=None) as batch_op:
        batch_op.add_column(sa.Column('budget_places', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('contract_places', sa.Integer(), nullable=False, server_default='0'))

    op.execute(sa.text(
        "UPDATE admission_campaigns_specialties SET budget_places = ("
        "  SELECT places FROM admission_campaigns_specialties_funding f WHERE "
        "  f.id_admission_campaign = admission_campaigns_specialties.id_admission_campaign AND "
        "  f.id_speciality = admission_campaigns_specialties.id_speciality AND "
        "  f.id_entry_base = admission_campaigns_specialties.id_entry_base AND "
        "  f.id_form_of_study = admission_campaigns_specialties.id_form_of_study AND "
        "  f.id_source_of_funding = 1"
        ")"
    ))
    op.execute(sa.text(
        "UPDATE admission_campaigns_specialties SET contract_places = ("
        "  SELECT places FROM admission_campaigns_specialties_funding f WHERE "
        "  f.id_admission_campaign = admission_campaigns_specialties.id_admission_campaign AND "
        "  f.id_speciality = admission_campaigns_specialties.id_speciality AND "
        "  f.id_entry_base = admission_campaigns_specialties.id_entry_base AND "
        "  f.id_form_of_study = admission_campaigns_specialties.id_form_of_study AND "
        "  f.id_source_of_funding = 2"
        ")"
    ))

    op.drop_table('admission_campaigns_specialties_funding')
    op.drop_table('source_of_funding_eligibility')

    with op.batch_alter_table('source_of_funding', schema=None) as batch_op:
        batch_op.drop_column('color')
        batch_op.drop_column('sequence')
