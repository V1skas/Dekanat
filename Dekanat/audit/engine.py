"""Рушій запису дій у журнал (DK-55).

Тонкий шар без бізнес-логіки: додає `AuditLogModel` **у ту саму сесію**, що й
зміна даних (commit робить сервіс). Це і є гарантія «логуємо лише те, що реально
застосувалось у БД»: якщо транзакція відкотиться — запис журналу теж не збережеться.
"""

from typing import Optional

from sqlmodel import Session

from Dekanat.models import AuditLogModel
from Dekanat.audit.base import BaseAuditAction, UpdateAction


def record_action(
    session: Session,
    actor_id: Optional[int],
    record_id,
    action: BaseAuditAction,
) -> None:
    """Записати дію в журнал (без commit).

    Для `UpdateAction` без реальних змін — no-op (порожній diff не логуємо).
    """
    if isinstance(action, UpdateAction) and not action.has_changes():
        return

    entry = AuditLogModel(
        id_worker=actor_id,
        action=action.action,
        table_name=action.table_name,
        record_id=str(record_id),
        changes=action.to_json(),
    )
    session.add(entry)
