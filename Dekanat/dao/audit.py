from typing import Sequence
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import AuditLogModel


class AuditDao:
    @staticmethod
    def get_history(
        session: Session,
        table_name: str,
        record_id: str,
        limit: int = 200,
    ) -> Sequence[AuditLogModel]:
        """Історія записів по конкретному запису — новіші зверху (DK-55).

        Актор підвантажується одразу (`selectinload`), щоб UI не робив N+1.
        """
        statement = (
            select(AuditLogModel)
            .where(AuditLogModel.table_name == table_name)
            .where(AuditLogModel.record_id == record_id)
            .options(selectinload(AuditLogModel.worker))
            .order_by(AuditLogModel.created_at.desc(), AuditLogModel.id.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return session.exec(statement).all()
