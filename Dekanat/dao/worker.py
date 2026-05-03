from typing import Optional, List
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import RoleModel, WorkerModel, ActionModel, WorkersActionsModel, WorkersRolesModel, RolesActionsModel


class WorkerDao:
    @staticmethod
    def get_by_id_with_roles_and_actions(id: int, session: Session) -> Optional[WorkerModel]:
        try:
            statement = select(WorkerModel).options(
                selectinload(WorkerModel.roles),
                selectinload(WorkerModel.actions)
            ).where(WorkerModel.id == id)

            return session.exec(statement).one_or_none()
        except Exception as e:
            print(f"[WorkerDao][get_by_id_with_roles_and_actions][ERROR] {e}")
            return None

    @staticmethod
    def get_by_id(id: int, session: Session) -> Optional[WorkerModel]:
        try:
            statement = select(WorkerModel).where(WorkerModel.id == id)
            return session.exec(statement).one_or_none()
        except Exception as e:
            print(f"[WorkerDao][get_by_id][ERROR] {e}")
            return None

    @staticmethod
    def get_worker_actions_by_id(id: int, session: Session) -> List[ActionModel]:
        try:
            statement = select(
                ActionModel
                ).where(
                    ActionModel.id == WorkersActionsModel.id_action
                    ).where(
                        WorkersActionsModel.id_worker == id
                    )
            return session.exec(statement).all()
        except Exception as e:
            print(f"[WorkerDao][get_worker_actions_by_id][ERROR] {e}")
            return []

    @staticmethod
    def get_worker_actions_in_roles_by_id(id: int, session: Session) -> List[ActionModel]:
        try:
            statement = select(
                ActionModel
            ).where(
                ActionModel.id == RolesActionsModel.id_action
            ).where(
                RolesActionsModel.id_role == RoleModel.id
            ).where(
                RoleModel.id == WorkersRolesModel.id_role
            ).where(
                WorkersRolesModel.id_worker == WorkerModel.id
            )
            return session.exec(statement).all()
        except Exception as e:
            print(f"[WorkerDao][get_worker_actions_in_roles_by_id][ERROR] {e}")
            return []
    
    @staticmethod
    def get_by_login(login: str, session: Session, with_delete=False):
        try:
            statement = select(WorkerModel).where(WorkerModel.login == login)
            if not with_delete:
                statement = statement.where(WorkerModel.is_deleted == False)
            result = session.exec(statement).one_or_none()
            if result:
                session.expunge_all()
            return result
        except Exception as e:
            print(f"[WorkerDao][get_by_login][ERROR] {e}")
            return None
