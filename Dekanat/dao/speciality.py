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
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[SpecialityModel]:
        statement = (
            select(SpecialityModel)
            .options(selectinload(SpecialityModel.department))
            .where(SpecialityModel.id == id)
        )
        if not with_del:
            statement = statement.where(SpecialityModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def get_duplicate(code: str, id_department: int, tag: str, session: Session, exclude_id: Optional[int] = None) -> Optional[SpecialityModel]:
        """Не видалена спеціальність з тим самим (code, id_department, tag) — для перевірки
        унікальності в сервісі (DK-38). exclude_id — щоб не ловити саму себе при edit."""
        statement = (
            select(SpecialityModel)
            .where(SpecialityModel.code == code)
            .where(SpecialityModel.id_department == id_department)
            .where(SpecialityModel.tag == tag)
            .where(SpecialityModel.is_deleted == False)
        )
        if exclude_id is not None:
            statement = statement.where(SpecialityModel.id != exclude_id)
        return session.exec(statement).first()

    @staticmethod
    def add_one(item: SpecialityModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: SpecialityModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged
