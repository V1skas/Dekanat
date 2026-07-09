import reflex as rx

from typing import Dict, List, Sequence

from Dekanat.dao.admission_campaign_speciality import AdmissionCampaignSpecialityDao
from Dekanat.models import AdmissionCampaignSpecialityModel, AdmissionCampaignSpecialityFundingModel


class AdmissionCampaignSpecialityService:
    def get_by_campaign(self, id_campaign: int) -> Sequence[AdmissionCampaignSpecialityModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignSpecialityDao.get_by_campaign(id_campaign, session)
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][get_by_campaign][ERROR] {e}")
            raise

    def replace_all_for_campaign(self, id_campaign: int, items: List) -> None:
        """Повністю замінює список квот для кампанії: видаляє всі існуючі та вставляє передані.

        Кожен елемент `items` — довільний обʼєкт з атрибутами `id_speciality`,
        `id_entry_base`, `id_form_of_study` і `funding` (Dict[str|int, int] —
        кількість місць по кожному `id_source_of_funding`, DK-52)."""
        try:
            with rx.session() as session:
                AdmissionCampaignSpecialityDao.delete_by_campaign(id_campaign, session)
                session.flush()
                for it in items:
                    new_item = AdmissionCampaignSpecialityModel(
                        id_admission_campaign=id_campaign,
                        id_speciality=it.id_speciality,
                        id_entry_base=it.id_entry_base,
                        id_form_of_study=it.id_form_of_study,
                    )
                    AdmissionCampaignSpecialityDao.add_one(new_item, session)
                    funding: Dict = it.funding or {}
                    for id_source_of_funding, places in funding.items():
                        AdmissionCampaignSpecialityDao.add_funding_one(
                            AdmissionCampaignSpecialityFundingModel(
                                id_admission_campaign=id_campaign,
                                id_speciality=it.id_speciality,
                                id_entry_base=it.id_entry_base,
                                id_form_of_study=it.id_form_of_study,
                                id_source_of_funding=int(id_source_of_funding),
                                places=places,
                            ),
                            session,
                        )
                session.commit()
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][replace_all_for_campaign][ERROR] {e}")
            raise
