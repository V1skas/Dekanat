import reflex as rx

from typing import List, Sequence

from Dekanat.dao.admission_campaign_speciality import AdmissionCampaignSpecialityDao
from Dekanat.models import AdmissionCampaignSpecialityModel


class AdmissionCampaignSpecialityService:
    def get_by_campaign(self, id_campaign: int) -> Sequence[AdmissionCampaignSpecialityModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignSpecialityDao.get_by_campaign(id_campaign, session)
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][get_by_campaign][ERROR] {e}")
            raise

    def replace_all_for_campaign(
        self, id_campaign: int, items: List[AdmissionCampaignSpecialityModel]
    ) -> None:
        """Повністю замінює список квот для кампанії: видаляє всі існуючі та вставляє передані."""
        try:
            with rx.session() as session:
                AdmissionCampaignSpecialityDao.delete_by_campaign(id_campaign, session)
                session.flush()
                for it in items:
                    new_item = AdmissionCampaignSpecialityModel(
                        id_admission_campaign=id_campaign,
                        id_speciality_code=it.id_speciality_code,
                        id_speciality_department=it.id_speciality_department,
                        budget_places=it.budget_places,
                        contract_places=it.contract_places,
                    )
                    AdmissionCampaignSpecialityDao.add_one(new_item, session)
                session.commit()
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][replace_all_for_campaign][ERROR] {e}")
            raise
