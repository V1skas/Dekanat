"""Дії журналу для ролей RBAC (roles, DK-55/DK-66).

Набір прав ролі — окреме поле `actions` (`CollectionChange` — додані/вилучені
назви прав, DK-66), яке сервіс виставляє вручну; скалярні title/description
дифаються `from_diff`.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow, CollectionChange


_ROLE_LABELS: Dict[str, str] = {
    "title": "Назва",
    "description": "Опис",
    "actions": "Права",
}


class RoleCreated(CreateAction):
    table_name: ClassVar[str] = "roles"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ROLE_LABELS
    title: str
    description: Optional[str] = None


class RoleUpdated(UpdateAction):
    table_name: ClassVar[str] = "roles"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ROLE_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "description")
    title: Optional[FieldChange] = None
    description: Optional[FieldChange] = None
    actions: Optional[CollectionChange] = None

    def has_changes(self) -> bool:
        return super().has_changes() or (self.actions is not None and self.actions.has_changes())

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.actions is not None and self.actions.has_changes():
            if self.actions.added:
                lines.append("Додано права: " + ", ".join(self.actions.added))
            if self.actions.removed:
                lines.append("Вилучено права: " + ", ".join(self.actions.removed))
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.actions is not None:
            rows.extend(self.actions.field_rows())
        return rows


class RoleDeleted(DeleteAction):
    table_name: ClassVar[str] = "roles"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ROLE_LABELS
    title: str
