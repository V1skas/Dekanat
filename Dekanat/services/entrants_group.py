import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.models import EntrantGroupModel, EntrantModel, EntrantExamModel


class EntrantsGroupService:
    def get_list_items(self) -> Sequence[EntrantGroupModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_all(session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantGroupModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                managed = EntrantsGroupDao.add_one(item, session)
                session.flush()
                if entrant_ids:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                managed = EntrantsGroupDao.edit_one(item, session)
                if entrant_ids is not None:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantGroupModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantsGroupDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantsGroupService][delete_one][ERROR] {e}")
            return False

    def get_entrants(self, group_id: int) -> Sequence[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_entrants_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_entrants][ERROR] {e}")
            raise

    def get_assignable_entrants(self, group_id: Optional[int]) -> Sequence[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_assignable_entrants(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_assignable_entrants][ERROR] {e}")
            raise

    def get_exams(self, group_id: int) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_exams_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_exams][ERROR] {e}")
            raise
