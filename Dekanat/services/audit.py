import reflex as rx

from typing import Sequence

from Dekanat.dao.audit import AuditDao
from Dekanat.models import AuditLogModel


class AuditService:
    """Читання журналу дій (DK-55). Запис веде `Dekanat.audit.record_action`
    усередині транзакції зміни — окремого write-методу тут немає навмисно."""

    def get_history(self, table_name: str, record_id: str) -> Sequence[AuditLogModel]:
        try:
            with rx.session() as session:
                return AuditDao.get_history(session, table_name, str(record_id))
        except Exception as e:
            print(f"[AuditService][get_history][ERROR] {e}")
            raise
