import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.form_of_study import FormOfStudyDao
from Dekanat.models import FormOfStudyModel


class FormOfStudyService:
    def get_list_items(self) -> Sequence[FormOfStudyModel]:
        try:
            with rx.session() as session:
                return FormOfStudyDao.get_all(session)
        except Exception as e:
            print(f"[FormOfStudyService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[FormOfStudyModel]:
        try:
            with rx.session() as session:
                return FormOfStudyDao.get_by_id(id, session)
        except Exception as e:
            print(f"[FormOfStudyService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: FormOfStudyModel) -> FormOfStudyModel:
        try:
            with rx.session() as session:
                FormOfStudyDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[FormOfStudyService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: FormOfStudyModel) -> FormOfStudyModel:
        try:
            with rx.session() as session:
                managed = FormOfStudyDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[FormOfStudyService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: FormOfStudyModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                FormOfStudyDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[FormOfStudyService][delete_one][ERROR] {e}")
            return False
