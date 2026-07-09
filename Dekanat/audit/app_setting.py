"""Дії журналу для налаштувань системи (app_settings, DK-55).

record_id — ключ налаштування (str PK). Логуємо лише зміну значення.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import UpdateAction, FieldChange


class AppSettingUpdated(UpdateAction):
    table_name: ClassVar[str] = "app_settings"
    FIELD_LABELS: ClassVar[Dict[str, str]] = {"value": "Значення"}
    TRACKED: ClassVar[Tuple[str, ...]] = ("value",)
    value: Optional[FieldChange] = None
