from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import DepartmentModel


class DepartmentDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[DepartmentModel]:
        statement = select(DepartmentModel)
        if not with_del:
            statement = statement.where(DepartmentModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[DepartmentModel]:
        statement = select(DepartmentModel).where(DepartmentModel.id == id)
        if not with_del:
            statement = statement.where(DepartmentModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: DepartmentModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: DepartmentModel, session: Session):
        item = session.merge(item)
        session.add(item)
