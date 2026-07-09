"""Тест DK-57: кілька документів по одній і тій же пільзі.

Перевіряє, що `EntrantDao.replace_special_conditions` більше не падає на
UNIQUE-конфлікті, коли особа отримує два записи з однаковим
`id_special_condition` (різні номер/дата видачі) — до DK-57 композитний PK
(id_person, id_special_condition) це забороняв.
"""

from sqlmodel import SQLModel, Session, create_engine, select

# Імпорт моделей реєструє таблиці у SQLModel.metadata.
import Dekanat.models as m
from Dekanat.dao.entrant import EntrantDao


def _session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_replace_special_conditions_allows_duplicate_condition():
    with _session() as session:
        session.add(m.SpecialConditionModel(subcategory_code="X1", title="Test", is_kvota=False))
        person = m.PersonModel(
            pib="Т", citizenship="UA", sex="Ч", date_of_birth="2000-01-01",
            place_of_registration="addr", phone_number="1", the_need_for_a_dormitory=False,
            id_source_of_funding=1, id_entry_base=1, email=None,
        )
        session.add(person)
        session.flush()

        items = [
            m.SpecialConditionPersonModel(id_person=person.id, id_special_condition="X1", number="A1", date_of_issue="2020-01-01"),
            m.SpecialConditionPersonModel(id_person=person.id, id_special_condition="X1", number="A2", date_of_issue="2021-01-01"),
        ]
        EntrantDao.replace_special_conditions(person.id, items, session)
        session.commit()

        rows = session.exec(
            select(m.SpecialConditionPersonModel).where(m.SpecialConditionPersonModel.id_person == person.id)
        ).all()
        assert len(rows) == 2
        assert {r.number for r in rows} == {"A1", "A2"}
        assert all(r.id_special_condition == "X1" for r in rows)
        # id — сурогатний і унікальний для кожного рядка.
        assert len({r.id for r in rows}) == 2


def test_replace_special_conditions_resets_ids_on_second_call():
    """Повторний виклик (напр. друге редагування картки) не повинен
    конфліктувати зі старими id, перенесеними з detached-обʼєктів."""
    with _session() as session:
        session.add(m.SpecialConditionModel(subcategory_code="X1", title="Test", is_kvota=False))
        person = m.PersonModel(
            pib="Т", citizenship="UA", sex="Ч", date_of_birth="2000-01-01",
            place_of_registration="addr", phone_number="1", the_need_for_a_dormitory=False,
            id_source_of_funding=1, id_entry_base=1, email=None,
        )
        session.add(person)
        session.flush()

        EntrantDao.replace_special_conditions(
            person.id,
            [m.SpecialConditionPersonModel(id_person=person.id, id_special_condition="X1", number="A1", date_of_issue="2020-01-01")],
            session,
        )
        session.commit()

        saved = session.exec(
            select(m.SpecialConditionPersonModel).where(m.SpecialConditionPersonModel.id_person == person.id)
        ).all()
        # Симулюємо повторне редагування: state передає ті самі завантажені
        # обʼєкти (з непорожнім .id) назад у replace_*.
        EntrantDao.replace_special_conditions(person.id, list(saved), session)
        session.commit()

        rows = session.exec(
            select(m.SpecialConditionPersonModel).where(m.SpecialConditionPersonModel.id_person == person.id)
        ).all()
        assert len(rows) == 1
        assert rows[0].number == "A1"
