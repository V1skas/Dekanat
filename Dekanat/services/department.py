import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.department import DepartmentDao
from Dekanat.models import DepartmentModel
from Dekanat.audit import (
    record_action,
    DepartmentCreated,
    DepartmentUpdated,
    DepartmentDeleted,
)


class DepartmentService:
    def get_list_items(self) -> Sequence[DepartmentModel]:
        try:
            with rx.session() as session:
                return DepartmentDao.get_all(session)
        except Exception as e:
            print(f"[DepartmentService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[DepartmentModel]:
        try:
            with rx.session() as session:
                return DepartmentDao.get_by_id(id, session)
        except Exception as e:
            print(f"[DepartmentService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: DepartmentModel, actor_id: Optional[int] = None) -> DepartmentModel:
        try:
            with rx.session() as session:
                DepartmentDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, DepartmentCreated(title=item.title))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[DepartmentService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: DepartmentModel, actor_id: Optional[int] = None) -> DepartmentModel:
        try:
            with rx.session() as session:
                old = DepartmentDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(title=old.title if old else None)
                managed = DepartmentDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, DepartmentUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[DepartmentService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: DepartmentModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                DepartmentDao.edit_one(item, session)
                record_action(session, actor_id, item.id, DepartmentDeleted(title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[DepartmentService][delete_one][ERROR] {e}")
            return False
