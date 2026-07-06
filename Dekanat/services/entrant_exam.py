import reflex as rx

from datetime import datetime
from typing import Optional, Sequence, List, Tuple, Dict

from Dekanat.dao.entrant_exam import EntrantExamDao
from Dekanat.models import EntrantExamModel


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

    def add_one(self, item: EntrantExamModel, worker_ids: List[int]) -> EntrantExamModel:
        try:
            with rx.session() as session:
                managed = EntrantExamDao.add_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantExamModel, worker_ids: List[int]) -> EntrantExamModel:
        try:
            with rx.session() as session:
                managed = EntrantExamDao.edit_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantExamModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantExamDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantExamService][delete_one][ERROR] {e}")
            return False
