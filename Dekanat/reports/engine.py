"""Тонкий рушій рендерингу DOCX за шаблоном (DK-27).

Знає тільки про `docxtpl`, директорію шаблонів, формат виводу та спільні
Jinja-фільтри (гроші, дати). НЕ знає нічого про конкретні звіти — stateless.
Бізнес-логіку та схему даних тримають класи-звіти у `reports/base.py` і далі.

Шар навмисно не залежить від Reflex: повертаємо `BytesIO`, а вже state-шар
загортає байти у `rx.download(...)`.
"""

from io import BytesIO
from pathlib import Path
from datetime import date, datetime
from typing import Any

from docxtpl import DocxTemplate
from jinja2 import Environment, StrictUndefined

# Усі шаблони лежать поряд, у `reports/templates/*.docx`.
TEMPLATES_DIR = Path(__file__).parent / "templates"


# Нерозривний пробіл як розділювач тисяч — щоб "1 234 567" не переносилось
# на різні рядки всередині документа.
_NBSP = "\u00a0"


def _fmt_money(value: Any) -> str:
    """1234567.5 → "1 234 567,50" (нерозривні пробіли, кома як десятковий
    розділювач). Порожнє/None → "" (хай шаблон сам вирішує)."""
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):,.2f}".replace(",", _NBSP).replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def _coerce_date(value: Any) -> date | None:
    """Приймає date/datetime/ISO-рядок ("2026-06-27" чи "2026-06-27T..."),
    повертає date або None, якщо розпарсити не вдалося."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _fmt_date(value: Any, fmt: str = "%d.%m.%Y") -> str:
    """date/datetime/ISO-рядок → "27.06.2026". Невідоме → вихідне значення як є."""
    d = _coerce_date(value)
    if d is not None:
        return d.strftime(fmt)
    return "" if value is None else str(value)


def _fmt_datetime(value: Any, fmt: str = "%d.%m.%Y %H:%M") -> str:
    """datetime/ISO-рядок → "27.06.2026 14:30"."""
    if isinstance(value, datetime):
        return value.strftime(fmt)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).strftime(fmt)
        except ValueError:
            return _fmt_date(value, "%d.%m.%Y")
    return "" if value is None else str(value)


def _jinja_env() -> Environment:
    """Jinja-середовище для шаблонів.

    `StrictUndefined` — fail-fast: якщо шаблон посилається на змінну, якої немає
    у context, рендер впаде з помилкою замість мовчазної підстановки порожнечі
    (для офіційних документів тиха порожнеча небезпечна).
    """
    env = Environment(undefined=StrictUndefined)
    env.filters["money"] = _fmt_money
    env.filters["date"] = _fmt_date
    env.filters["datetime"] = _fmt_datetime
    return env


def render_docx(template_name: str, context: dict) -> BytesIO:
    """Відрендерити шаблон `template_name` з `context` → `BytesIO` (.docx).

    Кидає `FileNotFoundError`, якщо шаблону немає, і пробрасує помилки Jinja
    (зокрема `UndefinedError` від `StrictUndefined`) — fail-fast.
    """
    path = TEMPLATES_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Шаблон не знайдено: {template_name}")
    try:
        doc = DocxTemplate(path)
        doc.render(context, jinja_env=_jinja_env())
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"[reports.engine][render_docx][ERROR] {template_name}: {e}")
        raise
