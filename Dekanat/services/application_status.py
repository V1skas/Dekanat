import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.application_status import ApplicationStatusDao
from Dekanat.models import ApplicationStatusModel


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

    def add_one(self, item: ApplicationStatusModel) -> ApplicationStatusModel:
        try:
            with rx.session() as session:
                ApplicationStatusDao.add_one(item, session)
                session.flush()
                # Якщо новий статус — дефолтний, знімаємо прапорець з решти (інваріант).
                if item.is_default:
                    ApplicationStatusDao.clear_default_except(item.id, session)
                session.commit()
                session.refresh(item)
            return item
        except Exception as e:
            print(f"[ApplicationStatusService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: ApplicationStatusModel) -> ApplicationStatusModel:
        try:
            with rx.session() as session:
                managed = ApplicationStatusDao.edit_one(item, session)
                session.flush()
                if managed.is_default:
                    ApplicationStatusDao.clear_default_except(managed.id, session)
                session.commit()
                session.refresh(managed)
            return managed
        except Exception as e:
            print(f"[ApplicationStatusService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: ApplicationStatusModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                ApplicationStatusDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[ApplicationStatusService][delete_one][ERROR] {e}")
            return False
