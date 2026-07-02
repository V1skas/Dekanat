"""Виконання блокуючих задач поза event loop (DK-41).

Формування документів (DOCX/XLSX) — важка CPU/IO-операція (`docxtpl`/`lxml`,
`openpyxl`). Reflex виконує тіло sync event-обробника прямо в єдиному потоці
asyncio: доки документ формується, застосунок «зависає» для **всіх**
користувачів — не обробляються ні події інших вкладок, ні запити інших клієнтів.

`run_blocking` виносить таку роботу у виділений пул потоків: event loop лишається
вільним обслуговувати запити інших користувачів, поки документ формується у фоні.
Обробник у стані має бути `async def`, а важку частину викликати через
`await run_blocking(self._render_something, ...)`.

Пул навмисно невеликий: важкий рендер під GIL все одно майже не паралелиться по
CPU, а обмеження кількості воркерів стримує споживання пам'яті, коли кілька
користувачів формують документи одночасно.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

_T = TypeVar("_T")

# Виділений пул для формування звітів/документів.
_REPORT_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="report")


async def run_blocking(fn: Callable[..., _T], *args) -> _T:
    """Виконати блокуючу `fn(*args)` у фоновому потоці, не блокуючи event loop.

    Повертає результат `fn`; винятки пробрасуються виклику як є. Функція `fn`
    працює в окремому потоці — вона **не повинна** мутувати стан Reflex і не
    повинна `yield`-ити події; хай лише рахує та повертає готові дані.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_REPORT_EXECUTOR, fn, *args)
