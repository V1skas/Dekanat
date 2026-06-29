import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.source_of_funding import SourceOfFundingDao
from Dekanat.models import SourceOfFundingModel


class SourceOfFundingService:
    def get_list_items(self) -> Sequence[SourceOfFundingModel]:
        try:
            with rx.session() as session:
                return SourceOfFundingDao.get_all(session)
        except Exception as e:
            print(f"[SourceOfFundingService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[SourceOfFundingModel]:
        try:
            with rx.session() as session:
                return SourceOfFundingDao.get_by_id(id, session)
        except Exception as e:
            print(f"[SourceOfFundingService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: SourceOfFundingModel) -> SourceOfFundingModel:
        try:
            with rx.session() as session:
                SourceOfFundingDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SourceOfFundingService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: SourceOfFundingModel) -> SourceOfFundingModel:
        try:
            with rx.session() as session:
                managed = SourceOfFundingDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[SourceOfFundingService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SourceOfFundingModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SourceOfFundingDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[SourceOfFundingService][delete_one][ERROR] {e}")
            return False
