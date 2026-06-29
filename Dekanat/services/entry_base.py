import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.entry_base import EntryBaseDao
from Dekanat.models import EntryBaseModel


class EntryBaseService:
    def get_list_items(self) -> Sequence[EntryBaseModel]:
        try:
            with rx.session() as session:
                return EntryBaseDao.get_all(session)
        except Exception as e:
            print(f"[EntryBaseService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntryBaseModel]:
        try:
            with rx.session() as session:
                return EntryBaseDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntryBaseService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: EntryBaseModel) -> EntryBaseModel:
        try:
            with rx.session() as session:
                EntryBaseDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[EntryBaseService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntryBaseModel) -> EntryBaseModel:
        try:
            with rx.session() as session:
                managed = EntryBaseDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[EntryBaseService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntryBaseModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntryBaseDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntryBaseService][delete_one][ERROR] {e}")
            return False
