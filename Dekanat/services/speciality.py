import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.speciality import SpecialityDao
from Dekanat.models import SpecialityModel
from Dekanat.audit import (
    record_action,
    SpecialityCreated,
    SpecialityUpdated,
    SpecialityDeleted,
)


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

    def add_one(self, item: SpecialityModel, actor_id: Optional[int] = None) -> SpecialityModel:
        try:
            with rx.session() as session:
                # Логічна унікальність (code, id_department, tag) серед не видалених (DK-38).
                if SpecialityDao.get_duplicate(item.code, item.id_department, item.tag, session) is not None:
                    raise ValueError("Спеціальність з таким кодом, відділенням і тегом вже існує")
                item.id = None  # type: ignore[assignment]
                SpecialityDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, SpecialityCreated(
                    code=item.code, title=item.title, tag=item.tag, id_department=item.id_department,
                ))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SpecialityService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: SpecialityModel, actor_id: Optional[int] = None) -> SpecialityModel:
        try:
            with rx.session() as session:
                if SpecialityDao.get_duplicate(item.code, item.id_department, item.tag, session, exclude_id=item.id) is not None:
                    raise ValueError("Спеціальність з таким кодом, відділенням і тегом вже існує")
                # Читаємо старий рядок через `session.get` (без eager `department`):
                # `SpecialityDao.get_by_id` підвантажив би DepartmentModel, який конфліктує
                # з `item.department`, що його несе завантажена картка при merge (DK-55).
                old = session.get(SpecialityModel, item.id)
                old_snap = SimpleNamespace(
                    code=old.code if old else None,
                    title=old.title if old else None,
                    tag=old.tag if old else None,
                    educational_and_professional_program=old.educational_and_professional_program if old else None,
                    id_department=old.id_department if old else None,
                )
                managed = SpecialityDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, SpecialityUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[SpecialityService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SpecialityModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SpecialityDao.edit_one(item, session)
                record_action(session, actor_id, item.id, SpecialityDeleted(code=item.code, title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[SpecialityService][delete_one][ERROR] {e}")
            return False
