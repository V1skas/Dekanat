import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.entry_base import EntryBaseDao
from Dekanat.models import EntryBaseModel
from Dekanat.audit import (
    record_action,
    EntryBaseCreated,
    EntryBaseUpdated,
    EntryBaseDeleted,
)


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

    def add_one(self, item: EntryBaseModel, actor_id: Optional[int] = None) -> EntryBaseModel:
        try:
            with rx.session() as session:
                EntryBaseDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, EntryBaseCreated(title=item.title, prefix=item.prefix))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[EntryBaseService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntryBaseModel, actor_id: Optional[int] = None) -> EntryBaseModel:
        try:
            with rx.session() as session:
                old = EntryBaseDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    prefix=old.prefix if old else None,
                )
                managed = EntryBaseDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, EntryBaseUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[EntryBaseService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntryBaseModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntryBaseDao.edit_one(item, session)
                record_action(session, actor_id, item.id, EntryBaseDeleted(title=item.title, prefix=item.prefix))
                session.commit()
            return True
        except Exception as e:
            print(f"[EntryBaseService][delete_one][ERROR] {e}")
            return False
