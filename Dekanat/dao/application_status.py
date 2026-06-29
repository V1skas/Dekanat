from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import ApplicationStatusModel


class ApplicationStatusDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[ApplicationStatusModel]:
        statement = select(ApplicationStatusModel)
        if not with_del:
            statement = statement.where(ApplicationStatusModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[ApplicationStatusModel]:
        statement = select(ApplicationStatusModel).where(ApplicationStatusModel.id == id)
        if not with_del:
            statement = statement.where(ApplicationStatusModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def get_default(session: Session) -> Optional[ApplicationStatusModel]:
        """Статус, позначений як дефолтний для нових карток абітурієнтів (DK-36)."""
        statement = (
            select(ApplicationStatusModel)
            .where(ApplicationStatusModel.is_deleted == False)
            .where(ApplicationStatusModel.is_default == True)
        )
        return session.exec(statement).first()

    @staticmethod
    def clear_default_except(except_id: Optional[int], session: Session) -> None:
        """Знімає прапорець is_default з усіх статусів, окрім вказаного. Підтримує
        інваріант «дефолтним може бути лише один статус» (DK-36)."""
        statement = select(ApplicationStatusModel).where(ApplicationStatusModel.is_default == True)
        for row in session.exec(statement).all():
            if except_id is not None and row.id == except_id:
                continue
            row.is_default = False
            session.add(row)

    @staticmethod
    def add_one(item: ApplicationStatusModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: ApplicationStatusModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged
