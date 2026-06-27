"""Пакет генерації DOCX-документів за шаблонами (DK-27).

Дворівнева конструкція:

* `engine.render_docx(template_name, context) -> BytesIO` — тонкий stateless
  рушій поверх `docxtpl` (шаблони, Jinja-фільтри, формат виводу).
* `base.BaseReport` — Pydantic-схема, що знає свій шаблон; валідує дані на
  конструкторі та віддає готовий документ через `.render()` / `.render_bytes()`.

Конкретні звіти додаються пізніше у `reports/<entity>.py` (нащадки `BaseReport`)
і реєструються у `REPORTS` нижче — реєстр потрібен лише там, де тип звіту
приходить рядком з UI (випадаючий список); типобезпека живе у самих класах.

Приклад майбутнього використання:

    from Dekanat.reports import get_report_class
    report_cls = get_report_class("admission_campaign")
    buffer = report_cls(**data).render()        # BytesIO → rx.download(...)
"""

from typing import Dict, Type

from Dekanat.reports.base import BaseReport
from Dekanat.reports.engine import render_docx, TEMPLATES_DIR
from Dekanat.reports.rating import RatingReport, RatingApplicant

# Реєстр «ключ з UI → клас звіту».
REPORTS: Dict[str, Type[BaseReport]] = {
    "rating": RatingReport,
}


def get_report_class(key: str) -> Type[BaseReport]:
    """Повернути клас звіту за ключем реєстру. Кидає `KeyError` з переліком
    доступних ключів, якщо ключа немає (fail-fast для опечаток у UI-диспетчері)."""
    try:
        return REPORTS[key]
    except KeyError:
        available = ", ".join(sorted(REPORTS)) or "—"
        raise KeyError(f"Невідомий тип звіту: {key!r}. Доступні: {available}")


__all__ = [
    "BaseReport",
    "render_docx",
    "TEMPLATES_DIR",
    "REPORTS",
    "get_report_class",
    "RatingReport",
    "RatingApplicant",
]
