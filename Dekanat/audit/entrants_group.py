"""Дії журналу для екзаменаційних груп (entrants_groups, DK-55).

Крім CRUD — зміна складу групи `GroupMembersChanged` (action="assign"): нею
логуються призначення абітурієнта з його картки, автопідбір, дозаповнення при
автоформуванні та ручні правки складу на сторінці редагування групи. record_id
у всіх — id групи.
"""

from typing import ClassVar, Dict, List, Optional, Tuple

from pydantic import Field

from Dekanat.audit.base import (
    BaseAuditAction,
    CreateAction,
    UpdateAction,
    DeleteAction,
    FieldChange,
    format_value,
)


_GROUP_LABELS: Dict[str, str] = {"title": "Назва"}


class GroupCreated(CreateAction):
    table_name: ClassVar[str] = "entrants_groups"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _GROUP_LABELS
    title: str


class GroupUpdated(UpdateAction):
    table_name: ClassVar[str] = "entrants_groups"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _GROUP_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title",)
    title: Optional[FieldChange] = None


class GroupDeleted(DeleteAction):
    table_name: ClassVar[str] = "entrants_groups"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _GROUP_LABELS
    title: str


class GroupMembersChanged(BaseAuditAction):
    """Зміна складу групи: списки доданих/вилучених абітурієнтів (ПІБ)."""

    action: ClassVar[str] = "assign"
    table_name: ClassVar[str] = "entrants_groups"
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def describe(self) -> list[str]:
        lines: list[str] = []
        if self.added:
            lines.append("Додано абітурієнтів: " + format_value(self.added))
        if self.removed:
            lines.append("Вилучено абітурієнтів: " + format_value(self.removed))
        return lines
