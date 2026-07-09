"""Дії журналу для іспитів груп (entrants_exams, DK-55).

Скалярні поля дифаються автоматично; зміна складу відповідальних співробітників —
окреме поле `responsible_workers` (кількість/список id до-після), яке сервіс
виставляє вручну.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange


_EXAM_LABELS: Dict[str, str] = {
    "id_group": "Група (id)",
    "id_item_zno": "Предмет ЗНО (id)",
    "date": "Дата",
    "time_start": "Початок",
    "time_end": "Завершення",
    "description": "Опис/аудиторія",
    "responsible_workers": "Відповідальні (id)",
}


class ExamCreated(CreateAction):
    table_name: ClassVar[str] = "entrants_exams"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _EXAM_LABELS
    id_group: int
    id_item_zno: int
    date: str
    time_start: str
    time_end: str


class ExamUpdated(UpdateAction):
    table_name: ClassVar[str] = "entrants_exams"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _EXAM_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = (
        "id_group", "id_item_zno", "date", "time_start", "time_end", "description",
    )
    id_group: Optional[FieldChange] = None
    id_item_zno: Optional[FieldChange] = None
    date: Optional[FieldChange] = None
    time_start: Optional[FieldChange] = None
    time_end: Optional[FieldChange] = None
    description: Optional[FieldChange] = None
    responsible_workers: Optional[FieldChange] = None


class ExamDeleted(DeleteAction):
    table_name: ClassVar[str] = "entrants_exams"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _EXAM_LABELS
    id_group: int
    id_item_zno: int
    date: str
