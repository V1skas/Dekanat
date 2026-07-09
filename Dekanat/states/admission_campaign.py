import reflex as rx

from pydantic import BaseModel, Field as PydanticField
from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.admission_campaign_speciality import AdmissionCampaignSpecialityService
from Dekanat.services.source_of_funding import SourceOfFundingService
from Dekanat.services.speciality import SpecialityService
from Dekanat.services.entry_base import EntryBaseService
from Dekanat.services.form_of_study import FormOfStudyService


class QuotaDraft(BaseModel):
    """Один рядок квоти (спеціальність+база+форма) у формі редагування кампанії.

    `funding` — кількість місць по кожному ресурсу фінансування (DK-52),
    ключ — `str(id_source_of_funding)` (Reflex Var-friendly)."""

    id_speciality: int = 0
    id_entry_base: int = 0
    id_form_of_study: int = 0
    funding: Dict[str, int] = PydanticField(default_factory=dict)
    # Сума місць по всіх ресурсах — рахується руками при зміні funding
    # (щоб не покладатись на property/computed_field у Reflex Var, DK-52).
    total_places: int = 0


class QuotaView(BaseModel):
    """Рядок квоти для сторінки перегляду кампанії (read-only, DK-52)."""

    id_speciality: int = 0
    speciality_label: str = ""
    entry_base_label: str = ""
    form_of_study_label: str = ""
    funding_map: Dict[str, int] = PydanticField(default_factory=dict)
    total_places: int = 0


class ListAdmissionCampaignState(AppState):
    items: Optional[Sequence[AdmissionCampaignModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            service = AdmissionCampaignService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ADMISSION_CAMPAIGN_ADD)


class _CampaignFormBase(AppState):
    """Спільний код для додавання/редагування: текстові поля та валідація."""

    item: AdmissionCampaignModel = AdmissionCampaignModel()
    #in_process: bool = True

    # Список квот по спеціальностям (буферизується у пам'яті, зберігається при on_save)
    quotas: List[QuotaDraft] = []

    # Довідник для select'а спеціальностей та лейблів у таблиці квот
    speciality_options: List[Dict[str, str]] = []
    # Довідники бази вступу та форми навчання (DK-26)
    entry_base_options: List[Dict[str, str]] = []
    form_of_study_options: List[Dict[str, str]] = []
    # Активні ресурси фінансування (DK-52), відсортовані за sequence — колонки таблиці квот.
    funding_resource_options: List[Dict[str, str]] = []

    # Стан діалогу квоти
    q_open: bool = False
    q_index: int = -1
    q_speciality_combined: str = ""  # "code|id_department"
    q_id_entry_base: int = 0
    q_id_form_of_study: int = 0
    # Кількість місць по ресурсах фінансування, ключ — str(id_source_of_funding) (DK-52)
    q_funding_places: Dict[str, int] = {}

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def start_date(self) -> str:
        return self.item.start_date if self.item is not None and self.item.start_date is not None else ""

    @rx.event
    def set_start_date(self, value: str):
        self.item.start_date = value

    @rx.var
    def end_date(self) -> str:
        return self.item.end_date if self.item is not None and self.item.end_date is not None else ""

    @rx.event
    def set_end_date(self, value: str):
        self.item.end_date = value

    @rx.var
    def speciality_labels(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.speciality_options}

    @rx.var
    def entry_base_labels(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.entry_base_options}

    @rx.var
    def form_labels(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.form_of_study_options}

    def _load_speciality_options(self):
        sp = SpecialityService().get_list_items()
        self.speciality_options = [
            {"value": str(s.id), "label": f"{s.code} {s.title} ({s.tag})"}
            for s in sp
        ]
        self.entry_base_options = [
            {"value": str(b.id), "label": b.title} for b in EntryBaseService().get_list_items()
        ]
        self.form_of_study_options = [
            {"value": str(f.id), "label": f.title} for f in FormOfStudyService().get_list_items()
        ]
        self.funding_resource_options = [
            {"value": str(r.id), "label": r.title}
            for r in SourceOfFundingService().get_list_items()
        ]

    def _validate(self) -> Optional[str]:
        if not self.item.title or not self.item.title.strip():
            return "Поле назви обов'язкове!"
        if not self.item.start_date:
            return "Вкажіть дату початку!"
        if not self.item.end_date:
            return "Вкажіть дату закінчення!"
        if self.item.end_date < self.item.start_date:
            return "Дата закінчення не може бути раніше дати початку!"
        return None

    # ---- Quota dialog handlers ----

    def _reset_q_dialog(self):
        self.q_index = -1
        self.q_speciality_combined = ""
        self.q_id_entry_base = 0
        self.q_id_form_of_study = 0
        self.q_funding_places = {opt["value"]: 0 for opt in self.funding_resource_options}

    @rx.event
    def open_q_add(self):
        self._reset_q_dialog()
        self.q_open = True

    @rx.event
    def open_q_edit(self, index: int):
        if index < 0 or index >= len(self.quotas):
            return
        item = self.quotas[index]
        self.q_index = index
        self.q_speciality_combined = str(item.id_speciality) if item.id_speciality else ""
        self.q_id_entry_base = item.id_entry_base or 0
        self.q_id_form_of_study = item.id_form_of_study or 0
        self.q_funding_places = {
            opt["value"]: item.funding.get(opt["value"], 0) for opt in self.funding_resource_options
        }
        self.q_open = True

    @rx.event
    def close_q(self):
        self.q_open = False
        self._reset_q_dialog()

    @rx.event
    def set_q_open(self, value: bool):
        self.q_open = value
        if not value:
            self._reset_q_dialog()

    @rx.event
    def set_q_speciality_combined(self, value: str):
        self.q_speciality_combined = value

    @rx.var
    def q_id_entry_base_str(self) -> str:
        return str(self.q_id_entry_base) if self.q_id_entry_base else ""

    @rx.event
    def set_q_id_entry_base(self, value: str):
        try:
            self.q_id_entry_base = int(value) if value else 0
        except (ValueError, TypeError):
            self.q_id_entry_base = 0

    @rx.var
    def q_id_form_of_study_str(self) -> str:
        return str(self.q_id_form_of_study) if self.q_id_form_of_study else ""

    @rx.event
    def set_q_id_form_of_study(self, value: str):
        try:
            self.q_id_form_of_study = int(value) if value else 0
        except (ValueError, TypeError):
            self.q_id_form_of_study = 0

    @rx.event
    def set_q_funding_place(self, id_source_of_funding: str, value: str):
        try:
            places = int(value) if value else 0
        except (ValueError, TypeError):
            places = 0
        new_map = dict(self.q_funding_places)
        new_map[id_source_of_funding] = places
        self.q_funding_places = new_map

    @rx.var
    def q_total_places(self) -> int:
        return sum(self.q_funding_places.values())

    @rx.event
    def save_q(self):
        if not self.q_speciality_combined:
            yield rx.toast.warning("Оберіть спеціальність!")
            return
        try:
            id_speciality = int(self.q_speciality_combined)
        except (ValueError, TypeError):
            yield rx.toast.warning("Некоректна спеціальність!")
            return
        if not self.q_id_entry_base:
            yield rx.toast.warning("Оберіть базу вступу!")
            return
        if not self.q_id_form_of_study:
            yield rx.toast.warning("Оберіть форму навчання!")
            return
        if any(places < 0 for places in self.q_funding_places.values()):
            yield rx.toast.warning("Кількість місць не може бути від'ємною!")
            return

        # Заборона дублікатів у межах однієї кампанії: ключ — спеціальність + база + форма
        for i, q in enumerate(self.quotas):
            if (
                q.id_speciality == id_speciality
                and q.id_entry_base == self.q_id_entry_base
                and q.id_form_of_study == self.q_id_form_of_study
                and i != self.q_index
            ):
                yield rx.toast.warning("Квота з такою спеціальністю, базою та формою вже додана!")
                return

        funding = dict(self.q_funding_places)
        item = QuotaDraft(
            id_speciality=id_speciality,
            id_entry_base=self.q_id_entry_base,
            id_form_of_study=self.q_id_form_of_study,
            funding=funding,
            total_places=sum(funding.values()),
        )
        if 0 <= self.q_index < len(self.quotas):
            self.quotas[self.q_index] = item
        else:
            self.quotas.append(item)
        self.q_open = False
        self._reset_q_dialog()

    @rx.event
    def delete_q(self, index: int):
        if 0 <= index < len(self.quotas):
            del self.quotas[index]


class AddAdmissionCampaignState(_CampaignFormBase):
    in_process: bool = True

    def _reload_item(self):
        self.item = AdmissionCampaignModel()
        self.quotas = []

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            self._load_speciality_options()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        err = self._validate()
        if err:
            yield rx.toast.warning(err)
            return

        service = AdmissionCampaignService()
        try:
            self.item = service.add_one(self.item, actor_id=self._actor_id())
            if len(self.quotas) > 0:
                AdmissionCampaignSpecialityService().replace_all_for_campaign(
                    self.item.id, list(self.quotas)
                )
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ADMISSION_CAMPAIGN_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ADMISSION_CAMPAIGN_LIST)


class EditAdmissionCampaignState(_CampaignFormBase):
    in_process: bool = True

    def _reload_item(self):
        service = AdmissionCampaignService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    def _reload_quotas(self):
        if self.item is None or self.item.id is None:
            self.quotas = []
            return
        existing = AdmissionCampaignSpecialityService().get_by_campaign(self.item.id)
        resource_ids = [opt["value"] for opt in self.funding_resource_options]
        drafts = []
        for q in existing:
            funding = {rid: 0 for rid in resource_ids}
            funding.update({str(f.id_source_of_funding): f.places for f in (q.funding or [])})
            drafts.append(
                QuotaDraft(
                    id_speciality=q.id_speciality,
                    id_entry_base=q.id_entry_base,
                    id_form_of_study=q.id_form_of_study,
                    funding=funding,
                    total_places=sum(funding.values()),
                )
            )
        self.quotas = drafts

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ADMISSION_CAMPAIGN_LIST)
                return
            self._load_speciality_options()
            self._reload_quotas()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        err = self._validate()
        if err:
            yield rx.toast.warning(err)
            return

        service = AdmissionCampaignService()
        try:
            self.item = service.edit_one(self.item, actor_id=self._actor_id())
            AdmissionCampaignSpecialityService().replace_all_for_campaign(
                self.item.id, list(self.quotas)
            )
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ADMISSION_CAMPAIGN_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ADMISSION_CAMPAIGN_VIEW + str(self.item.id))


class ViewAdmissionCampaignState(AppState):
    item: AdmissionCampaignModel = AdmissionCampaignModel()
    quotas: List[QuotaView] = []
    # Активні ресурси фінансування (DK-52) — колонки таблиці квот.
    funding_resource_options: List[Dict[str, str]] = []
    in_process: bool = True

    def _reload_item(self):
        service = AdmissionCampaignService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    def _reload_quotas(self):
        self.funding_resource_options = [
            {"value": str(r.id), "label": r.title}
            for r in SourceOfFundingService().get_list_items()
        ]
        if self.item is None or self.item.id is None:
            self.quotas = []
            return
        existing = AdmissionCampaignSpecialityService().get_by_campaign(self.item.id)
        resource_ids = [opt["value"] for opt in self.funding_resource_options]
        views = []
        for q in existing:
            # Всі активні ресурси мають ключ (навіть 0), щоб рядок Var-lookup у
            # view не впав на ресурсі, доданому вже після збереження квоти (DK-52).
            funding_map = {rid: 0 for rid in resource_ids}
            funding_map.update({str(f.id_source_of_funding): f.places for f in (q.funding or [])})
            speciality_label = (
                f"{q.speciality.code} {q.speciality.title} ({q.speciality.tag})"
                if q.speciality is not None
                else str(q.id_speciality)
            )
            views.append(
                QuotaView(
                    id_speciality=q.id_speciality,
                    speciality_label=speciality_label,
                    entry_base_label=q.entry_base.title if q.entry_base is not None else "",
                    form_of_study_label=q.form_of_study.title if q.form_of_study is not None else "",
                    funding_map=funding_map,
                    total_places=sum(funding_map.values()),
                )
            )
        self.quotas = views

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.DASHBOARD)
            else:
                self._reload_quotas()
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ADMISSION_CAMPAIGN_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ADMISSION_CAMPAIGN_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = AdmissionCampaignService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(routes.ADMISSION_CAMPAIGN_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.var
    def start_date(self) -> str:
        return self.item.start_date if self.item is not None and self.item.start_date is not None else ""

    @rx.var
    def end_date(self) -> str:
        return self.item.end_date if self.item is not None and self.item.end_date is not None else ""
