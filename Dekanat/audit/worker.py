"""Дії журналу для користувачів системи (workers, DK-55/DK-66).

Поля пароля/солі навмисно не логуються. Набір ролей — окреме поле `roles`
(`CollectionChange` — додані/вилучені назви ролей, DK-66), яке сервіс виставляє
вручну (з `from_diff` для скалярних полів воно не рахується).
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow, CollectionChange


_WORKER_LABELS: Dict[str, str] = {
    "pib": "ПІБ",
    "login": "Логін",
    "email": "Email",
    "phone_number": "Телефон",
    "roles": "Ролі",
}


class WorkerCreated(CreateAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    pib: str
    login: str
    email: Optional[str] = None
    phone_number: Optional[str] = None


class WorkerUpdated(UpdateAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("pib", "login", "email", "phone_number")
    pib: Optional[FieldChange] = None
    login: Optional[FieldChange] = None
    email: Optional[FieldChange] = None
    phone_number: Optional[FieldChange] = None
    # Набір ролей — виставляється сервісом вручну (added/removed назв ролей, DK-66).
    roles: Optional[CollectionChange] = None

    def has_changes(self) -> bool:
        return super().has_changes() or (self.roles is not None and self.roles.has_changes())

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.roles is not None and self.roles.has_changes():
            if self.roles.added:
                lines.append("Додано ролі: " + ", ".join(self.roles.added))
            if self.roles.removed:
                lines.append("Вилучено ролі: " + ", ".join(self.roles.removed))
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.roles is not None:
            rows.extend(self.roles.field_rows())
        return rows


class WorkerDeleted(DeleteAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    pib: str
    login: str
