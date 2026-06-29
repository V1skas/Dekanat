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
    def add_one(item: ApplicationStatusModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: ApplicationStatusModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged
