import reflex as rx

from typing import Optional, Sequence, List, Tuple

from Dekanat.dao.entrant_exam import EntrantExamDao
from Dekanat.models import EntrantExamModel


class EntrantExamService:
    def get_list_items(
        self,
        id_group: Optional[int] = None,
        id_item_zno: Optional[int] = None,
        id_worker: Optional[int] = None,
        date_between: Optional[Tuple[str, str]] = None,
    ) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_all(
                    session,
                    id_group=id_group,
                    id_item_zno=id_item_zno,
                    id_worker=id_worker,
                    date_between=date_between,
                )
        except Exception as e:
            print(f"[EntrantExamService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantExamService][get_by_id][ERROR] {e}")
            raise

    def get_by_group(self, group_id: int) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantExamDao.get_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantExamService][get_by_group][ERROR] {e}")
            raise

    def add_one(self, item: EntrantExamModel, worker_ids: List[int]) -> EntrantExamModel:
        try:
            with rx.session() as session:
                managed = EntrantExamDao.add_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantExamModel, worker_ids: List[int]) -> EntrantExamModel:
        try:
            with rx.session() as session:
                managed = EntrantExamDao.edit_one(item, session)
                session.flush()
                EntrantExamDao.replace_workers(managed.id, worker_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantExamService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantExamModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantExamDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantExamService][delete_one][ERROR] {e}")
            return False
