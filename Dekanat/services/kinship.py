import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.kinship import KinshipDao
from Dekanat.models import KinshipModel


class KinshipService:
    def get_list_items(self) -> Sequence[KinshipModel]:
        try:
            with rx.session() as session:
                return KinshipDao.get_all(session)
        except Exception as e:
            print(f"[KinshipService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[KinshipModel]:
        try:
            with rx.session() as session:
                return KinshipDao.get_by_id(id, session)
        except Exception as e:
            print(f"[KinshipService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: KinshipModel) -> KinshipModel:
        try:
            with rx.session() as session:
                KinshipDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[KinshipService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: KinshipModel) -> KinshipModel:
        try:
            with rx.session() as session:
                KinshipDao.edit_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[KinshipService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: KinshipModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                KinshipDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[KinshipService][delete_one][ERROR] {e}")
            return False
