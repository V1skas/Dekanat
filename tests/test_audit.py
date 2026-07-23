"""Тести журналу дій (DK-55/DK-56).

Перевіряють, що `record_action` пише коректний рядок у `audit_log`, що
`parse_changes` відновлює типізовану дію, `describe()`/`field_rows()` дають
читабельний текст/структуровану деталізацію, і що порожній diff (update без
змін) не логується.
"""

from types import SimpleNamespace

from sqlmodel import SQLModel, Session, create_engine, select

# Імпорт моделей реєструє таблиці у SQLModel.metadata.
import Dekanat.models  # noqa: F401
from Dekanat.models import AuditLogModel, WorkerModel
from Dekanat.audit import (
    record_action, parse_changes, KinshipUpdated, KinshipCreated,
    diff_collection, diff_string_list, CollectionChange, EntrantUpdated,
)


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


def test_field_rows_update_and_create():
    """DK-56: структурована деталізація для UI (label/old/new замість plain text)."""
    update = KinshipUpdated.from_diff(SimpleNamespace(title="Батько"), SimpleNamespace(title="Мати"))
    rows = update.field_rows()
    assert len(rows) == 1
    assert rows[0].label == "Назва"
    assert rows[0].old == "Батько"
    assert rows[0].new == "Мати"

    created = KinshipCreated(title="Дядько")
    rows = created.field_rows()
    assert rows[0].label == "" and rows[0].text == "Створено запис"
    assert rows[1].label == "Назва" and rows[1].new == "Дядько" and rows[1].old == ""


def test_update_without_changes_is_not_logged():
    with _session() as session:
        actor = _actor(session, "actor3")
        record_action(
            session, actor.id, "9",
            KinshipUpdated.from_diff(SimpleNamespace(title="X"), SimpleNamespace(title="X")),
        )
        session.commit()
        assert session.exec(select(AuditLogModel)).all() == []


def _row(id_key, identity: str, value=None) -> dict:
    return {"id_key": id_key, "identity": identity, "value": value}


def test_diff_collection_added_removed_edited():
    """DK-66: поштучний diff колекції — added/removed/edited за id_key, з
    порівнянням value лише коли воно є в обох рядках."""
    old_rows = [
        _row(1, "Математика", "90"),
        _row(2, "Фізика", "80"),
    ]
    new_rows = [
        _row(1, "Математика", "95"),   # значення змінилось → edited
        _row(3, "Хімія", "70"),        # новий рядок → added
    ]
    change = diff_collection("Результати", old_rows, new_rows)
    assert change.added == ["Хімія"]
    assert change.removed == ["Фізика"]
    assert len(change.edited) == 1
    assert change.edited[0].label == "Математика"
    assert change.edited[0].old == "90"
    assert change.edited[0].new == "95"
    assert change.has_changes()


def test_diff_collection_no_changes():
    rows = [_row(1, "Математика", "90")]
    change = diff_collection("Результати", rows, rows)
    assert not change.has_changes()
    assert change.field_rows() == []


def test_diff_collection_without_value_is_add_remove_only():
    """Без стабільного `value` (природний ключ без FK) будь-яка зміна рядка —
    видалення старого + додавання нового, ніколи не `edited`."""
    old_rows = [_row(("Диплом", "123"), "Диплом № 123")]
    new_rows = [_row(("Диплом", "124"), "Диплом № 124")]
    change = diff_collection("Документи про освіту", old_rows, new_rows)
    assert change.added == ["Диплом № 124"]
    assert change.removed == ["Диплом № 123"]
    assert change.edited == []


def test_diff_string_list_added_removed():
    change = diff_string_list("Ролі", ["Адміністратор"], ["Адміністратор", "Куратор"])
    assert change.added == ["Куратор"]
    assert change.removed == []
    assert change.has_changes()


def test_collection_change_field_rows_rendering():
    change = CollectionChange(label="Спеціальності", added=["Інформатика"], removed=["Право"])
    rows = change.field_rows()
    assert rows[0].label == "" and rows[0].text == "Спеціальності:"
    assert any(r.new == "Інформатика" for r in rows)
    assert any(r.old == "Право" for r in rows)


def test_entrant_updated_collection_changes_roundtrip():
    """DK-66: `collection_changes` (поштучний diff) переживає JSON-серіалізацію
    і повертається типізованим після `parse_changes`."""
    with _session() as session:
        actor = _actor(session, "actor4")
        action = EntrantUpdated.from_diff(
            SimpleNamespace(pib="Іваненко"), SimpleNamespace(pib="Іваненко"),
        )
        action.collection_changes = [
            CollectionChange(label="Спеціальності", added=["Інформатика (Денна)"]),
        ]
        record_action(session, actor.id, "42", action)
        session.commit()

        row = session.exec(select(AuditLogModel)).one()
        parsed = parse_changes(row)
        assert isinstance(parsed, EntrantUpdated)
        assert parsed.collection_changes is not None
        assert parsed.collection_changes[0].added == ["Інформатика (Денна)"]
        assert parsed.has_changes()


def test_entrant_updated_legacy_changed_collections_still_parses():
    """Старі записи (до DK-66) мали лише `changed_collections` (перелік назв,
    без деталізації) — має й далі парситись і рендеритись без падіння."""
    with _session() as session:
        actor = _actor(session, "actor5")
        action = EntrantUpdated.from_diff(
            SimpleNamespace(pib="Петренко"), SimpleNamespace(pib="Петренко"),
        )
        action.changed_collections = ["Спеціальності", "Результати ЗНО"]
        record_action(session, actor.id, "43", action)
        session.commit()

        row = session.exec(select(AuditLogModel)).one()
        parsed = parse_changes(row)
        assert isinstance(parsed, EntrantUpdated)
        assert parsed.changed_collections == ["Спеціальності", "Результати ЗНО"]
        rows = parsed.field_rows()
        assert any(r.label == "Оновлено дані" for r in rows)
