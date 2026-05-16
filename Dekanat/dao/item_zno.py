from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import ItemZnoModel


class ItemZnoDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[ItemZnoModel]:
        statement = select(ItemZnoModel)
        if not with_del:
            statement = statement.where(ItemZnoModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[ItemZnoModel]:
        statement = select(ItemZnoModel).where(ItemZnoModel.id == id)
        if not with_del:
            statement = statement.where(ItemZnoModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: ItemZnoModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: ItemZnoModel, session: Session):
        item = session.merge(item)
        session.add(item)
