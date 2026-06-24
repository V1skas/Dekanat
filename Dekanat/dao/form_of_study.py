from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import FormOfStudyModel


class FormOfStudyDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[FormOfStudyModel]:
        statement = select(FormOfStudyModel)
        if not with_del:
            statement = statement.where(FormOfStudyModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[FormOfStudyModel]:
        statement = select(FormOfStudyModel).where(FormOfStudyModel.id == id)
        if not with_del:
            statement = statement.where(FormOfStudyModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: FormOfStudyModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: FormOfStudyModel, session: Session) -> FormOfStudyModel:
        # merge повертає НОВИЙ persistent-екземпляр; саме його треба використовувати
        # далі (commit/refresh), бо переданий `item` лишається detached.
        merged = session.merge(item)
        session.add(merged)
        return merged
