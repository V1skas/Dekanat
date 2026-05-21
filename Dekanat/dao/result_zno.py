from typing import Sequence, Optional, List
from sqlmodel import Session, select

from Dekanat.models import ResultZnoModel


class ResultZnoDao:
    @staticmethod
    def get_by_subject_and_persons(
        id_items_zno: int, person_ids: List[int], session: Session
    ) -> Sequence[ResultZnoModel]:
        if not person_ids:
            return []
        statement = (
            select(ResultZnoModel)
            .where(ResultZnoModel.id_items_zno == id_items_zno)
            .where(ResultZnoModel.id_person.in_(person_ids))  # type: ignore[attr-defined]
        )
        return session.exec(statement).all()

    @staticmethod
    def get_one(
        id_items_zno: int, id_person: int, session: Session
    ) -> Optional[ResultZnoModel]:
        statement = (
            select(ResultZnoModel)
            .where(ResultZnoModel.id_items_zno == id_items_zno)
            .where(ResultZnoModel.id_person == id_person)
        )
        return session.exec(statement).one_or_none()

    @staticmethod
    def upsert(
        id_items_zno: int, id_person: int, points: int, session: Session
    ) -> ResultZnoModel:
        existing = ResultZnoDao.get_one(id_items_zno, id_person, session)
        if existing is not None:
            existing.points = points
            session.add(existing)
            return existing
        new_item = ResultZnoModel(
            id_items_zno=id_items_zno, id_person=id_person, points=points
        )
        session.add(new_item)
        return new_item

    @staticmethod
    def delete_one(id_items_zno: int, id_person: int, session: Session) -> None:
        existing = ResultZnoDao.get_one(id_items_zno, id_person, session)
        if existing is not None:
            session.delete(existing)
