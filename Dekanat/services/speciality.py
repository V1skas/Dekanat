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

    def get_by_id(self, id: int) -> Optional[SpecialityModel]:
        try:
            with rx.session() as session:
                return SpecialityDao.get_by_id(id, session)
        except Exception as e:
            print(f"[SpecialityService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: SpecialityModel) -> SpecialityModel:
        try:
            with rx.session() as session:
                # Логічна унікальність (code, id_department, tag) серед не видалених (DK-38).
                if SpecialityDao.get_duplicate(item.code, item.id_department, item.tag, session) is not None:
                    raise ValueError("Спеціальність з таким кодом, відділенням і тегом вже існує")
                item.id = None  # type: ignore[assignment]
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
                if SpecialityDao.get_duplicate(item.code, item.id_department, item.tag, session, exclude_id=item.id) is not None:
                    raise ValueError("Спеціальність з таким кодом, відділенням і тегом вже існує")
                managed = SpecialityDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
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
