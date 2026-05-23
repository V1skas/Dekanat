import reflex as rx

from typing import List, Dict
from pydantic import BaseModel, Field

from Dekanat.actions import Actions


class RatingGroup(BaseModel):
    spec_key: str = ""
    spec_label: str = ""
    rows: List[Dict[str, str]] = Field(default_factory=list)

from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.rating import RatingService


def _spec_key(code: str, dept: int) -> str:
    return f"{code}|{dept}"


class ListRatingState(AppState):
    in_progress: bool = True
    generating: bool = False

    campaigns: List[AdmissionCampaignModel] = []
    selected_campaign_id: int = 0

    # "__all__" — всі спеціальності кампанії
    selected_spec_key: str = "__all__"

    # Кеш доступних спеціальностей з квот вибраної кампанії
    speciality_options: List[Dict[str, str]] = []

    # Згруповано за спеціальністю: окрема таблиця для кожної.
    groups: List[RatingGroup] = []

    generated_at_display: str = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.RATING_VIEW):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_progress = True
        try:
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            active = campaign_service.get_active_campaign()
            if active is not None and active.id is not None:
                self.selected_campaign_id = active.id
            elif self.campaigns:
                self.selected_campaign_id = self.campaigns[0].id or 0
            else:
                self.selected_campaign_id = 0

            self._reload_speciality_options()
            self._load_latest_snapshot()
            self.in_progress = False
        except Exception:
            self.in_progress = False
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")

    def _reload_speciality_options(self):
        from Dekanat.services.admission_campaign_speciality import (
            AdmissionCampaignSpecialityService,
        )
        opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі спеціальності"}]
        if self.selected_campaign_id:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(self.selected_campaign_id)
            for q in quotas:
                label = (
                    f"{q.speciality.code} {q.speciality.title}"
                    if q.speciality is not None
                    else f"{q.id_speciality_code}"
                )
                opts.append(
                    {
                        "value": _spec_key(q.id_speciality_code, q.id_speciality_department),
                        "label": label,
                    }
                )
        self.speciality_options = opts
        if not any(o["value"] == self.selected_spec_key for o in opts):
            self.selected_spec_key = "__all__"

    def _load_latest_snapshot(self):
        self.groups = []
        self.generated_at_display = ""
        if not self.selected_campaign_id:
            return

        snapshot, entries = RatingService().get_latest_for_campaign(self.selected_campaign_id)
        if snapshot is None:
            return
        try:
            self.generated_at_display = snapshot.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            self.generated_at_display = str(snapshot.generated_at)

        self._fill_from_entries(entries)

    def _fill_from_entries(self, entries):
        groups_by_key: Dict[str, RatingGroup] = {}
        order: List[str] = []

        for e in entries:
            key = _spec_key(e.id_speciality_code, e.id_speciality_department)
            if self.selected_spec_key != "__all__" and key != self.selected_spec_key:
                continue
            spec_label = (
                f"{e.speciality.code} {e.speciality.title}"
                if e.speciality is not None
                else f"{e.id_speciality_code}"
            )
            pib = (
                e.entrant.person.pib
                if e.entrant is not None and e.entrant.person is not None and e.entrant.person.pib
                else f"#{e.id_entrant}"
            )
            if key not in groups_by_key:
                groups_by_key[key] = RatingGroup(spec_key=key, spec_label=spec_label, rows=[])
                order.append(key)
            groups_by_key[key].rows.append(
                {
                    "position": str(e.position),
                    "pib": pib,
                    "total": str(e.total_points),
                    "status": e.status,
                }
            )

        self.groups = [groups_by_key[k] for k in order]

    @rx.var
    def selected_campaign_id_str(self) -> str:
        return str(self.selected_campaign_id) if self.selected_campaign_id else ""

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        return [{"value": str(c.id), "label": c.title} for c in self.campaigns]

    @rx.event
    def set_selected_campaign_id(self, value: str):
        try:
            self.selected_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.selected_campaign_id = 0
        self.selected_spec_key = "__all__"
        self._reload_speciality_options()
        self._load_latest_snapshot()

    @rx.event
    def set_selected_spec_key(self, value: str):
        self.selected_spec_key = value or "__all__"
        # Перерахунок rows з кешованого знімка
        if self.selected_campaign_id:
            _, entries = RatingService().get_latest_for_campaign(self.selected_campaign_id)
            self._fill_from_entries(entries)

    @rx.event
    def on_click_generate(self):
        if not self.has_permission(Actions.RATING_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування рейтингу!")
            return
        if not self.selected_campaign_id:
            yield rx.toast.warning("Оберіть вступну кампанію!")
            return

        self.generating = True
        yield
        try:
            snapshot, entries = RatingService().generate(self.selected_campaign_id)
            try:
                self.generated_at_display = snapshot.generated_at.strftime("%Y-%m-%d %H:%M:%S")
            except AttributeError:
                self.generated_at_display = str(snapshot.generated_at)
            self._fill_from_entries(entries)
            yield rx.toast.success("Рейтинг сформовано!")
        except Exception:
            yield rx.toast.error("Під час формування рейтингу сталася помилка. Спробуйте ще раз.")
        finally:
            self.generating = False
