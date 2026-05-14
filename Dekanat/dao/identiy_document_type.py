from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import IdentityDocumentTypeModel


class IdentityDocumentTypeDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[IdentityDocumentTypeModel]:
        statement = select(IdentityDocumentTypeModel)
        if not with_del:
            statement = statement.where(IdentityDocumentTypeModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[IdentityDocumentTypeModel]:
        statement = select(IdentityDocumentTypeModel).where(IdentityDocumentTypeModel.id == id)
        if not with_del:
            statement = statement.where(IdentityDocumentTypeModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: IdentityDocumentTypeModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: IdentityDocumentTypeModel, session: Session):
        item = session.merge(item)
        session.add(item)
