import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.item_zno import ItemZnoDao
from Dekanat.models import ItemZnoModel


class ItemZnoService:
    def get_list_items(self) -> Sequence[ItemZnoModel]:
        try:
            with rx.session() as session:
                return ItemZnoDao.get_all(session)
        except Exception as e:
            print(f"[ItemZnoService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[ItemZnoModel]:
        try:
            with rx.session() as session:
                return ItemZnoDao.get_by_id(id, session)
        except Exception as e:
            print(f"[ItemZnoService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: ItemZnoModel) -> ItemZnoModel:
        try:
            with rx.session() as session:
                ItemZnoDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[ItemZnoService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: ItemZnoModel) -> ItemZnoModel:
        try:
            with rx.session() as session:
                managed = ItemZnoDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[ItemZnoService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: ItemZnoModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                ItemZnoDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[ItemZnoService][delete_one][ERROR] {e}")
            return False
