import reflex as rx

from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import (
    AdmissionCampaignModel,
    AdmissionCampaignSpecialityModel,
)
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.admission_campaign_speciality import AdmissionCampaignSpecialityService
from Dekanat.services.speciality import SpecialityService
from Dekanat.services.entry_base import EntryBaseService
from Dekanat.services.form_of_study import FormOfStudyService


def _quota_key(code: str, id_department: int) -> str:
    return f"{code}|{id_department}"


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
    quotas: List[AdmissionCampaignSpecialityModel] = []

    # Довідник для select'а спеціальностей та лейблів у таблиці квот
    speciality_options: List[Dict[str, str]] = []
    # Довідники бази вступу та форми навчання (DK-26)
    entry_base_options: List[Dict[str, str]] = []
    form_of_study_options: List[Dict[str, str]] = []

    # Стан діалогу квоти
    q_open: bool = False
    q_index: int = -1
    q_speciality_combined: str = ""  # "code|id_department"
    q_id_entry_base: int = 0
    q_id_form_of_study: int = 0
    q_budget_places: int = 0
    q_contract_places: int = 0

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
            {"value": _quota_key(s.code, s.id_department), "label": f"{s.code} {s.title}"}
            for s in sp
        ]
        self.entry_base_options = [
            {"value": str(b.id), "label": b.title} for b in EntryBaseService().get_list_items()
        ]
        self.form_of_study_options = [
            {"value": str(f.id), "label": f.title} for f in FormOfStudyService().get_list_items()
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
        self.q_budget_places = 0
        self.q_contract_places = 0

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
        self.q_speciality_combined = _quota_key(item.id_speciality_code, item.id_speciality_department)
        self.q_id_entry_base = item.id_entry_base or 0
        self.q_id_form_of_study = item.id_form_of_study or 0
        self.q_budget_places = item.budget_places or 0
        self.q_contract_places = item.contract_places or 0
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
    def set_q_budget_places(self, value: str):
        try:
            self.q_budget_places = int(value) if value else 0
        except (ValueError, TypeError):
            self.q_budget_places = 0

    @rx.event
    def set_q_contract_places(self, value: str):
        try:
            self.q_contract_places = int(value) if value else 0
        except (ValueError, TypeError):
            self.q_contract_places = 0

    @rx.event
    def save_q(self):
        if not self.q_speciality_combined:
            yield rx.toast.warning("Оберіть спеціальність!")
            return
        try:
            code, dept = self.q_speciality_combined.split("|", 1)
            id_speciality_code = code
            id_speciality_department = int(dept)
        except Exception:
            yield rx.toast.warning("Некоректна спеціальність!")
            return
        if not self.q_id_entry_base:
            yield rx.toast.warning("Оберіть базу вступу!")
            return
        if not self.q_id_form_of_study:
            yield rx.toast.warning("Оберіть форму навчання!")
            return
        if self.q_budget_places < 0 or self.q_contract_places < 0:
            yield rx.toast.warning("Кількість місць не може бути від'ємною!")
            return

        # Заборона дублікатів у межах однієї кампанії: ключ — спеціальність + база + форма
        for i, q in enumerate(self.quotas):
            if (
                q.id_speciality_code == id_speciality_code
                and q.id_speciality_department == id_speciality_department
                and q.id_entry_base == self.q_id_entry_base
                and q.id_form_of_study == self.q_id_form_of_study
                and i != self.q_index
            ):
                yield rx.toast.warning("Квота з такою спеціальністю, базою та формою вже додана!")
                return

        item = AdmissionCampaignSpecialityModel(
            id_admission_campaign=self.item.id if self.item is not None and self.item.id is not None else 0,
            id_speciality_code=id_speciality_code,
            id_speciality_department=id_speciality_department,
            id_entry_base=self.q_id_entry_base,
            id_form_of_study=self.q_id_form_of_study,
            budget_places=self.q_budget_places,
            contract_places=self.q_contract_places,
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
            self.item = service.add_one(self.item)
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
        self.quotas = [
            AdmissionCampaignSpecialityModel(
                id_admission_campaign=q.id_admission_campaign,
                id_speciality_code=q.id_speciality_code,
                id_speciality_department=q.id_speciality_department,
                id_entry_base=q.id_entry_base,
                id_form_of_study=q.id_form_of_study,
                budget_places=q.budget_places,
                contract_places=q.contract_places,
            )
            for q in existing
        ]

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
            self.item = service.edit_one(self.item)
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
    quotas: Sequence[AdmissionCampaignSpecialityModel] = []
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
        self.quotas = AdmissionCampaignSpecialityService().get_by_campaign(self.item.id)

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
        if service.delete_one(self.item):
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
