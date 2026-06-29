import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.department import DepartmentDao
from Dekanat.models import DepartmentModel


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

    def add_one(self, item: DepartmentModel) -> DepartmentModel:
        try:
            with rx.session() as session:
                DepartmentDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[DepartmentService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: DepartmentModel) -> DepartmentModel:
        try:
            with rx.session() as session:
                managed = DepartmentDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[DepartmentService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: DepartmentModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                DepartmentDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[DepartmentService][delete_one][ERROR] {e}")
            return False
