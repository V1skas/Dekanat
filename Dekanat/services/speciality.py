import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.speciality import SpecialityDao
from Dekanat.models import SpecialityModel


class SpecialityService:
    def get_list_items(self) -> Sequence[SpecialityModel]:
        try:
            with rx.session() as session:
                return SpecialityDao.get_all(session)
        except Exception as e:
            print(f"[SpecialityService][get_list_items][ERROR] {e}")
            raise

    def get_by_pk(self, code: str, id_department: int) -> Optional[SpecialityModel]:
        try:
            with rx.session() as session:
                return SpecialityDao.get_by_pk(code, id_department, session)
        except Exception as e:
            print(f"[SpecialityService][get_by_pk][ERROR] {e}")
            raise

    def add_one(self, item: SpecialityModel) -> SpecialityModel:
        try:
            with rx.session() as session:
                SpecialityDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialityService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: SpecialityModel) -> SpecialityModel:
        try:
            with rx.session() as session:
                SpecialityDao.edit_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialityService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SpecialityModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SpecialityDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[SpecialityService][delete_one][ERROR] {e}")
            return False
