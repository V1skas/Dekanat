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

from typing import Any, ClassVar, Dict, List, Self, Tuple

from pydantic import BaseModel, Field


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


class FieldRow(BaseModel):
    """Один рядок деталізованої історії для UI (DK-56).

    `label == ""` → звичайний нейтральний рядок (весь текст у `text`, напр.
    «Створено запис», «Сформовано рейтинговий список…»). Інакше — рядок поля:
    заповнені і `old`, і `new` → diff (старе закреслено → нове); лише `new` →
    значення «додано»; лише `old` → значення «видалено». Рендер-конвенція
    визначається наявністю значень, без окремого enum — див.
    `views/templates/audit.py:_field_row`.
    """

    label: str = ""
    text: str = ""
    old: str = ""
    new: str = ""


class CollectionChange(BaseModel):
    """Зміна дочірньої колекції (DK-66): що додано / вилучено / відредаговано,
    людиночитаними рядками (назви, а не id). Порожня — якщо колекція не
    змінилась (`has_changes()` це і перевіряє)."""

    label: str = ""
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    edited: List[FieldRow] = Field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.edited)

    def field_rows(self) -> list[FieldRow]:
        if not self.has_changes():
            return []
        rows = [FieldRow(text=f"{self.label}:")]
        rows.extend(FieldRow(new=v) for v in self.added)
        rows.extend(FieldRow(old=v) for v in self.removed)
        rows.extend(self.edited)
        return rows


def diff_collection(
    label: str,
    old_rows: list[Dict[str, Any]],
    new_rows: list[Dict[str, Any]],
) -> CollectionChange:
    """Diff двох списків уже підготовлених рядків: кожен `row` —
    `{"id_key": ..., "identity": str, "value": Optional[str]}`. Викликач резолвить
    id→назва і будує ці три поля ДО виклику (DK-66) — тут лише порівняння.

    `id_key` — ідентичність рядка (без значення, що диффиться); `identity` —
    людиночитаний підпис (для added/removed і як label edited-рядка); `value` —
    змінна частина для порівняння і показу old→new. `value is None` (в обох
    рядках з однаковим `id_key`) означає «немає з чим порівнювати» — рядок
    ніколи не потрапить у `edited`, лишиться add+remove при будь-якій зміні."""
    old_map = {r["id_key"]: r for r in old_rows}
    new_map = {r["id_key"]: r for r in new_rows}
    old_ids, new_ids = set(old_map), set(new_map)

    added = sorted(new_map[k]["identity"] for k in new_ids - old_ids)
    removed = sorted(old_map[k]["identity"] for k in old_ids - new_ids)
    edited: list[FieldRow] = []
    for k in old_ids & new_ids:
        old_r, new_r = old_map[k], new_map[k]
        old_v, new_v = old_r.get("value"), new_r.get("value")
        if old_v is not None and new_v is not None and old_v != new_v:
            edited.append(FieldRow(label=new_r["identity"], old=old_v, new=new_v))

    return CollectionChange(label=label, added=added, removed=removed, edited=edited)


def diff_string_list(label: str, old_names: list[str], new_names: list[str]) -> CollectionChange:
    """Diff двох списків рядків (уже людиночитаних назв, DK-66) — лише
    added/removed, без `edited` (немає складеного значення для порівняння).
    Для простих M2M-наборів: ролі воркера, права ролі, відповідальні на іспиті."""
    old_set, new_set = set(old_names), set(new_names)
    return CollectionChange(
        label=label,
        added=sorted(new_set - old_set),
        removed=sorted(old_set - new_set),
    )


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

    def field_rows(self) -> list[FieldRow]:
        """Структурована деталізація для UI (DK-56). Дефолт перетворює
        `describe()` на нейтральні рядки-примітки — покриває дії без
        пар полів (напр. `RatingGenerated`, `GenericAudit`)."""
        return [FieldRow(text=line) for line in self.describe()]

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

    def field_rows(self) -> list[FieldRow]:
        rows = [FieldRow(text="Створено запис")]
        for name in type(self).model_fields:
            rows.append(FieldRow(label=self._label(name), new=format_value(getattr(self, name))))
        return rows


class DeleteAction(BaseAuditAction):
    action: ClassVar[str] = "delete"

    def describe(self) -> list[str]:
        return ["Видалено запис", *self._snapshot_lines()]

    def field_rows(self) -> list[FieldRow]:
        rows = [FieldRow(text="Видалено запис")]
        for name in type(self).model_fields:
            rows.append(FieldRow(label=self._label(name), old=format_value(getattr(self, name))))
        return rows


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

    def field_rows(self) -> list[FieldRow]:
        rows: list[FieldRow] = []
        for name in self._changed_fields():
            fc: FieldChange = getattr(self, name)
            rows.append(FieldRow(label=self._label(name), old=format_value(fc.old), new=format_value(fc.new)))
        return rows
