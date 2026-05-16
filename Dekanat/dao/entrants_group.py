from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import EntrantGroupModel


class EntrantsGroupDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[EntrantGroupModel]:
        statement = select(EntrantGroupModel)
        if not with_del:
            statement = statement.where(EntrantGroupModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[EntrantGroupModel]:
        statement = select(EntrantGroupModel).where(EntrantGroupModel.id == id)
        if not with_del:
            statement = statement.where(EntrantGroupModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: EntrantGroupModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: EntrantGroupModel, session: Session):
        item = session.merge(item)
        session.add(item)
