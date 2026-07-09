import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.special_condition import SpecialConditionDao
from Dekanat.models import SpecialConditionModel
from Dekanat.audit import (
    record_action,
    SpecialConditionCreated,
    SpecialConditionUpdated,
    SpecialConditionDeleted,
)


class SpecialConditionService:
    def get_list_items(self) -> Sequence[SpecialConditionModel]:
        try:
            with rx.session() as session:
                return SpecialConditionDao.get_all(session)
        except Exception as e:
            print(f"[SpecialConditionService][get_list_items][ERROR] {e}")
            raise

    def get_by_code(self, code: str) -> Optional[SpecialConditionModel]:
        try:
            with rx.session() as session:
                return SpecialConditionDao.get_by_code(code, session)
        except Exception as e:
            print(f"[SpecialConditionService][get_by_code][ERROR] {e}")
            raise

    def add_one(self, item: SpecialConditionModel, actor_id: Optional[int] = None) -> SpecialConditionModel:
        try:
            with rx.session() as session:
                SpecialConditionDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.subcategory_code, SpecialConditionCreated(
                    subcategory_code=item.subcategory_code,
                    title=item.title,
                    is_kvota=item.is_kvota,
                ))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialConditionService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: SpecialConditionModel, actor_id: Optional[int] = None) -> SpecialConditionModel:
        try:
            with rx.session() as session:
                old = SpecialConditionDao.get_by_code(item.subcategory_code, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    description=old.description if old else None,
                    is_kvota=old.is_kvota if old else None,
                )
                managed = SpecialConditionDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.subcategory_code, SpecialConditionUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[SpecialConditionService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SpecialConditionModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SpecialConditionDao.edit_one(item, session)
                record_action(session, actor_id, item.subcategory_code, SpecialConditionDeleted(
                    subcategory_code=item.subcategory_code, title=item.title,
                ))
                session.commit()
            return True
        except Exception as e:
            print(f"[SpecialConditionService][delete_one][ERROR] {e}")
            return False
