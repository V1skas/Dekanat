import reflex as rx

from typing import Dict, List, Optional, Sequence

from Dekanat.dao.admission_campaign_speciality import AdmissionCampaignSpecialityDao
from Dekanat.dao.speciality import SpecialityDao
from Dekanat.dao.entry_base import EntryBaseDao
from Dekanat.dao.form_of_study import FormOfStudyDao
from Dekanat.dao.source_of_funding import SourceOfFundingDao
from Dekanat.models import AdmissionCampaignSpecialityModel, AdmissionCampaignSpecialityFundingModel
from Dekanat.audit import record_action, diff_collection, AdmissionCampaignUpdated


def _funding_value(pairs) -> str:
    """`[(назва джерела, місця), ...]` → `"Бюджет: 20, Контракт: 10"` (DK-66).
    Порожній список — усе одно непорожній рядок, щоб «0 квот» відрізнялось
    від «немає значення для порівняння» (None у diff_collection)."""
    return ", ".join(f"{title}: {places}" for title, places in pairs) if pairs else "0 місць"


def _old_quota_rows(items: Sequence[AdmissionCampaignSpecialityModel]) -> List[Dict]:
    rows = []
    for it in items:
        spec = f"{it.speciality.code} {it.speciality.title}" if it.speciality is not None else f"#{it.id_speciality}"
        base = it.entry_base.title if it.entry_base is not None else f"#{it.id_entry_base}"
        form = it.form_of_study.title if it.form_of_study is not None else f"#{it.id_form_of_study}"
        pairs = sorted(
            (f.source_of_funding.title if f.source_of_funding is not None else f"#{f.id_source_of_funding}", f.places)
            for f in (it.funding or [])
        )
        rows.append({
            "id_key": (it.id_speciality, it.id_entry_base, it.id_form_of_study),
            "identity": f"{spec} ({base}, {form})",
            "value": _funding_value(pairs),
        })
    return rows


def _new_quota_rows(items: List, maps: Dict) -> List[Dict]:
    rows = []
    for it in items:
        spec = maps["speciality"].get(it.id_speciality, f"#{it.id_speciality}")
        base = maps["entry_base"].get(it.id_entry_base, f"#{it.id_entry_base}")
        form = maps["form_of_study"].get(it.id_form_of_study, f"#{it.id_form_of_study}")
        funding: Dict = it.funding or {}
        pairs = sorted(
            (maps["source_of_funding"].get(int(sid), f"#{sid}"), places)
            for sid, places in funding.items()
        )
        rows.append({
            "id_key": (it.id_speciality, it.id_entry_base, it.id_form_of_study),
            "identity": f"{spec} ({base}, {form})",
            "value": _funding_value(pairs),
        })
    return rows


class AdmissionCampaignSpecialityService:
    def get_by_campaign(self, id_campaign: int) -> Sequence[AdmissionCampaignSpecialityModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignSpecialityDao.get_by_campaign(id_campaign, session)
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][get_by_campaign][ERROR] {e}")
            raise

    def replace_all_for_campaign(self, id_campaign: int, items: List, actor_id: Optional[int] = None) -> None:
        """Повністю замінює список квот для кампанії: видаляє всі існуючі та вставляє передані.

        Кожен елемент `items` — довільний обʼєкт з атрибутами `id_speciality`,
        `id_entry_base`, `id_form_of_study` і `funding` (Dict[str|int, int] —
        кількість місць по кожному `id_source_of_funding`, DK-52). Diff квот
        (додано/вилучено/змінено, за назвою спеціальності+бази+форми, DK-66)
        пишеться окремим записом журналу — `replace_all_for_campaign` викликається
        окремо від `AdmissionCampaignService.edit_one`, тож не може домішатись у
        той самий diff скалярних полів кампанії."""
        try:
            with rx.session() as session:
                old_rows = _old_quota_rows(AdmissionCampaignSpecialityDao.get_by_campaign(id_campaign, session))
                maps = {
                    "speciality": {r.id: f"{r.code} {r.title}" for r in SpecialityDao.get_all(session, with_del=True)},
                    "entry_base": {r.id: r.title for r in EntryBaseDao.get_all(session, with_del=True)},
                    "form_of_study": {r.id: r.title for r in FormOfStudyDao.get_all(session, with_del=True)},
                    "source_of_funding": {r.id: r.title for r in SourceOfFundingDao.get_all(session, with_del=True)},
                }
                new_rows = _new_quota_rows(items, maps)

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

                change = diff_collection("Квоти", old_rows, new_rows)
                if change.has_changes():
                    record_action(session, actor_id, id_campaign, AdmissionCampaignUpdated(quotas=change))

                session.commit()
        except Exception as e:
            print(f"[AdmissionCampaignSpecialityService][replace_all_for_campaign][ERROR] {e}")
            raise
