"""Дії журналу для ролей RBAC (roles, DK-55).

Набір прав ролі — окреме поле `actions` (список кодів дій до/після), яке сервіс
виставляє вручну; скалярні title/description дифаються `from_diff`.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange


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
    actions: Optional[FieldChange] = None


class RoleDeleted(DeleteAction):
    table_name: ClassVar[str] = "roles"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ROLE_LABELS
    title: str
