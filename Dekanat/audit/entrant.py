"""Дії журналу для картки абітурієнта (entrants, DK-55/DK-66).

Один запис на збереження: diff скалярних полів особи (person) та абітурієнта
(entrant), зведених у спільний простір імен. FK-поля (`id_source_of_funding`,
`id_entry_base`, `id_application_status`, `id_entrant_group`) дифаються вже як
резолвлені назви (сервіс підставляє назву замість id — DK-66), тому в
`FieldChange` тут лежать рядки, а не числа.

Дочірні колекції (документи, результати ЗНО, спеціальності тощо) логуються
поштучно через `collection_changes` (список `CollectionChange` — додано/
вилучено/відредаговано, DK-66). Легасі-поле `changed_collections` (лише
перелік назв колекцій, що змінились) лишено для читання старих записів
журналу — нові записи його не заповнюють. Призначення екзаменаційної групи —
окремий запис (`GroupEntrantAssigned` у audit/entrants_group).
"""

from typing import ClassVar, Dict, List, Optional, Tuple

from Dekanat.audit.base import (
    CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow, CollectionChange,
)


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
    "id_source_of_funding": "Джерело фінансування",
    "id_entry_base": "База вступу",
    "id_application_status": "Статус заявки",
    "comment": "Коментар",
    "submitted_electronically": "Подано електронно",
    "id_entrant_group": "Екзаменаційна група",
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
    id_application_status: str  # назва статусу (DK-66), не id


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
    # Легасі (DK-55) — перелік назв колекцій, що змінились, без деталізації.
    # Нові записи його не заповнюють; лишено для читання старих логів.
    changed_collections: Optional[List[str]] = None
    # Поштучні diff'и дочірніх колекцій (DK-66) — added/removed/edited з назвами.
    collection_changes: Optional[List[CollectionChange]] = None

    def has_changes(self) -> bool:
        return (
            super().has_changes()
            or bool(self.changed_collections)
            or any(c.has_changes() for c in (self.collection_changes or []))
        )

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.changed_collections:
            lines.append("Оновлено дані: " + ", ".join(self.changed_collections))
        for c in self.collection_changes or []:
            if c.has_changes():
                lines.append(f"{c.label}: додано {len(c.added)}, вилучено {len(c.removed)}, змінено {len(c.edited)}")
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.changed_collections:
            rows.append(FieldRow(label="Оновлено дані", new=", ".join(self.changed_collections)))
        for c in self.collection_changes or []:
            rows.extend(c.field_rows())
        return rows


class EntrantDeleted(DeleteAction):
    table_name: ClassVar[str] = "entrants"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRANT_LABELS
    pib: str
    edbo: Optional[str] = None
