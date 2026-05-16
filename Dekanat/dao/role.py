from typing import Sequence, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import RoleModel, RolesActionsModel, WorkersRolesModel


class RoleDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[RoleModel]:
        statement = select(RoleModel)
        if not with_del:
            statement = statement.where(RoleModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False, with_relationship: bool = False) -> Optional[RoleModel]:
        statement = select(RoleModel).where(RoleModel.id == id)
        if not with_del:
            statement = statement.where(RoleModel.is_deleted == False)
        if with_relationship:
            statement = statement.options(selectinload(RoleModel.actions))
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: RoleModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: RoleModel, session: Session):
        item = session.merge(item)
        session.add(item)

    @staticmethod
    def hard_delete(role: RoleModel, session: Session) -> None:
        """Перманентне видалення ролі: знімає її з усіх працівників і чистить призначені дії."""
        for link in session.exec(
            select(WorkersRolesModel).where(WorkersRolesModel.id_role == role.id)
        ).all():
            session.delete(link)
        for link in session.exec(
            select(RolesActionsModel).where(RolesActionsModel.id_role == role.id)
        ).all():
            session.delete(link)
        session.flush()
        session.delete(role)
