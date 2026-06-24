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

    # Згорнутий стан картки фільтрів: показуються лише маркери, дата та кнопка розгортання.
    filter_collapsed: bool = False

    # "__all__" — без фільтра
    selected_spec_key: str = "__all__"
    selected_base_key: str = "__all__"
    selected_form_key: str = "__all__"

    # Кеш доступних опцій фільтрів з квот вибраної кампанії
    speciality_options: List[Dict[str, str]] = []
    base_filter_options: List[Dict[str, str]] = []
    form_filter_options: List[Dict[str, str]] = []

    # Лейбли довідників бази вступу та форми навчання (для підписів груп) — DK-26
    entry_base_labels: Dict[str, str] = {}
    form_labels: Dict[str, str] = {}

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

            self._load_reference_labels()
            self._reload_speciality_options()
            self._load_latest_snapshot()
            self.in_progress = False
        except Exception:
            self.in_progress = False
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")

    def _load_reference_labels(self):
        from Dekanat.services.entry_base import EntryBaseService
        from Dekanat.services.form_of_study import FormOfStudyService

        self.entry_base_labels = {
            str(b.id): b.title for b in EntryBaseService().get_list_items()
        }
        self.form_labels = {
            str(f.id): f.title for f in FormOfStudyService().get_list_items()
        }

    def _reload_speciality_options(self):
        from Dekanat.services.admission_campaign_speciality import (
            AdmissionCampaignSpecialityService,
        )
        # Кожна спеціальність — лише раз (квоти повторюють її для різних база/форма).
        spec_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі спеціальності"}]
        base_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі бази вступу"}]
        form_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі форми навчання"}]
        seen_spec: set = set()
        seen_base: set = set()
        seen_form: set = set()
        if self.selected_campaign_id:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(self.selected_campaign_id)
            for q in quotas:
                sk = _spec_key(q.id_speciality_code, q.id_speciality_department)
                if sk not in seen_spec:
                    seen_spec.add(sk)
                    label = (
                        f"{q.speciality.code} {q.speciality.title}"
                        if q.speciality is not None
                        else f"{q.id_speciality_code}"
                    )
                    spec_opts.append({"value": sk, "label": label})
                bk = str(q.id_entry_base)
                if bk not in seen_base:
                    seen_base.add(bk)
                    base_opts.append({"value": bk, "label": self.entry_base_labels.get(bk, bk)})
                fk = str(q.id_form_of_study)
                if fk not in seen_form:
                    seen_form.add(fk)
                    form_opts.append({"value": fk, "label": self.form_labels.get(fk, fk)})
        self.speciality_options = spec_opts
        self.base_filter_options = base_opts
        self.form_filter_options = form_opts
        if not any(o["value"] == self.selected_spec_key for o in spec_opts):
            self.selected_spec_key = "__all__"
        if not any(o["value"] == self.selected_base_key for o in base_opts):
            self.selected_base_key = "__all__"
        if not any(o["value"] == self.selected_form_key for o in form_opts):
            self.selected_form_key = "__all__"

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
            spec_only = _spec_key(e.id_speciality_code, e.id_speciality_department)
            if self.selected_spec_key != "__all__" and spec_only != self.selected_spec_key:
                continue
            if self.selected_base_key != "__all__" and str(e.id_entry_base) != self.selected_base_key:
                continue
            if self.selected_form_key != "__all__" and str(e.id_form_of_study) != self.selected_form_key:
                continue
            # Групуємо за кортежем спеціальність+база+форма — однакові спеціальності
            # з різною базою/формою показуються окремими таблицями (DK-26).
            group_key = f"{spec_only}|{e.id_entry_base}|{e.id_form_of_study}"
            spec_name = (
                f"{e.speciality.code} {e.speciality.title}"
                if e.speciality is not None
                else f"{e.id_speciality_code}"
            )
            base_name = self.entry_base_labels.get(str(e.id_entry_base), "—")
            form_name = self.form_labels.get(str(e.id_form_of_study), "—")
            spec_label = f"{spec_name} · {base_name} · {form_name}"
            pib = (
                e.entrant.person.pib
                if e.entrant is not None and e.entrant.person is not None and e.entrant.person.pib
                else f"#{e.id_entrant}"
            )
            if group_key not in groups_by_key:
                groups_by_key[group_key] = RatingGroup(spec_key=group_key, spec_label=spec_label, rows=[])
                order.append(group_key)
            groups_by_key[group_key].rows.append(
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
        self.selected_base_key = "__all__"
        self.selected_form_key = "__all__"
        self._reload_speciality_options()
        self._load_latest_snapshot()

    @rx.event
    def toggle_filter_collapsed(self):
        self.filter_collapsed = not self.filter_collapsed

    def _refill_from_latest(self):
        """Перерахунок груп з кешованого знімка під поточні фільтри."""
        if self.selected_campaign_id:
            _, entries = RatingService().get_latest_for_campaign(self.selected_campaign_id)
            self._fill_from_entries(entries)

    @rx.event
    def set_selected_spec_key(self, value: str):
        self.selected_spec_key = value or "__all__"
        self._refill_from_latest()

    @rx.event
    def set_selected_base_key(self, value: str):
        self.selected_base_key = value or "__all__"
        self._refill_from_latest()

    @rx.event
    def set_selected_form_key(self, value: str):
        self.selected_form_key = value or "__all__"
        self._refill_from_latest()

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
