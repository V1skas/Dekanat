from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import SpecialConditionModel


class SpecialConditionDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[SpecialConditionModel]:
        statement = select(SpecialConditionModel)
        if not with_del:
            statement = statement.where(SpecialConditionModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_code(code: str, session: Session, with_del: bool = False) -> Optional[SpecialConditionModel]:
        statement = select(SpecialConditionModel).where(SpecialConditionModel.subcategory_code == code)
        if not with_del:
            statement = statement.where(SpecialConditionModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: SpecialConditionModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: SpecialConditionModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged
