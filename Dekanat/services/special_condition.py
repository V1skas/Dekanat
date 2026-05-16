import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.special_condition import SpecialConditionDao
from Dekanat.models import SpecialConditionModel


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

    def add_one(self, item: SpecialConditionModel) -> SpecialConditionModel:
        try:
            with rx.session() as session:
                SpecialConditionDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialConditionService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: SpecialConditionModel) -> SpecialConditionModel:
        try:
            with rx.session() as session:
                SpecialConditionDao.edit_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialConditionService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SpecialConditionModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SpecialConditionDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[SpecialConditionService][delete_one][ERROR] {e}")
            return False
