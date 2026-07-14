"""Тексти історії оновлень (changelog, DK-32).

Джерело правди — git: кожен реліз дописує сюди новий запис. Синхронізація в БД —
`AppUpdateService.sync_updates` (виклик з `update.py`, за зразком `sync_actions`).
`body` — markdown (рендериться `rx.markdown`), емодзі/списки/виділення доречні.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AppUpdate:
    version: str
    title: str
    body: str


UPDATES: List[AppUpdate] = [
]
