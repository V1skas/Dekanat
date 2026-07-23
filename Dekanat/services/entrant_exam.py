import reflex as rx

from datetime import datetime
from types import SimpleNamespace
from typing import Optional, Sequence, List, Tuple, Dict

from sqlmodel import select

from Dekanat.dao.entrant_exam import EntrantExamDao
from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.dao.item_zno import ItemZnoDao
from Dekanat.dao.worker import WorkerDao
from Dekanat.models import EntrantExamModel, EntrantExamWorkerModel
from Dekanat.audit import (
    record_action,
    diff_string_list,
    ExamCreated,
    ExamUpdated,
    ExamDeleted,
)


def _group_title(id_group: Optional[int], session) -> str:
    if id_group is None:
        return ""
    group = EntrantsGroupDao.get_by_id(id_group, session, with_del=True)
    return group.title if group is not None else f"#{id_group}"


def _item_zno_title(id_item_zno: Optional[int], session) -> str:
    if id_item_zno is None:
        return ""
    item = ItemZnoDao.get_by_id(id_item_zno, session, with_del=True)
    return item.title if item is not None else f"#{id_item_zno}"


def _worker_pib_map(session) -> Dict[int, str]:
    return {w.id: w.pib for w in WorkerDao.get_all(session, with_del=True)}


# День тижня українською за Python-індексом (Пн=0 … Нд=6).
_UA_WEEKDAYS = [
    "Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя",
]

# Форма навчання → фраза для підзаголовка-відділення розкладу (DK-46).
_FORM_DIVISION = {
    "Денна": "денне відділення",
    "Заочна": "заочне відділення",
}


def _weekday_ua(date_str: Optional[str]) -> str:
    """'2026-07-28' → 'Вівторок'. Невідоме → ''."""
    if not date_str:
        return ""
    try:
        return _UA_WEEKDAYS[datetime.strptime(date_str[:10], "%Y-%m-%d").weekday()]
    except (ValueError, TypeError, IndexError):
        return ""


def _fmt_date(date_str: Optional[str]) -> str:
    """'2026-07-28' → '28.07.2026'. Невідоме → як є."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return date_str


def _subtitle_from_forms(forms: Sequence[str]) -> str:
    """Підзаголовок «(… відділення)» за формами навчання груп. Якщо форма одна —
    показуємо її; якщо їх декілька або жодної — підзаголовок порожній (DK-46)."""
    distinct = sorted({f for f in forms if f})
    if len(distinct) != 1:
        return ""
    title = distinct[0]
    phrase = _FORM_DIVISION.get(title, f"{title.lower()} відділення")
    return f"({phrase})"


class EntrantExamService:
    def get_list_items(
        self,
        id_group: Optional[int] = None,
        id_item_zno: Optional[int] = None,
        id_worker: Optional[int] = None,
        date_between: Optional[Tuple[str, str]] = None,
    ) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_all(
                    session,
                    id_group=id_group,
                    id_item_zno=id_item_zno,
                    id_worker=id_worker,
                    date_between=date_between,
                )
        except Exception as e:
            print(f"[EntrantExamService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantExamService][get_by_id][ERROR] {e}")
            raise

    def get_schedule_payload(self, exam_ids: Sequence[int]) -> Dict:
        """Payload для `ExamScheduleReport(**payload)` (DK-46): рядки розкладу за
        обраними іспитами + підзаголовок-відділення. Read-only — придатне до
        виклику у фоновому потоці (`run_blocking`)."""
        try:
            with rx.session() as session:
                exams = EntrantExamDao.get_by_ids(exam_ids, session)
                group_ids = sorted({e.id_group for e in exams if e.id_group})
                forms = EntrantExamDao.get_forms_of_study_for_groups(group_ids, session)
                rows = [
                    {
                        "group": e.group.title if e.group is not None else "—",
                        "weekday": _weekday_ua(e.date),
                        "date": _fmt_date(e.date),
                        "time": e.time_start or "",
                        "auditorium": (e.description or "").strip() or "-",
                    }
                    for e in exams
                ]
            return {
                "subtitle": _subtitle_from_forms(forms),
                "file_stem": "Розклад іспитів",
                "rows": rows,
            }
        except Exception as e:
            print(f"[EntrantExamService][get_schedule_payload][ERROR] {e}")
            raise

    def get_by_group(self, group_id: int) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantExamService][get_by_group][ERROR] {e}")
            raise

    def add_one(self, item: EntrantExamModel, worker_ids: List[int], actor_id: Optional[int] = None) -> EntrantExamModel:
        try:
            with rx.session() as session:
                managed = EntrantExamDao.add_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)
                record_action(session, actor_id, managed.id, ExamCreated(
                    id_group=_group_title(managed.id_group, session),
                    id_item_zno=_item_zno_title(managed.id_item_zno, session),
                    date=managed.date,
                    time_start=managed.time_start,
                    time_end=managed.time_end,
                ))
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantExamModel, worker_ids: List[int], actor_id: Optional[int] = None) -> EntrantExamModel:
        try:
            with rx.session() as session:
                # Старий стан читаємо БЕЗ eager-load: `session.get` тягне лише рядок,
                # а список відповідальних — окремим скалярним запитом по M2M. Інакше
                # `get_by_id` підвантажив би `item_zno`/`group`/`responsible_workers`
                # у пишучу сесію, і `session.merge(item)` (item несе ці ж relationship)
                # впав би на identity-map конфлікті (як у картці абітурієнта) — DK-55.
                old = session.get(EntrantExamModel, item.id)
                old_snap = SimpleNamespace(
                    id_group=_group_title(old.id_group, session) if old else None,
                    id_item_zno=_item_zno_title(old.id_item_zno, session) if old else None,
                    date=old.date if old else None,
                    time_start=old.time_start if old else None,
                    time_end=old.time_end if old else None,
                    description=old.description if old else None,
                )
                old_worker_ids = sorted(session.exec(
                    select(EntrantExamWorkerModel.id_worker).where(EntrantExamWorkerModel.id_exam == item.id)
                ).all()) if old is not None else []
                managed = EntrantExamDao.edit_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)

                pib_map = _worker_pib_map(session)
                new_snap = SimpleNamespace(
                    id_group=_group_title(managed.id_group, session),
                    id_item_zno=_item_zno_title(managed.id_item_zno, session),
                    date=managed.date, time_start=managed.time_start,
                    time_end=managed.time_end, description=managed.description,
                )
                action = ExamUpdated.from_diff(old_snap, new_snap)
                old_pibs = sorted(pib_map.get(wid, f"#{wid}") for wid in old_worker_ids)
                new_pibs = sorted(pib_map.get(wid, f"#{wid}") for wid in sorted(worker_ids))
                workers_change = diff_string_list("Відповідальні", old_pibs, new_pibs)
                if workers_change.has_changes():
                    action.responsible_workers = workers_change
                record_action(session, actor_id, item.id, action)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantExamModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantExamDao.edit_one(item, session)
                record_action(session, actor_id, item.id, ExamDeleted(
                    id_group=_group_title(item.id_group, session),
                    id_item_zno=_item_zno_title(item.id_item_zno, session),
                    date=item.date,
                ))
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantExamService][delete_one][ERROR] {e}")
            return False
