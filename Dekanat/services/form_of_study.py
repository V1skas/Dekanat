import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.form_of_study import FormOfStudyDao
from Dekanat.models import FormOfStudyModel
from Dekanat.audit import (
    record_action,
    FormOfStudyCreated,
    FormOfStudyUpdated,
    FormOfStudyDeleted,
)


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

    def add_one(self, item: FormOfStudyModel, actor_id: Optional[int] = None) -> FormOfStudyModel:
        try:
            with rx.session() as session:
                FormOfStudyDao.add_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, FormOfStudyCreated(title=item.title, prefix=item.prefix))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[FormOfStudyService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: FormOfStudyModel, actor_id: Optional[int] = None) -> FormOfStudyModel:
        try:
            with rx.session() as session:
                old = FormOfStudyDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    prefix=old.prefix if old else None,
                )
                managed = FormOfStudyDao.edit_one(item, session)
                session.flush()
                record_action(session, actor_id, item.id, FormOfStudyUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[FormOfStudyService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: FormOfStudyModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                FormOfStudyDao.edit_one(item, session)
                record_action(session, actor_id, item.id, FormOfStudyDeleted(title=item.title, prefix=item.prefix))
                session.commit()
            return True
        except Exception as e:
            print(f"[FormOfStudyService][delete_one][ERROR] {e}")
            return False
