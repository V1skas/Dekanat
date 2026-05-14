from typing import Sequence, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import SpecialityModel


class SpecialityDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[SpecialityModel]:
        statement = select(SpecialityModel).options(selectinload(SpecialityModel.department))
        if not with_del:
            statement = statement.where(SpecialityModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_pk(code: str, id_department: int, session: Session, with_del: bool = False) -> Optional[SpecialityModel]:
        statement = (
            select(SpecialityModel)
            .options(selectinload(SpecialityModel.department))
            .where(SpecialityModel.code == code)
            .where(SpecialityModel.id_department == id_department)
        )
        if not with_del:
            statement = statement.where(SpecialityModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: SpecialityModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: SpecialityModel, session: Session):
        item = session.merge(item)
        session.add(item)
