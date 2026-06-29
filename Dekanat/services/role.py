import reflex as rx

from typing import Optional, Sequence, List
from sqlmodel import select

from Dekanat.dao.role import RoleDao
from Dekanat.models import ActionModel, RoleModel, WorkerModel, WorkersRolesModel


class RoleService:
    def get_list_items(self) -> Sequence[RoleModel]:
        try:
            with rx.session() as session:
                return RoleDao.get_all(session)
        except Exception as e:
            print(f"[RoleService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[RoleModel]:
        try:
            with rx.session() as session:
                return RoleDao.get_by_id(id, session, with_relationship=True)
        except Exception as e:
            print(f"[RoleService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, title: str, description: Optional[str], action_ids: List[int]) -> int:
        try:
            with rx.session() as session:
                actions = [a for a in (session.get(ActionModel, aid) for aid in action_ids) if a is not None]
                role = RoleModel(title=title, description=description, actions=actions)
                session.add(role)
                session.commit()
                session.refresh(role)
                return role.id
        except Exception as e:
            print(f"[RoleService][add_one][ERROR] {e}")
            raise

    def edit_one(self, id: int, title: str, description: Optional[str], action_ids: List[int]) -> bool:
        try:
            with rx.session() as session:
                role = RoleDao.get_by_id(id, session, with_relationship=True)
                if role is None:
                    return False
                role.title = title
                role.description = description
                actions = [a for a in (session.get(ActionModel, aid) for aid in action_ids) if a is not None]
                role.actions = actions
                session.add(role)
                # Бамп версії прав у всіх воркерів, які мають цю роль —
                # щоб їх живі сесії перечитали actions_worker на наступному require_auth.
                worker_ids = list(session.exec(
                    select(WorkersRolesModel.id_worker).where(WorkersRolesModel.id_role == id)
                ).all())
                if worker_ids:
                    workers = session.exec(
                        select(WorkerModel).where(WorkerModel.id.in_(worker_ids))  # type: ignore[attr-defined]
                    ).all()
                    for w in workers:
                        w.permissions_version = (w.permissions_version or 0) + 1
                        session.add(w)
                session.commit()
            return True
        except Exception as e:
            print(f"[RoleService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: RoleModel) -> bool:
        """Видаляє роль перманентно — разом з її призначеннями працівникам та діями."""
        try:
            with rx.session() as session:
                role = RoleDao.get_by_id(item.id, session)
                if role is None:
                    return False
                RoleDao.hard_delete(role, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[RoleService][delete_one][ERROR] {e}")
            return False
