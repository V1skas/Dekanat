"""Базові класи журналу дій (DK-55).

За аналогією з `Dekanat/reports/` (BaseReport + Pydantic-схеми + рушій), кожна
дія над записом — це Pydantic-модель, що декларативно знає свою `action` та
`table_name`, вміє серіалізуватись у JSON (`to_json`) для колонки `changes` і
описувати себе людині (`describe`).

Три форми дії:

* `CreateAction` — знімок ключових полів створеного запису;
* `UpdateAction` — лише реально змінені поля як `FieldChange(old, new)`
  (порівняння старого й нового значення до збереження);
* `DeleteAction` — знімок ключових полів запису на момент видалення.

Конкретні дії живуть у `audit/<entity>.py` і реєструються в `audit/registry.py`.
"""

from typing import Any, ClassVar, Dict, Self, Tuple

from pydantic import BaseModel


def format_value(value: Any) -> str:
    """Значення поля у людиночитаному вигляді для `describe()`."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "так" if value else "ні"
    if isinstance(value, (list, tuple)):
        return ", ".join(format_value(v) for v in value) if value else "—"
    return str(value)


class FieldChange(BaseModel):
    """Зміна одного поля. `old`/`new` — обовʼязкові (без дефолтів), щоб
    `model_dump_json(exclude_defaults=True)` у `UpdateAction` не викидав
    вкладене значення, коли воно дорівнює `None` (напр. очищення email)."""

    old: Any
    new: Any


class BaseAuditAction(BaseModel):
    """Базовий клас дії. `action`/`table_name` — ClassVar (не поля моделі), тому
    не серіалізуються у `changes` і не конфліктують із полями-даними."""

    action: ClassVar[str] = ""
    table_name: ClassVar[str] = ""
    # Мапа «імʼя поля → укр. підпис» для describe().
    FIELD_LABELS: ClassVar[Dict[str, str]] = {}

    def to_json(self) -> str:
        return self.model_dump_json()

    def describe(self) -> list[str]:
        return []

    def _label(self, name: str) -> str:
        return self.FIELD_LABELS.get(name, name)

    def _snapshot_lines(self) -> list[str]:
        lines: list[str] = []
        for name in type(self).model_fields:
            lines.append(f"{self._label(name)}: {format_value(getattr(self, name))}")
        return lines


class CreateAction(BaseAuditAction):
    action: ClassVar[str] = "create"

    def describe(self) -> list[str]:
        return ["Створено запис", *self._snapshot_lines()]


class DeleteAction(BaseAuditAction):
    action: ClassVar[str] = "delete"

    def describe(self) -> list[str]:
        return ["Видалено запис", *self._snapshot_lines()]


class UpdateAction(BaseAuditAction):
    """Поля-зміни оголошуються як `Optional[FieldChange] = None`. `TRACKED`
    перелічує скалярні поля, які автоматично дифаються `from_diff`; додаткові
    поля (напр. набір ролей) сервіс може виставити вручну."""

    action: ClassVar[str] = "update"
    TRACKED: ClassVar[Tuple[str, ...]] = ()

    @classmethod
    def from_diff(cls, old: Any, new: Any) -> Self:
        changed: Dict[str, FieldChange] = {}
        for name in cls.TRACKED:
            old_val = getattr(old, name, None)
            new_val = getattr(new, name, None)
            if old_val != new_val:
                changed[name] = FieldChange(old=old_val, new=new_val)
        return cls(**changed)

    def _changed_fields(self) -> list[str]:
        return [f for f in type(self).model_fields if isinstance(getattr(self, f), FieldChange)]

    def has_changes(self) -> bool:
        return bool(self._changed_fields())

    def to_json(self) -> str:
        # exclude_defaults відкидає невиставлені Optional[FieldChange] (== None),
        # лишаючи виставлені разом із вкладеними old/new (навіть коли ті None).
        return self.model_dump_json(exclude_defaults=True)

    def describe(self) -> list[str]:
        lines: list[str] = []
        for name in self._changed_fields():
            fc: FieldChange = getattr(self, name)
            lines.append(f"{self._label(name)}: {format_value(fc.old)} → {format_value(fc.new)}")
        return lines
