import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.kinship import KinshipDao
from Dekanat.models import KinshipModel
from Dekanat.audit import record_action, KinshipCreated, KinshipUpdated, KinshipDeleted


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

    def add_one(self, item: KinshipModel, actor_id: Optional[int] = None) -> KinshipModel:
        try:
            with rx.session() as session:
                KinshipDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, KinshipCreated(title=item.title))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[KinshipService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: KinshipModel, actor_id: Optional[int] = None) -> KinshipModel:
        try:
            with rx.session() as session:
                old = KinshipDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(title=old.title if old else None)
                managed = KinshipDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, KinshipUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[KinshipService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: KinshipModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                KinshipDao.edit_one(item, session)
                record_action(session, actor_id, item.id, KinshipDeleted(title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[KinshipService][delete_one][ERROR] {e}")
            return False
