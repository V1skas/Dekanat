import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.item_zno import ItemZnoDao
from Dekanat.models import ItemZnoModel
from Dekanat.audit import (
    record_action,
    ItemZnoCreated,
    ItemZnoUpdated,
    ItemZnoDeleted,
)


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

    def add_one(self, item: ItemZnoModel, actor_id: Optional[int] = None) -> ItemZnoModel:
        try:
            with rx.session() as session:
                ItemZnoDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, ItemZnoCreated(
                    title=item.title,
                    coefficient=item.coefficient,
                    is_counted_in_rating=item.is_counted_in_rating,
                ))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[ItemZnoService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: ItemZnoModel, actor_id: Optional[int] = None) -> ItemZnoModel:
        try:
            with rx.session() as session:
                old = ItemZnoDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    coefficient=old.coefficient if old else None,
                    is_counted_in_rating=old.is_counted_in_rating if old else None,
                )
                managed = ItemZnoDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, ItemZnoUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[ItemZnoService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: ItemZnoModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                ItemZnoDao.edit_one(item, session)
                record_action(session, actor_id, item.id, ItemZnoDeleted(title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[ItemZnoService][delete_one][ERROR] {e}")
            return False
