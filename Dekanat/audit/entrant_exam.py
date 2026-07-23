"""Дії журналу для іспитів груп (entrants_exams, DK-55/DK-66).

Скалярні поля дифаються автоматично; `id_group`/`id_item_zno` дифаються вже як
резолвлені назви (сервіс підставляє назву замість id — DK-66). Зміна складу
відповідальних співробітників — окреме поле `responsible_workers`
(`CollectionChange` — додані/вилучені ПІБ), яке сервіс виставляє вручну.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow, CollectionChange


_EXAM_LABELS: Dict[str, str] = {
    "id_group": "Група",
    "id_item_zno": "Предмет ЗНО",
    "date": "Дата",
    "time_start": "Початок",
    "time_end": "Завершення",
    "description": "Опис/аудиторія",
    "responsible_workers": "Відповідальні",
}


class ExamCreated(CreateAction):
    table_name: ClassVar[str] = "entrants_exams"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _EXAM_LABELS
    id_group: str  # назва групи (DK-66)
    id_item_zno: str  # назва предмета ЗНО (DK-66)
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
    responsible_workers: Optional[CollectionChange] = None

    def has_changes(self) -> bool:
        return super().has_changes() or (
            self.responsible_workers is not None and self.responsible_workers.has_changes()
        )

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.responsible_workers is not None and self.responsible_workers.has_changes():
            if self.responsible_workers.added:
                lines.append("Додано відповідальних: " + ", ".join(self.responsible_workers.added))
            if self.responsible_workers.removed:
                lines.append("Вилучено відповідальних: " + ", ".join(self.responsible_workers.removed))
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.responsible_workers is not None:
            rows.extend(self.responsible_workers.field_rows())
        return rows


class ExamDeleted(DeleteAction):
    table_name: ClassVar[str] = "entrants_exams"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _EXAM_LABELS
    id_group: str
    id_item_zno: str
    date: str
