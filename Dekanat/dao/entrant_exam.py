from typing import Sequence, Optional, List, Tuple
from sqlmodel import Session, select, delete
from sqlalchemy.orm import selectinload

from Dekanat.models import (
    EntrantExamModel,
    EntrantExamWorkerModel,
)


class EntrantExamDao:
    @staticmethod
    def _base_select():
        return (
            select(EntrantExamModel)
            .options(
                selectinload(EntrantExamModel.group),
                selectinload(EntrantExamModel.item_zno),
                selectinload(EntrantExamModel.responsible_workers),
            )
        )

    @staticmethod
    def get_all(
        session: Session,
        with_del: bool = False,
        id_group: Optional[int] = None,
        id_item_zno: Optional[int] = None,
        id_worker: Optional[int] = None,
        date_between: Optional[Tuple[str, str]] = None,
    ) -> Sequence[EntrantExamModel]:
        statement = EntrantExamDao._base_select()
        if not with_del:
            statement = statement.where(EntrantExamModel.is_deleted == False)
        if id_group is not None and id_group > 0:
            statement = statement.where(EntrantExamModel.id_group == id_group)
        if id_item_zno is not None and id_item_zno > 0:
            statement = statement.where(EntrantExamModel.id_item_zno == id_item_zno)
        if id_worker is not None and id_worker > 0:
            # filter exams that have a link to this worker
            statement = statement.where(
                EntrantExamModel.id.in_(
                    select(EntrantExamWorkerModel.id_exam).where(
                        EntrantExamWorkerModel.id_worker == id_worker
                    )
                )
            )
        if date_between is not None:
            start_date, end_date = date_between
            statement = (
                statement
                .where(EntrantExamModel.date >= start_date)
                .where(EntrantExamModel.date <= end_date)
            )
        statement = statement.order_by(
            EntrantExamModel.date, EntrantExamModel.time_start
        )
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[EntrantExamModel]:
        statement = EntrantExamDao._base_select().where(EntrantExamModel.id == id)
        if not with_del:
            statement = statement.where(EntrantExamModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def get_by_group(group_id: int, session: Session, with_del: bool = False) -> Sequence[EntrantExamModel]:
        statement = (
            EntrantExamDao._base_select()
            .where(EntrantExamModel.id_group == group_id)
            .order_by(EntrantExamModel.date, EntrantExamModel.time_start)
        )
        if not with_del:
            statement = statement.where(EntrantExamModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def add_one(item: EntrantExamModel, session: Session) -> EntrantExamModel:
        session.add(item)
        return item

    @staticmethod
    def edit_one(item: EntrantExamModel, session: Session) -> EntrantExamModel:
        merged = session.merge(item)
        session.add(merged)
        return merged

    @staticmethod
    def replace_workers(exam_id: int, worker_ids: List[int], session: Session) -> None:
        """Повна заміна списку відповідальних співробітників іспиту."""
        session.exec(  # type: ignore[arg-type]
            delete(EntrantExamWorkerModel).where(EntrantExamWorkerModel.id_exam == exam_id)
        )
        session.flush()
        for wid in worker_ids:
            session.add(EntrantExamWorkerModel(id_exam=exam_id, id_worker=wid))
