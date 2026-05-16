from typing import Sequence, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import (
    EntrantGroupModel,
    EntrantModel,
    EntrantExamModel,
)


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
    def add_one(item: EntrantGroupModel, session: Session) -> EntrantGroupModel:
        session.add(item)
        return item

    @staticmethod
    def edit_one(item: EntrantGroupModel, session: Session) -> EntrantGroupModel:
        # `session.merge` returns a new managed instance; the input stays detached.
        # Return the managed one so callers can refresh/commit on the right object.
        merged = session.merge(item)
        session.add(merged)
        return merged

    # --- related data ---

    @staticmethod
    def get_entrants_by_group(group_id: int, session: Session) -> Sequence[EntrantModel]:
        statement = (
            select(EntrantModel)
            .options(selectinload(EntrantModel.person))
            .where(EntrantModel.id_entrant_group == group_id)
            .where(EntrantModel.is_deleted == False)
        )
        return session.exec(statement).all()

    @staticmethod
    def get_assignable_entrants(group_id: Optional[int], session: Session) -> Sequence[EntrantModel]:
        """Абітурієнти, яких можна додати до групи:
        - не прив'язані до жодної групи (id_entrant_group IS NULL), або
        - прив'язані до групи, яка soft-deleted (is_deleted=True), або
        - (для існуючої групи) вже додані до неї.
        LEFT JOIN потрібен щоб мати доступ до is_deleted чужої групи.
        """
        statement = (
            select(EntrantModel)
            .outerjoin(EntrantGroupModel, EntrantModel.id_entrant_group == EntrantGroupModel.id)
            .options(selectinload(EntrantModel.person))
            .where(EntrantModel.is_deleted == False)
        )
        free_condition = (
            (EntrantModel.id_entrant_group == None)  # noqa: E711
            | (EntrantGroupModel.is_deleted == True)
        )
        if group_id is None or group_id <= 0:
            statement = statement.where(free_condition)
        else:
            statement = statement.where(free_condition | (EntrantModel.id_entrant_group == group_id))
        return session.exec(statement).all()

    @staticmethod
    def replace_entrants(group_id: int, entrant_ids: list[int], session: Session) -> None:
        """Замінює склад групи: усім поточним членам ставить id_entrant_group=None,
        потім переданим — id_entrant_group=group_id."""
        current = session.exec(
            select(EntrantModel).where(EntrantModel.id_entrant_group == group_id)
        ).all()
        for e in current:
            e.id_entrant_group = None  # type: ignore[assignment]
            session.add(e)
        session.flush()
        if entrant_ids:
            to_add = session.exec(
                select(EntrantModel).where(EntrantModel.id.in_(entrant_ids))
            ).all()
            for e in to_add:
                e.id_entrant_group = group_id
                session.add(e)

    @staticmethod
    def get_exams_by_group(group_id: int, session: Session) -> Sequence[EntrantExamModel]:
        statement = (
            select(EntrantExamModel)
            .options(selectinload(EntrantExamModel.item_zno))
            .where(EntrantExamModel.id_group == group_id)
            .order_by(EntrantExamModel.date_time)
        )
        return session.exec(statement).all()
