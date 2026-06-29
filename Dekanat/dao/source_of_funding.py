from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import SourceOfFundingModel


class SourceOfFundingDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[SourceOfFundingModel]:
        statement = select(SourceOfFundingModel)
        if not with_del:
            statement = statement.where(SourceOfFundingModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[SourceOfFundingModel]:
        statement = select(SourceOfFundingModel).where(SourceOfFundingModel.id == id)
        if not with_del:
            statement = statement.where(SourceOfFundingModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: SourceOfFundingModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: SourceOfFundingModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged
