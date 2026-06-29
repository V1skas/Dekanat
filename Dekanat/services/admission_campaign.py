import reflex as rx

from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlmodel import select

from Dekanat.dao.admission_campaign import AdmissionCampaignDao
from Dekanat.models import AdmissionCampaignModel


class AdmissionCampaignService:
    def get_list_items(self) -> Sequence[AdmissionCampaignModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignDao.get_all(session)
        except Exception as e:
            print(f"[AdmissionCampaignService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[AdmissionCampaignModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignDao.get_by_id(id, session)
        except Exception as e:
            print(f"[AdmissionCampaignService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: AdmissionCampaignModel) -> AdmissionCampaignModel:
        try:
            with rx.session() as session:
                managed = AdmissionCampaignDao.add_one(item, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[AdmissionCampaignService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: AdmissionCampaignModel) -> AdmissionCampaignModel:
        try:
            with rx.session() as session:
                managed = AdmissionCampaignDao.edit_one(item, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[AdmissionCampaignService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: AdmissionCampaignModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                AdmissionCampaignDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[AdmissionCampaignService][delete_one][ERROR] {e}")
            return False

    def get_active_campaign(self) -> Optional[AdmissionCampaignModel]:
        """Повертає активну (з-поміж не видалених) кампанію, чий період містить поточну дату.
        Якщо таких декілька — повертається з найпізнішою датою початку.
        Якщо жодної — повертає None."""
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with rx.session() as session:
                statement = (
                    select(AdmissionCampaignModel)
                    .where(AdmissionCampaignModel.is_deleted == False)
                    .where(AdmissionCampaignModel.start_date <= today)
                    .where(AdmissionCampaignModel.end_date >= today)
                    .order_by(AdmissionCampaignModel.start_date.desc())
                )
                return session.exec(statement).first()
        except Exception as e:
            print(f"[AdmissionCampaignService][get_active_campaign][ERROR] {e}")
            return None

    def get_active_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Активна кампанія, конвертована у пару datetime (00:00 початку та 23:59:59 кінця).
        Використовується для фільтрації запитів по created_at."""
        active = self.get_active_campaign()
        if active is None:
            return None
        try:
            start_dt = datetime.strptime(active.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(active.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            return start_dt, end_dt
        except (ValueError, TypeError) as e:
            print(f"[AdmissionCampaignService][get_active_range][ERROR] {e}")
            return None
