import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence

from Dekanat.dao.application_status import ApplicationStatusDao
from Dekanat.models import ApplicationStatusModel
from Dekanat.audit import (
    record_action,
    ApplicationStatusCreated,
    ApplicationStatusUpdated,
    ApplicationStatusDeleted,
)


class ApplicationStatusService:
    def get_list_items(self) -> Sequence[ApplicationStatusModel]:
        try:
            with rx.session() as session:
                return ApplicationStatusDao.get_all(session)
        except Exception as e:
            print(f"[ApplicationStatusService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[ApplicationStatusModel]:
        try:
            with rx.session() as session:
                return ApplicationStatusDao.get_by_id(id, session)
        except Exception as e:
            print(f"[ApplicationStatusService][get_by_id][ERROR] {e}")
            raise

    def get_default(self) -> Optional[ApplicationStatusModel]:
        """Дефолтний статус для нових карток абітурієнтів (DK-36)."""
        try:
            with rx.session() as session:
                return ApplicationStatusDao.get_default(session)
        except Exception as e:
            print(f"[ApplicationStatusService][get_default][ERROR] {e}")
            raise

    def add_one(self, item: ApplicationStatusModel, actor_id: Optional[int] = None) -> ApplicationStatusModel:
        try:
            with rx.session() as session:
                ApplicationStatusDao.add_one(item, session)
                session.flush()
                # Якщо новий статус — дефолтний, знімаємо прапорець з решти (інваріант).
                if item.is_default:
                    ApplicationStatusDao.clear_default_except(item.id, session)
                record_action(session, actor_id, item.id, ApplicationStatusCreated(
                    title=item.title,
                    is_default=item.is_default,
                    is_allowed_in_rating=item.is_allowed_in_rating,
                ))
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[ApplicationStatusService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: ApplicationStatusModel, actor_id: Optional[int] = None) -> ApplicationStatusModel:
        try:
            with rx.session() as session:
                old = ApplicationStatusDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(
                    title=old.title if old else None,
                    description=old.description if old else None,
                    is_default=old.is_default if old else None,
                    is_allowed_in_rating=old.is_allowed_in_rating if old else None,
                )
                managed = ApplicationStatusDao.edit_one(item, session)
                session.flush()
                if managed.is_default:
                    ApplicationStatusDao.clear_default_except(managed.id, session)
                record_action(session, actor_id, item.id, ApplicationStatusUpdated.from_diff(old_snap, managed))
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[ApplicationStatusService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: ApplicationStatusModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                ApplicationStatusDao.edit_one(item, session)
                record_action(session, actor_id, item.id, ApplicationStatusDeleted(title=item.title))
                session.commit()
            return True
        except Exception as e:
            print(f"[ApplicationStatusService][delete_one][ERROR] {e}")
            return False
