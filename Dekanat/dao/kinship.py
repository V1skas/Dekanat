from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import KinshipModel


class KinshipDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[KinshipModel]:
        statement = select(KinshipModel).where(KinshipModel.is_deleted == False)
        if with_del:
            statement = statement.where(KinshipModel.is_deleted == True)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[KinshipModel]:
        statement = select(KinshipModel).where(KinshipModel.id == id).where(KinshipModel.is_deleted == False)
        if with_del:
            statement = statement.where(KinshipModel.is_deleted == True)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: KinshipModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: KinshipModel, session: Session):
        item = session.merge(item)
        session.add(item)
