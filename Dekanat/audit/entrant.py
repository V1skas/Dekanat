"""Дії журналу для картки абітурієнта (entrants, DK-55).

Один запис на збереження: diff скалярних полів особи (person) та абітурієнта
(entrant), зведених у спільний простір імен. Дочірні колекції (документи,
результати ЗНО, спеціальності тощо) не логуються поштучно — сервіс лише
позначає, які з них змінились, у полі `changed_collections`. Призначення
екзаменаційної групи — окремий запис (`GroupEntrantAssigned` у audit/entrants_group).
"""

from typing import ClassVar, Dict, List, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow


_ENTRANT_LABELS: Dict[str, str] = {
    "pib": "ПІБ",
    "edbo": "ЄДБО",
    "citizenship": "Громадянство",
    "sex": "Стать",
    "date_of_birth": "Дата народження",
    "place_of_registration_city": "Місто реєстрації",
    "place_of_registration": "Адреса реєстрації",
    "mokpp": "ІПН",
    "email": "Email",
    "phone_number": "Телефон",
    "the_need_for_a_dormitory": "Потреба в гуртожитку",
    "id_source_of_funding": "Джерело фінансування (id)",
    "id_entry_base": "База вступу (id)",
    "id_application_status": "Статус заявки (id)",
    "comment": "Коментар",
    "submitted_electronically": "Подано електронно",
    "id_entrant_group": "Екзаменаційна група (id)",
}

# Скалярні поля, що дифаються автоматично.
_ENTRANT_TRACKED: Tuple[str, ...] = (
    "pib", "edbo", "citizenship", "sex", "date_of_birth",
    "place_of_registration_city", "place_of_registration", "mokpp", "email",
    "phone_number", "the_need_for_a_dormitory", "id_source_of_funding",
    "id_entry_base", "id_application_status", "comment", "submitted_electronically",
    "id_entrant_group",
)


class EntrantCreated(CreateAction):
    table_name: ClassVar[str] = "entrants"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRANT_LABELS
    pib: str
    edbo: Optional[str] = None
    id_application_status: int


class EntrantUpdated(UpdateAction):
    table_name: ClassVar[str] = "entrants"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRANT_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = _ENTRANT_TRACKED
    pib: Optional[FieldChange] = None
    edbo: Optional[FieldChange] = None
    citizenship: Optional[FieldChange] = None
    sex: Optional[FieldChange] = None
    date_of_birth: Optional[FieldChange] = None
    place_of_registration_city: Optional[FieldChange] = None
    place_of_registration: Optional[FieldChange] = None
    mokpp: Optional[FieldChange] = None
    email: Optional[FieldChange] = None
    phone_number: Optional[FieldChange] = None
    the_need_for_a_dormitory: Optional[FieldChange] = None
    id_source_of_funding: Optional[FieldChange] = None
    id_entry_base: Optional[FieldChange] = None
    id_application_status: Optional[FieldChange] = None
    comment: Optional[FieldChange] = None
    submitted_electronically: Optional[FieldChange] = None
    id_entrant_group: Optional[FieldChange] = None
    # Перелік дочірніх колекцій, що змінились (укр. підписи). Виставляє сервіс.
    changed_collections: Optional[List[str]] = None

    def has_changes(self) -> bool:
        return super().has_changes() or bool(self.changed_collections)

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.changed_collections:
            lines.append("Оновлено дані: " + ", ".join(self.changed_collections))
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.changed_collections:
            rows.append(FieldRow(label="Оновлено дані", new=", ".join(self.changed_collections)))
        return rows


class EntrantDeleted(DeleteAction):
    table_name: ClassVar[str] = "entrants"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRANT_LABELS
    pib: str
    edbo: Optional[str] = None
