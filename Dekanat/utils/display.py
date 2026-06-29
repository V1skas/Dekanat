"""Утиліти відображення, незалежні від конкретних сутностей.

`disambiguate_pib` розрізняє абітурієнтів з однаковим ПІБ (повні тезки) у
рейтингах, групах та при виставленні оцінок: до ПІБ, що зустрічається в наборі
більше одного разу, додається номер телефону в дужках (DK-36).
"""
from collections import Counter
from typing import Iterable, List, Tuple


def disambiguate_pib(entries: Iterable[Tuple[str, str]]) -> List[str]:
    """`entries` — послідовність пар (pib, phone). Повертає список рядків для
    відображення у тому ж порядку: для ПІБ-тезок додає « (телефон)», інакше —
    лишає ПІБ як є. Якщо телефон порожній, дужки не додаються навіть для тезок.
    """
    items = list(entries)
    counts = Counter(pib for pib, _ in items)
    result: List[str] = []
    for pib, phone in items:
        if counts[pib] > 1 and phone:
            result.append(f"{pib} ({phone})")
        else:
            result.append(pib)
    return result
