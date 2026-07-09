import reflex as rx

from types import SimpleNamespace
from typing import List, Optional, Sequence

from Dekanat.dao.source_of_funding import SourceOfFundingDao, SourceOfFundingEligibilityDao
from Dekanat.models import SourceOfFundingModel, SourceOfFundingEligibilityModel
from Dekanat.audit import (
    record_action,
    SourceOfFundingCreated,
    SourceOfFundingUpdated,
    SourceOfFundingDeleted,
)


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

    def get_eligible_ids(self, id_source_of_funding: int) -> List[int]:
        try:
            with rx.session() as session:
                return list(SourceOfFundingEligibilityDao.get_eligible_ids(id_source_of_funding, session))
        except Exception as e:
            print(f"[SourceOfFundingService][get_eligible_ids][ERROR] {e}")
            raise

    def add_one(
        self,
        item: SourceOfFundingModel,
        eligible_ids: Optional[List[int]] = None,
        actor_id: Optional[int] = None,
    ) -> SourceOfFundingModel:
        try:
            with rx.session() as session:
                SourceOfFundingDao.add_one(item, session)
                session.flush()
                for eligible_id in (eligible_ids or []):
                    SourceOfFundingEligibilityDao.add_one(
                        SourceOfFundingEligibilityModel(
                            id_source_of_funding=item.id,
                            id_eligible_source_of_funding=eligible_id,
                        ),
                        session,
                    )
                record_action(session, actor_id, item.id, SourceOfFundingCreated(title=item.title))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[SourceOfFundingService][add_one][ERROR] {e}")
            raise

    def edit_one(
        self,
        item: SourceOfFundingModel,
        eligible_ids: Optional[List[int]] = None,
        actor_id: Optional[int] = None,
    ) -> SourceOfFundingModel:
        try:
            with rx.session() as session:
                old = SourceOfFundingDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    sequence=old.sequence if old else None,
                    color=old.color if old else None,
                )
                managed = SourceOfFundingDao.edit_one(item, session)
                session.flush()
                if eligible_ids is not None:
                    SourceOfFundingEligibilityDao.delete_for_source(item.id, session)
                    session.flush()
                    for eligible_id in eligible_ids:
                        SourceOfFundingEligibilityDao.add_one(
                            SourceOfFundingEligibilityModel(
                                id_source_of_funding=item.id,
                                id_eligible_source_of_funding=eligible_id,
                            ),
                            session,
                        )
                record_action(session, actor_id, item.id, SourceOfFundingUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[SourceOfFundingService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: SourceOfFundingModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                SourceOfFundingDao.edit_one(item, session)
                record_action(session, actor_id, item.id, SourceOfFundingDeleted(title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[SourceOfFundingService][delete_one][ERROR] {e}")
            return False
