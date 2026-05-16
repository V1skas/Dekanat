import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.models import EntrantGroupModel


class EntrantsGroupService:
    def get_list_items(self) -> Sequence[EntrantGroupModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_all(session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantGroupModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: EntrantGroupModel) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                EntrantsGroupDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[EntrantsGroupService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantGroupModel) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                EntrantsGroupDao.edit_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[EntrantsGroupService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantGroupModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantsGroupDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantsGroupService][delete_one][ERROR] {e}")
            return False
