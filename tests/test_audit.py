"""Тести журналу дій (DK-55).

Перевіряють, що `record_action` пише коректний рядок у `audit_log`, що
`parse_changes` відновлює типізовану дію, `describe()` дає читабельний текст, і
що порожній diff (update без змін) не логується.
"""

from types import SimpleNamespace

from sqlmodel import SQLModel, Session, create_engine, select

# Імпорт моделей реєструє таблиці у SQLModel.metadata.
import Dekanat.models  # noqa: F401
from Dekanat.models import AuditLogModel, WorkerModel
from Dekanat.audit import record_action, parse_changes, KinshipUpdated


def _session() -> Session:
    """Свіжа in-memory БД зі схемою (ізольована на кожен виклик)."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _actor(session: Session, login: str) -> WorkerModel:
    worker = WorkerModel(pib="Тестовий Актор", login=login, password="x", password_salt="y")
    session.add(worker)
    session.flush()
    return worker


def test_record_action_writes_row():
    with _session() as session:
        actor = _actor(session, "actor1")
        action = KinshipUpdated.from_diff(
            SimpleNamespace(title="Батько"), SimpleNamespace(title="Мати")
        )
        record_action(session, actor.id, "5", action)
        session.commit()

        rows = session.exec(select(AuditLogModel)).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.id_worker == actor.id
        assert row.action == "update"
        assert row.table_name == "kinship"
        assert row.record_id == "5"
        # changes — JSON лише зі зміненим полем і старим/новим значенням.
        assert "Батько" in row.changes and "Мати" in row.changes
        assert '"title"' in row.changes


def test_parse_changes_roundtrip_and_describe():
    with _session() as session:
        actor = _actor(session, "actor2")
        record_action(
            session, actor.id, "7",
            KinshipUpdated.from_diff(SimpleNamespace(title="A"), SimpleNamespace(title="B")),
        )
        session.commit()

        row = session.exec(select(AuditLogModel)).one()
        action = parse_changes(row)
        assert isinstance(action, KinshipUpdated)
        assert action.title is not None
        assert action.title.old == "A"
        assert action.title.new == "B"
        assert action.describe() == ["Назва: A → B"]


def test_update_without_changes_is_not_logged():
    with _session() as session:
        actor = _actor(session, "actor3")
        record_action(
            session, actor.id, "9",
            KinshipUpdated.from_diff(SimpleNamespace(title="X"), SimpleNamespace(title="X")),
        )
        session.commit()
        assert session.exec(select(AuditLogModel)).all() == []
