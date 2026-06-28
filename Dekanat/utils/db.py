"""Утиліти для роботи з БД, незалежні від конкретних сутностей.

`UA_CI` — кастомний SQLite collation для українського алфавіту:
у Unicode літера `І` (U+0406) йде раніше за `А` (U+0410), тож стандартне
BINARY-сортування ставить «Іванова» перед «Андрієнко». До того ж `lower()`
у SQLite за замовчуванням не знає кирилицю. Реєструємо власну функцію
порівняння: спершу `lower()`, потім зважування за позицією в українському
алфавіті — кожен символ за межами алфавіту іде в кінець у звичайному
лексикографічному порядку.
"""
from typing import Optional

from sqlalchemy import event
from reflex.model import get_engine


UA_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
_UA_ORDER = {ch: idx for idx, ch in enumerate(UA_ALPHABET, start=1)}
# Великі літери — за такою ж вагою (порівняння без регістру).
for ch, idx in list(_UA_ORDER.items()):
    _UA_ORDER[ch.upper()] = idx

_NON_UA_OFFSET = 10_000  # символи не з українського алфавіту — після нього


def _char_weight(c: str) -> int:
    w = _UA_ORDER.get(c)
    if w is not None:
        return w
    return _NON_UA_OFFSET + ord(c)


def _ua_compare(a: Optional[str], b: Optional[str]) -> int:
    a = a or ""
    b = b or ""
    for i in range(max(len(a), len(b))):
        if i >= len(a):
            return -1
        if i >= len(b):
            return 1
        wa = _char_weight(a[i])
        wb = _char_weight(b[i])
        if wa != wb:
            return -1 if wa < wb else 1
    return 0


_registered = False


def register_ua_collation() -> None:
    """Підписує listener на SQLAlchemy engine, який реєструє collation `UA_CI`
    при кожному новому DBAPI-зʼєднанні. Викликати треба один раз при старті
    застосунку — до першого використання rx.session().

    Кастомний collation через `create_collation` — це API лише SQLite. Для
    інших СУБД (MySQL у проді) listener не реєструється, а сортування кирилиці
    забезпечує нативний collation (див. `ua_collate`).
    """
    global _registered
    if _registered:
        return
    engine = get_engine()
    if engine.dialect.name != "sqlite":
        # Нема чого реєструвати — не SQLite. Позначаємо як виконане (ідемпотентно).
        _registered = True
        return

    @event.listens_for(engine, "connect")
    def _setup_collation(dbapi_connection, connection_record):  # noqa: ARG001
        dbapi_connection.create_collation("UA_CI", _ua_compare)

    _registered = True


# Назва collation для сортування кирилиці, залежно від СУБД. Резолвиться лениво
# (один раз), бо движок може ще не існувати на момент імпорту модуля.
_UA_COLLATION_NAME: Optional[str] = None


def _resolve_collation_name() -> str:
    global _UA_COLLATION_NAME
    if _UA_COLLATION_NAME is None:
        try:
            dialect = get_engine().dialect.name
        except Exception:
            dialect = ""
        if dialect == "sqlite":
            _UA_COLLATION_NAME = "UA_CI"               # кастомний, реєструється на connect
        elif dialect == "mysql":
            _UA_COLLATION_NAME = "utf8mb4_unicode_ci"  # нативний Unicode-collation MySQL
        else:
            _UA_COLLATION_NAME = ""                    # без collation — сортування «як є»
    return _UA_COLLATION_NAME


def ua_collate(col):
    """Обгортає текстову колонку потрібним для поточної СУБД collation для
    коректного сортування кирилиці. Для невідомих діалектів повертає колонку
    без collation. Використовувати у DAO замість прямого `col.collate("UA_CI")`.
    """
    name = _resolve_collation_name()
    return col.collate(name) if name else col
