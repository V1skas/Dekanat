import reflex as rx

from typing import Sequence, Optional, List, Dict
from datetime import date, datetime

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import (
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    IdentityDocumentModel,
    DocumentAboutEducationModel,
    MilitaryAccountingModel,
    MedicalReferenceModel,
    InformationAboutRelativesModel,
    SpecialConditionPersonModel,
    ResultZnoModel,
)
from Dekanat.services.entrant import EntrantService, photo_to_data_url
from Dekanat.services.source_of_funding import SourceOfFundingService
from Dekanat.services.entry_base import EntryBaseService
from Dekanat.services.form_of_study import FormOfStudyService
from Dekanat.services.application_status import ApplicationStatusService
from Dekanat.services.entrants_group import EntrantsGroupService
from Dekanat.services.speciality import SpecialityService
from Dekanat.services.identity_document_type import IdentityDocumentTypeService
from Dekanat.services.kinship import KinshipService
from Dekanat.services.special_condition import SpecialConditionService
from Dekanat.services.item_zno import ItemZnoService
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.admission_campaign_speciality import AdmissionCampaignSpecialityService
from Dekanat.models import AdmissionCampaignModel


# ---------- List page ----------

class ListEntrantState(AppState):
    items: Optional[Sequence[EntrantModel]] = None
    in_progress: bool = True

    # Стан панелі фільтрів
    filter_open: bool = False
    filter_pib: str = ""
    filter_status_id: int = 0
    filter_entry_base_id: int = 0
    filter_campaign_id: int = 0  # 0 — без фільтра по кампанії
    # "code|id_department"; "__all__" — без фільтра (Radix забороняє value="" в rx.select.item).
    filter_speciality_key: str = "__all__"
    application_status_options: List[Dict[str, str]] = []
    entry_base_options: List[Dict[str, str]] = []
    # Опции спеціальностей — обмежені квотами активної кампанії (як у формі абітурієнта).
    speciality_options: List[Dict[str, str]] = []
    campaigns: List[AdmissionCampaignModel] = []

    # Сортування. sort_field == "" — за замовчуванням (created_at desc).
    sort_field: str = ""
    sort_dir: str = "asc"  # "asc" | "desc"

    def _campaign_range(self):
        if not self.filter_campaign_id:
            return None
        campaign = next((c for c in self.campaigns if c.id == self.filter_campaign_id), None)
        if campaign is None:
            return None
        try:
            start_dt = datetime.strptime(campaign.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(campaign.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            return (start_dt, end_dt)
        except (ValueError, TypeError):
            return None

    def _parse_speciality_key(self):
        if not self.filter_speciality_key or self.filter_speciality_key == "__all__":
            return (None, None)
        try:
            code, dept = self.filter_speciality_key.split("|", 1)
            return (code, int(dept))
        except (ValueError, TypeError):
            return (None, None)

    def _reload_items(self):
        service = EntrantService()
        spec_code, spec_dept = self._parse_speciality_key()
        self.items = service.get_list_items(
            pib=self.filter_pib.strip() or None,
            status_id=self.filter_status_id or None,
            entry_base_id=self.filter_entry_base_id or None,
            created_between=self._campaign_range(),
            priority_speciality_code=spec_code,
            priority_speciality_department=spec_dept,
            sort_field=self.sort_field or None,
            sort_dir=self.sort_dir,
        )

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            self.application_status_options = [
                {"value": str(s.id), "label": s.title}
                for s in ApplicationStatusService().get_list_items()
            ]
            self.entry_base_options = [
                {"value": str(b.id), "label": b.title}
                for b in EntryBaseService().get_list_items()
            ]
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            active = campaign_service.get_active_campaign()
            self.filter_campaign_id = active.id if active is not None else 0
            self._reload_speciality_options()
            self._reload_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ENTRANT_ADD)

    # --- filter panel ---

    @rx.event
    def toggle_filter(self):
        self.filter_open = not self.filter_open

    @rx.event
    def set_filter_pib(self, value: str):
        self.filter_pib = value
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def filter_status_id_str(self) -> str:
        return str(self.filter_status_id) if self.filter_status_id else ""

    @rx.event
    def set_filter_status_id(self, value: str):
        try:
            self.filter_status_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.filter_status_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def filter_entry_base_id_str(self) -> str:
        return str(self.filter_entry_base_id) if self.filter_entry_base_id else ""

    @rx.event
    def set_filter_entry_base_id(self, value: str):
        try:
            self.filter_entry_base_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.filter_entry_base_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(c.id), "label": c.title} for c in self.campaigns)
        return opts

    @rx.var
    def filter_campaign_id_str(self) -> str:
        return str(self.filter_campaign_id) if self.filter_campaign_id else "0"

    @rx.event
    def set_filter_campaign_id(self, value: str):
        try:
            self.filter_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.filter_campaign_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def clear_filters(self):
        self.filter_pib = ""
        self.filter_status_id = 0
        self.filter_entry_base_id = 0
        self.filter_campaign_id = 0
        self.filter_speciality_key = "__all__"
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- speciality filter ---

    def _reload_speciality_options(self):
        """Опції спеціальностей беремо з квот активної кампанії; якщо нема —
        повний довідник, щоб фільтр все одно мав сенс у поза-кампанійному режимі.
        Перший пункт — sentinel '__all__' (Radix забороняє value='')."""
        opts: List[Dict[str, str]] = [{"value": "__all__", "label": "— Будь-яка —"}]
        active = AdmissionCampaignService().get_active_campaign()
        if active is not None and active.id is not None:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(active.id)
            seen_keys: set = set()
            for q in quotas:
                if q.speciality is None:
                    continue
                key = f"{q.id_speciality_code}|{q.id_speciality_department}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                opts.append({
                    "value": key,
                    "label": f"{q.speciality.code} {q.speciality.title}",
                })
        if len(opts) == 1:
            for s in SpecialityService().get_list_items():
                opts.append({
                    "value": f"{s.code}|{s.id_department}",
                    "label": f"{s.code} {s.title}",
                })
        self.speciality_options = opts

    @rx.event
    def set_filter_speciality_key(self, value: str):
        self.filter_speciality_key = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- sorting ---

    @rx.event
    def on_click_sort(self, field: str):
        """Клік по заголовку столбця: якщо вже активне сортування цього поля —
        тогглим напрямок; інакше — ставимо поле і починаємо з asc."""
        if self.sort_field == field:
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"
        else:
            self.sort_field = field
            self.sort_dir = "asc"
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def sort_indicator(self) -> Dict[str, str]:
        """Для кожного поля повертає " ↑" / " ↓" / "" — рендериться поруч із назвою колонки."""
        arrow = " ↑" if self.sort_dir == "asc" else " ↓"
        return {
            "pib": arrow if self.sort_field == "pib" else "",
            "phone_number": arrow if self.sort_field == "phone_number" else "",
            "email": arrow if self.sort_field == "email" else "",
            "entry_base": arrow if self.sort_field == "entry_base" else "",
            "source_of_funding": arrow if self.sort_field == "source_of_funding" else "",
            "speciality": arrow if self.sort_field == "speciality" else "",
            "application_status": arrow if self.sort_field == "application_status" else "",
        }


# ---------- View page ----------

class ViewEntrantState(AppState):
    item: Optional[EntrantModel] = None
    in_process: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            service = EntrantService()
            self.item = service.get_by_id(int(self._route_param("id", "-1")))
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANT_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ENTRANT_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        if self.item is None:
            return None
        return rx.redirect(routes.ENTRANT_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRANT_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return
        if self.item is None:
            return

        service = EntrantService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ENTRANT_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")

    @rx.var
    def photo_data_url(self) -> str:
        if self.item is None or self.item.person is None:
            return ""
        return photo_to_data_url(self.item.person.photo, self.item.person.photo_mime_type)

    @rx.var
    def has_photo(self) -> bool:
        return bool(self.photo_data_url)

    @rx.var
    def photo_download_name(self) -> str:
        """Назва файлу для завантаження фото: ПІБ із підкресленнями + розширення з mime."""
        if self.item is None or self.item.person is None or not self.item.person.pib:
            return "photo"
        name = "_".join(self.item.person.pib.strip().split())
        mime = (self.item.person.photo_mime_type or "").lower()
        if "png" in mime:
            ext = "png"
        elif "webp" in mime:
            ext = "webp"
        else:
            ext = "jpg"
        return f"{name}.{ext}"

    @staticmethod
    def _fmt_dt(value) -> str:
        if value is None:
            return "—"
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except AttributeError:
            return str(value)

    @rx.var
    def person_created_at_display(self) -> str:
        if self.item is None or self.item.person is None:
            return "—"
        return self._fmt_dt(self.item.person.created_at)

    @rx.var
    def entrant_created_at_display(self) -> str:
        if self.item is None:
            return "—"
        return self._fmt_dt(self.item.created_at)

    @rx.var
    def status_changed_at_display(self) -> str:
        if self.item is None:
            return "—"
        return self._fmt_dt(self.item.application_status_changed_at)


# ---------- Add / Edit (shared form state) ----------

CITIZENSHIP_OPTIONS = ["Україна", "Інше"]
SEX_OPTIONS = ["Чоловіча", "Жіноча"]


class EntrantFormState(AppState):
    """Combined form state for both /add and /edit/{id} entrant pages."""

    # ---- Mode / loading ----
    mode: str = "add"  # "add" | "edit"
    entrant_id: int = -1
    in_process: bool = True

    # ---- Photo (kept as separate bytes/mime; persisted into PersonModel on save) ----
    photo_bytes: Optional[bytes] = None
    photo_mime: Optional[str] = None

    # ---- Person fields (flat for easy form binding) ----
    edbo: str = ""
    pib: str = ""
    citizenship: str = "Україна"
    sex: str = ""
    date_of_birth: str = ""
    place_of_registration_city: str = ""
    place_of_registration: str = ""
    mokpp: str = ""
    email: str = ""
    phone_number: str = ""
    the_need_for_a_dormitory: bool = False
    id_source_of_funding: int = 0
    id_entry_base: int = 0

    # ---- Entrant fields ----
    id_application_status: int = 0
    id_entrant_group: int = 0  # 0 means "not assigned"
    comment: str = ""

    # ---- Dropdown options ----
    source_of_funding_options: List[Dict[str, str]] = []
    entry_base_options: List[Dict[str, str]] = []
    application_status_options: List[Dict[str, str]] = []
    entrant_group_options: List[Dict[str, str]] = []
    # campaign_quota_rows — рядки квот активної кампанії: spec_key|base_id|form_id.
    # На їх основі обчислюються speciality_options (фільтр за базою вступу абітурієнта)
    # та sp_form_options (форми, доступні для обраної спеціальності+бази) — DK-26.
    campaign_quota_rows: List[Dict[str, str]] = []
    # form_of_study_options — повний довідник форм навчання (для лейблів у таблиці).
    form_of_study_options: List[Dict[str, str]] = []
    # all_speciality_options — повний довідник спеціальностей; використовується для
    # відображення назв у таблиці вже збережених пріоритетів абітурієнта (у т.ч. тих,
    # що могли бути додані в минулих кампаніях і вже не входять до активної).
    all_speciality_options: List[Dict[str, str]] = []
    identity_document_type_options: List[Dict[str, str]] = []
    kinship_options: List[Dict[str, str]] = []
    special_condition_options: List[Dict[str, str]] = []
    item_zno_options: List[Dict[str, str]] = []

    # ---- Child collections ----
    identity_documents: List[IdentityDocumentModel] = []
    documents_about_education: List[DocumentAboutEducationModel] = []
    military_accountings: List[MilitaryAccountingModel] = []
    medical_references: List[MedicalReferenceModel] = []
    information_about_relatives: List[InformationAboutRelativesModel] = []
    special_conditions_person: List[SpecialConditionPersonModel] = []
    specialties: List[SpecialtieEntrantModel] = []
    results_zno: List[ResultZnoModel] = []

    # ---- Identity document dialog ----
    iddoc_open: bool = False
    iddoc_index: int = -1
    iddoc_id_type: int = 0
    iddoc_number: str = ""
    iddoc_series: str = ""
    iddoc_code: str = ""
    iddoc_issued_by: str = ""
    iddoc_date_of_issue: str = ""

    # ---- Document about education dialog ----
    docedu_open: bool = False
    docedu_index: int = -1
    docedu_title: str = ""
    docedu_number: str = ""
    docedu_series: str = ""
    docedu_issued_by: str = ""
    docedu_date_of_issue: str = ""

    # ---- Military accounting dialog ----
    mil_open: bool = False
    mil_index: int = -1
    mil_number: str = ""
    mil_series: str = ""
    mil_issued_by: str = ""
    mil_date_of_issue: str = ""

    # ---- Medical reference dialog ----
    med_open: bool = False
    med_index: int = -1
    med_number: str = ""
    med_date_of_issue: str = ""

    # ---- Relatives dialog ----
    rel_open: bool = False
    rel_index: int = -1
    rel_id_kinship: int = 0
    rel_pib: str = ""
    rel_phone_number: str = ""

    # ---- Special condition dialog ----
    scp_open: bool = False
    scp_index: int = -1
    scp_id_special_condition: str = ""
    scp_title: str = ""
    scp_number: str = ""
    scp_description: str = ""
    scp_date_of_issue: str = ""

    # ---- Specialty (priority list) dialog ----
    sp_open: bool = False
    sp_index: int = -1
    sp_combined: str = ""  # "code|id_department"
    sp_id_form_of_study: int = 0
    sp_priority: int = 1

    # ---- ZNO result dialog ----
    rz_open: bool = False
    rz_index: int = -1
    rz_id_items_zno: int = 0
    rz_points: int = 0

    # ============================================================
    # On-load: shared dropdown init + branch on mode
    # ============================================================

    def _load_dropdowns(self):
        sof = SourceOfFundingService().get_list_items()
        self.source_of_funding_options = [{"value": str(s.id), "label": s.title} for s in sof]
        eb = EntryBaseService().get_list_items()
        self.entry_base_options = [{"value": str(e.id), "label": e.title} for e in eb]
        ast = ApplicationStatusService().get_list_items()
        self.application_status_options = [{"value": str(a.id), "label": a.title} for a in ast]
        eg = EntrantsGroupService().get_list_items()
        self.entrant_group_options = [{"value": str(g.id), "label": g.title} for g in eg]
        sp = SpecialityService().get_list_items()
        sp_by_key: Dict[str, str] = {
            f"{s.code}|{s.id_department}": f"{s.code} {s.title}" for s in sp
        }
        self.all_speciality_options = [
            {"value": k, "label": v} for k, v in sp_by_key.items()
        ]
        # Форми навчання — повний довідник (для лейблів і select'ів).
        self.form_of_study_options = [
            {"value": str(f.id), "label": f.title} for f in FormOfStudyService().get_list_items()
        ]
        # Квоти активної кампанії — основа фільтрації спеціальностей за базою вступу
        # та підбору форм навчання для обраної спеціальності (DK-26).
        active_campaign = AdmissionCampaignService().get_active_campaign()
        rows: List[Dict[str, str]] = []
        if active_campaign is not None and active_campaign.id is not None:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(active_campaign.id)
            for q in quotas:
                rows.append({
                    "spec_key": f"{q.id_speciality_code}|{q.id_speciality_department}",
                    "base_id": str(q.id_entry_base),
                    "form_id": str(q.id_form_of_study),
                })
        self.campaign_quota_rows = rows
        idt = IdentityDocumentTypeService().get_list_items()
        self.identity_document_type_options = [{"value": str(t.id), "label": t.title} for t in idt]
        ks = KinshipService().get_list_items()
        self.kinship_options = [{"value": str(k.id), "label": k.title} for k in ks]
        sc = SpecialConditionService().get_list_items()
        self.special_condition_options = [{"value": s.subcategory_code, "label": s.title} for s in sc]
        iz = ItemZnoService().get_list_items()
        self.item_zno_options = [{"value": str(i.id), "label": i.title} for i in iz]

    def _reset_form(self):
        self.entrant_id = -1
        self.photo_bytes = None
        self.photo_mime = None
        self.edbo = ""
        self.pib = ""
        self.citizenship = "Україна"
        self.sex = ""
        self.date_of_birth = ""
        self.place_of_registration_city = ""
        self.place_of_registration = ""
        self.mokpp = ""
        self.email = ""
        self.phone_number = ""
        self.the_need_for_a_dormitory = False
        self.id_source_of_funding = 0
        self.id_entry_base = 0
        self.id_application_status = 0
        self.id_entrant_group = 0
        self.comment = ""
        self.identity_documents = []
        self.documents_about_education = []
        self.military_accountings = []
        self.medical_references = []
        self.information_about_relatives = []
        self.special_conditions_person = []
        self.specialties = []
        self.results_zno = []

    @rx.event
    def on_load_add(self):
        if not self.has_permission(Actions.ENTRANT_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.mode = "add"
        self.in_process = True
        try:
            self._reset_form()
            self._load_dropdowns()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")

    @rx.event
    def on_load_edit(self):
        if not self.has_permission(Actions.ENTRANT_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.mode = "edit"
        self.in_process = True
        try:
            self._reset_form()
            self._load_dropdowns()

            id_param = int(self._route_param("id", "-1"))
            entrant = EntrantService().get_by_id(id_param)
            if entrant is None or entrant.person is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANT_LIST)
                return

            person = entrant.person
            self.entrant_id = entrant.id
            self.photo_bytes = person.photo
            self.photo_mime = person.photo_mime_type
            self.edbo = person.edbo or ""
            self.pib = person.pib or ""
            self.citizenship = person.citizenship or "Україна"
            self.sex = person.sex or ""
            self.date_of_birth = person.date_of_birth or ""
            self.place_of_registration_city = person.place_of_registration_city or ""
            self.place_of_registration = person.place_of_registration or ""
            self.mokpp = person.mokpp or ""
            self.email = person.email or ""
            self.phone_number = person.phone_number or ""
            self.the_need_for_a_dormitory = bool(person.the_need_for_a_dormitory)
            self.id_source_of_funding = person.id_source_of_funding or 0
            self.id_entry_base = person.id_entry_base or 0
            self.id_application_status = entrant.id_application_status or 0
            self.id_entrant_group = entrant.id_entrant_group or 0
            self.comment = entrant.comment or ""

            self.identity_documents = list(person.identity_document or [])
            self.documents_about_education = list(person.document_about_education or [])
            self.military_accountings = list(person.military_accounting or [])
            self.medical_references = list(person.medical_reference or [])
            self.information_about_relatives = list(person.information_about_relatives or [])
            self.special_conditions_person = list(person.special_conditions or [])
            self.specialties = list(entrant.specialties or [])
            self.results_zno = list(person.results_zno or [])

            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")

    # ============================================================
    # Field setters for radio / select dropdowns that need str <-> int
    # ============================================================

    @rx.var
    def id_source_of_funding_str(self) -> str:
        return str(self.id_source_of_funding) if self.id_source_of_funding else ""

    @rx.event
    def set_id_source_of_funding(self, value: str):
        try:
            self.id_source_of_funding = int(value) if value else 0
        except (ValueError, TypeError):
            self.id_source_of_funding = 0

    @rx.var
    def id_entry_base_str(self) -> str:
        return str(self.id_entry_base) if self.id_entry_base else ""

    @rx.event
    def set_id_entry_base(self, value: str):
        try:
            self.id_entry_base = int(value) if value else 0
        except (ValueError, TypeError):
            self.id_entry_base = 0
        # Зміна бази вступу може зробити обрану спеціальність/форму недоступною — скидаємо
        # незбережений вибір у діалозі пріоритету (DK-26).
        self.sp_combined = ""
        self.sp_id_form_of_study = 0

    @rx.var
    def id_application_status_str(self) -> str:
        return str(self.id_application_status) if self.id_application_status else ""

    @rx.event
    def set_id_application_status(self, value: str):
        try:
            self.id_application_status = int(value) if value else 0
        except (ValueError, TypeError):
            self.id_application_status = 0

    @rx.var
    def id_entrant_group_str(self) -> str:
        return str(self.id_entrant_group) if self.id_entrant_group else ""

    @rx.event
    def set_id_entrant_group(self, value: str):
        try:
            self.id_entrant_group = int(value) if value else 0
        except (ValueError, TypeError):
            self.id_entrant_group = 0

    # ============================================================
    # Прості сетери для базових текстових полів форми.
    # Reflex 0.8.9+ депрекейтить state_auto_setters; нижче — явні
    # сетери для всіх полів, що використовуються через `set_X` у view.
    # ============================================================

    @rx.event
    def set_edbo(self, value: str):
        self.edbo = value

    @rx.event
    def set_pib(self, value: str):
        self.pib = value

    @rx.event
    def set_sex(self, value: str):
        self.sex = value

    @rx.event
    def set_email(self, value: str):
        self.email = value

    @rx.event
    def set_mokpp(self, value: str):
        self.mokpp = value

    @rx.event
    def set_comment(self, value: str):
        self.comment = value

    @rx.event
    def set_citizenship(self, value: str):
        self.citizenship = value

    @rx.event
    def set_date_of_birth(self, value: str):
        self.date_of_birth = value

    @rx.event
    def set_place_of_registration_city(self, value: str):
        self.place_of_registration_city = value

    @rx.event
    def set_place_of_registration(self, value: str):
        self.place_of_registration = value

    @rx.event
    def set_phone_number(self, value: str):
        self.phone_number = value

    @rx.event
    def set_the_need_for_a_dormitory(self, value: bool):
        self.the_need_for_a_dormitory = value

    # ---- iddoc dialog ----
    @rx.event
    def set_iddoc_number(self, value: str):
        self.iddoc_number = value

    @rx.event
    def set_iddoc_series(self, value: str):
        self.iddoc_series = value

    @rx.event
    def set_iddoc_code(self, value: str):
        self.iddoc_code = value

    @rx.event
    def set_iddoc_issued_by(self, value: str):
        self.iddoc_issued_by = value

    @rx.event
    def set_iddoc_date_of_issue(self, value: str):
        self.iddoc_date_of_issue = value

    @rx.event
    def set_iddoc_open(self, value: bool):
        self.iddoc_open = value

    # ---- docedu dialog ----
    @rx.event
    def set_docedu_title(self, value: str):
        self.docedu_title = value

    @rx.event
    def set_docedu_number(self, value: str):
        self.docedu_number = value

    @rx.event
    def set_docedu_series(self, value: str):
        self.docedu_series = value

    @rx.event
    def set_docedu_issued_by(self, value: str):
        self.docedu_issued_by = value

    @rx.event
    def set_docedu_date_of_issue(self, value: str):
        self.docedu_date_of_issue = value

    @rx.event
    def set_docedu_open(self, value: bool):
        self.docedu_open = value

    # ---- mil dialog ----
    @rx.event
    def set_mil_number(self, value: str):
        self.mil_number = value

    @rx.event
    def set_mil_series(self, value: str):
        self.mil_series = value

    @rx.event
    def set_mil_issued_by(self, value: str):
        self.mil_issued_by = value

    @rx.event
    def set_mil_date_of_issue(self, value: str):
        self.mil_date_of_issue = value

    @rx.event
    def set_mil_open(self, value: bool):
        self.mil_open = value

    # ---- med dialog ----
    @rx.event
    def set_med_number(self, value: str):
        self.med_number = value

    @rx.event
    def set_med_date_of_issue(self, value: str):
        self.med_date_of_issue = value

    @rx.event
    def set_med_open(self, value: bool):
        self.med_open = value

    # ---- rel dialog ----
    @rx.event
    def set_rel_pib(self, value: str):
        self.rel_pib = value

    @rx.event
    def set_rel_phone_number(self, value: str):
        self.rel_phone_number = value

    @rx.event
    def set_rel_open(self, value: bool):
        self.rel_open = value

    # ---- scp dialog ----
    @rx.event
    def set_scp_title(self, value: str):
        self.scp_title = value

    @rx.event
    def set_scp_number(self, value: str):
        self.scp_number = value

    @rx.event
    def set_scp_description(self, value: str):
        self.scp_description = value

    @rx.event
    def set_scp_date_of_issue(self, value: str):
        self.scp_date_of_issue = value

    @rx.event
    def set_scp_open(self, value: bool):
        self.scp_open = value

    # ---- specialty / zno dialogs ----
    @rx.event
    def set_sp_open(self, value: bool):
        self.sp_open = value

    @rx.event
    def set_rz_open(self, value: bool):
        self.rz_open = value

    # ============================================================
    # Photo upload / clear
    # ============================================================

    @rx.event
    async def handle_photo_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        f = files[0]
        data = await f.read()
        self.photo_bytes = data
        self.photo_mime = f.content_type or "image/png"

    @rx.event
    def clear_photo(self):
        self.photo_bytes = None
        self.photo_mime = None

    @rx.var
    def photo_data_url(self) -> str:
        return photo_to_data_url(self.photo_bytes, self.photo_mime)

    @rx.var
    def has_photo(self) -> bool:
        return bool(self.photo_data_url)

    @rx.var
    def max_birth_date(self) -> str:
        return date.today().isoformat()

    # ============================================================
    # Display title lookup maps (used in form sub-tables)
    # ============================================================

    @rx.var
    def identity_document_type_titles(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.identity_document_type_options}

    @rx.var
    def kinship_titles(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.kinship_options}

    @rx.var
    def item_zno_titles(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.item_zno_options}

    @rx.var
    def special_condition_titles(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.special_condition_options}

    @rx.var
    def speciality_labels(self) -> Dict[str, str]:
        # Завжди повний довідник — щоб уже збережені пріоритети відображались навіть якщо
        # відповідна спеціальність більше не входить до квот поточної кампанії.
        return {opt["value"]: opt["label"] for opt in self.all_speciality_options}

    @rx.var
    def form_labels(self) -> Dict[str, str]:
        return {opt["value"]: opt["label"] for opt in self.form_of_study_options}

    @rx.var
    def sp_form_options(self) -> List[Dict[str, str]]:
        """Форми навчання, доступні для бази вступу абітурієнта (з квот активної
        кампанії). Обираються ПЕРШИМИ у діалозі. Поки база не обрана — порожньо (DK-26)."""
        if not self.id_entry_base:
            return []
        base = str(self.id_entry_base)
        form_map = {opt["value"]: opt["label"] for opt in self.form_of_study_options}
        seen: set = set()
        result: List[Dict[str, str]] = []
        for row in self.campaign_quota_rows:
            if row["base_id"] != base:
                continue
            fid = row["form_id"]
            if fid in seen:
                continue
            seen.add(fid)
            result.append({"value": fid, "label": form_map.get(fid, fid)})
        return result

    @rx.var
    def sp_speciality_options(self) -> List[Dict[str, str]]:
        """Спеціальності, доступні для (база вступу + обрана форма навчання). Поки
        форма не обрана — порожньо (поле спеціальності неактивне) — DK-26."""
        if not self.id_entry_base or not self.sp_id_form_of_study:
            return []
        base = str(self.id_entry_base)
        form = str(self.sp_id_form_of_study)
        label_map = {opt["value"]: opt["label"] for opt in self.all_speciality_options}
        seen: set = set()
        result: List[Dict[str, str]] = []
        for row in self.campaign_quota_rows:
            if row["base_id"] != base or row["form_id"] != form:
                continue
            key = row["spec_key"]
            if key in seen:
                continue
            seen.add(key)
            result.append({"value": key, "label": label_map.get(key, key)})
        return result

    # ============================================================
    # Identity document dialog
    # ============================================================

    def _reset_iddoc_dialog(self):
        self.iddoc_index = -1
        self.iddoc_id_type = 0
        self.iddoc_number = ""
        self.iddoc_series = ""
        self.iddoc_code = ""
        self.iddoc_issued_by = ""
        self.iddoc_date_of_issue = ""

    @rx.event
    def open_iddoc_add(self):
        self._reset_iddoc_dialog()
        self.iddoc_open = True

    @rx.event
    def open_iddoc_edit(self, index: int):
        if index < 0 or index >= len(self.identity_documents):
            return
        item = self.identity_documents[index]
        self.iddoc_index = index
        self.iddoc_id_type = item.id_type or 0
        self.iddoc_number = item.number or ""
        self.iddoc_series = item.series or ""
        self.iddoc_code = item.code or ""
        self.iddoc_issued_by = item.issued_by or ""
        self.iddoc_date_of_issue = item.date_of_issue or ""
        self.iddoc_open = True

    @rx.event
    def close_iddoc(self):
        self.iddoc_open = False
        self._reset_iddoc_dialog()

    @rx.var
    def iddoc_id_type_str(self) -> str:
        return str(self.iddoc_id_type) if self.iddoc_id_type else ""

    @rx.event
    def set_iddoc_id_type(self, value: str):
        try:
            self.iddoc_id_type = int(value) if value else 0
        except (ValueError, TypeError):
            self.iddoc_id_type = 0

    @rx.event
    def save_iddoc(self):
        if not self.iddoc_id_type:
            yield rx.toast.warning("Оберіть тип документа!")
            return
        if not self.iddoc_number:
            yield rx.toast.warning("Введіть номер!")
            return
        if not self.iddoc_issued_by:
            yield rx.toast.warning("Введіть, ким видано!")
            return
        if not self.iddoc_date_of_issue:
            yield rx.toast.warning("Введіть дату видачі!")
            return

        item = IdentityDocumentModel(
            number=self.iddoc_number.strip(),
            series=self.iddoc_series.strip() or None,  # type: ignore[arg-type]
            code=self.iddoc_code.strip() or None,  # type: ignore[arg-type]
            issued_by=self.iddoc_issued_by.strip(),
            date_of_issue=self.iddoc_date_of_issue,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
            id_type=self.iddoc_id_type,
        )

        if self.iddoc_index >= 0 and self.iddoc_index < len(self.identity_documents):
            self.identity_documents[self.iddoc_index] = item
        else:
            self.identity_documents.append(item)
        self.iddoc_open = False
        self._reset_iddoc_dialog()

    @rx.event
    def delete_iddoc(self, index: int):
        if 0 <= index < len(self.identity_documents):
            del self.identity_documents[index]

    # ============================================================
    # Document about education dialog
    # ============================================================

    def _reset_docedu_dialog(self):
        self.docedu_index = -1
        self.docedu_title = ""
        self.docedu_number = ""
        self.docedu_series = ""
        self.docedu_issued_by = ""
        self.docedu_date_of_issue = ""

    @rx.event
    def open_docedu_add(self):
        self._reset_docedu_dialog()
        self.docedu_open = True

    @rx.event
    def open_docedu_edit(self, index: int):
        if index < 0 or index >= len(self.documents_about_education):
            return
        item = self.documents_about_education[index]
        self.docedu_index = index
        self.docedu_title = item.title or ""
        self.docedu_number = item.number or ""
        self.docedu_series = item.series or ""
        self.docedu_issued_by = item.issued_by or ""
        self.docedu_date_of_issue = item.date_of_issue or ""
        self.docedu_open = True

    @rx.event
    def close_docedu(self):
        self.docedu_open = False
        self._reset_docedu_dialog()

    @rx.event
    def save_docedu(self):
        if not self.docedu_title:
            yield rx.toast.warning("Введіть назву документа!")
            return
        if not self.docedu_number:
            yield rx.toast.warning("Введіть номер!")
            return
        if not self.docedu_date_of_issue:
            yield rx.toast.warning("Введіть дату видачі!")
            return

        item = DocumentAboutEducationModel(
            title=self.docedu_title.strip(),
            number=self.docedu_number.strip(),
            series=self.docedu_series.strip() or None,  # type: ignore[arg-type]
            issued_by=self.docedu_issued_by.strip() or None,  # type: ignore[arg-type]
            date_of_issue=self.docedu_date_of_issue,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
        )
        if 0 <= self.docedu_index < len(self.documents_about_education):
            self.documents_about_education[self.docedu_index] = item
        else:
            self.documents_about_education.append(item)
        self.docedu_open = False
        self._reset_docedu_dialog()

    @rx.event
    def delete_docedu(self, index: int):
        if 0 <= index < len(self.documents_about_education):
            del self.documents_about_education[index]

    # ============================================================
    # Military accounting dialog
    # ============================================================

    def _reset_mil_dialog(self):
        self.mil_index = -1
        self.mil_number = ""
        self.mil_series = ""
        self.mil_issued_by = ""
        self.mil_date_of_issue = ""

    @rx.event
    def open_mil_add(self):
        self._reset_mil_dialog()
        self.mil_open = True

    @rx.event
    def open_mil_edit(self, index: int):
        if index < 0 or index >= len(self.military_accountings):
            return
        item = self.military_accountings[index]
        self.mil_index = index
        self.mil_number = item.number or ""
        self.mil_series = item.series or ""
        self.mil_issued_by = item.issued_by or ""
        self.mil_date_of_issue = item.date_of_issue or ""
        self.mil_open = True

    @rx.event
    def close_mil(self):
        self.mil_open = False
        self._reset_mil_dialog()

    @rx.event
    def save_mil(self):
        if not self.mil_number:
            yield rx.toast.warning("Введіть номер!")
            return
        if not self.mil_series:
            yield rx.toast.warning("Введіть серію!")
            return
        if not self.mil_date_of_issue:
            yield rx.toast.warning("Введіть дату видачі!")
            return

        item = MilitaryAccountingModel(
            number=self.mil_number.strip(),
            series=self.mil_series.strip(),
            issued_by=self.mil_issued_by.strip() or None,  # type: ignore[arg-type]
            date_of_issue=self.mil_date_of_issue,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
        )
        if 0 <= self.mil_index < len(self.military_accountings):
            self.military_accountings[self.mil_index] = item
        else:
            self.military_accountings.append(item)
        self.mil_open = False
        self._reset_mil_dialog()

    @rx.event
    def delete_mil(self, index: int):
        if 0 <= index < len(self.military_accountings):
            del self.military_accountings[index]

    # ============================================================
    # Medical reference dialog
    # ============================================================

    def _reset_med_dialog(self):
        self.med_index = -1
        self.med_number = ""
        self.med_date_of_issue = ""

    @rx.event
    def open_med_add(self):
        self._reset_med_dialog()
        self.med_open = True

    @rx.event
    def open_med_edit(self, index: int):
        if index < 0 or index >= len(self.medical_references):
            return
        item = self.medical_references[index]
        self.med_index = index
        self.med_number = item.number or ""
        self.med_date_of_issue = item.date_of_issue or ""
        self.med_open = True

    @rx.event
    def close_med(self):
        self.med_open = False
        self._reset_med_dialog()

    @rx.event
    def save_med(self):
        if not self.med_number:
            yield rx.toast.warning("Введіть номер!")
            return
        if not self.med_date_of_issue:
            yield rx.toast.warning("Введіть дату видачі!")
            return

        item = MedicalReferenceModel(
            number=self.med_number.strip(),
            date_of_issue=self.med_date_of_issue,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
        )
        if 0 <= self.med_index < len(self.medical_references):
            self.medical_references[self.med_index] = item
        else:
            self.medical_references.append(item)
        self.med_open = False
        self._reset_med_dialog()

    @rx.event
    def delete_med(self, index: int):
        if 0 <= index < len(self.medical_references):
            del self.medical_references[index]

    # ============================================================
    # Relatives dialog
    # ============================================================

    def _reset_rel_dialog(self):
        self.rel_index = -1
        self.rel_id_kinship = 0
        self.rel_pib = ""
        self.rel_phone_number = ""

    @rx.event
    def open_rel_add(self):
        self._reset_rel_dialog()
        self.rel_open = True

    @rx.event
    def open_rel_edit(self, index: int):
        if index < 0 or index >= len(self.information_about_relatives):
            return
        item = self.information_about_relatives[index]
        self.rel_index = index
        self.rel_id_kinship = item.id_kinship or 0
        self.rel_pib = item.pib or ""
        self.rel_phone_number = item.phone_number or ""
        self.rel_open = True

    @rx.event
    def close_rel(self):
        self.rel_open = False
        self._reset_rel_dialog()

    @rx.var
    def rel_id_kinship_str(self) -> str:
        return str(self.rel_id_kinship) if self.rel_id_kinship else ""

    @rx.event
    def set_rel_id_kinship(self, value: str):
        try:
            self.rel_id_kinship = int(value) if value else 0
        except (ValueError, TypeError):
            self.rel_id_kinship = 0

    @rx.event
    def save_rel(self):
        if not self.rel_id_kinship:
            yield rx.toast.warning("Оберіть тип родинного зв'язку!")
            return
        if not self.rel_pib:
            yield rx.toast.warning("Введіть ПІБ родича!")
            return
        if not self.rel_phone_number:
            yield rx.toast.warning("Введіть номер телефону!")
            return

        item = InformationAboutRelativesModel(
            id_kinship=self.rel_id_kinship,
            pib=self.rel_pib.strip(),
            phone_number=self.rel_phone_number.strip(),
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
        )
        if 0 <= self.rel_index < len(self.information_about_relatives):
            self.information_about_relatives[self.rel_index] = item
        else:
            self.information_about_relatives.append(item)
        self.rel_open = False
        self._reset_rel_dialog()

    @rx.event
    def delete_rel(self, index: int):
        if 0 <= index < len(self.information_about_relatives):
            del self.information_about_relatives[index]

    # ============================================================
    # Special condition (per person) dialog
    # ============================================================

    def _reset_scp_dialog(self):
        self.scp_index = -1
        self.scp_id_special_condition = ""
        self.scp_title = ""
        self.scp_number = ""
        self.scp_description = ""
        self.scp_date_of_issue = ""

    @rx.event
    def open_scp_add(self):
        self._reset_scp_dialog()
        self.scp_open = True

    @rx.event
    def open_scp_edit(self, index: int):
        if index < 0 or index >= len(self.special_conditions_person):
            return
        item = self.special_conditions_person[index]
        self.scp_index = index
        self.scp_id_special_condition = item.id_special_condition or ""
        self.scp_title = item.title or ""
        self.scp_number = item.number or ""
        self.scp_description = item.description or ""
        self.scp_date_of_issue = item.date_of_issue or ""
        self.scp_open = True

    @rx.event
    def close_scp(self):
        self.scp_open = False
        self._reset_scp_dialog()

    @rx.event
    def set_scp_id_special_condition(self, value: str):
        self.scp_id_special_condition = value

    @rx.event
    def save_scp(self):
        if not self.scp_id_special_condition:
            yield rx.toast.warning("Оберіть спеціальну умову!")
            return
        if not self.scp_date_of_issue:
            yield rx.toast.warning("Введіть дату видачі!")
            return

        item = SpecialConditionPersonModel(
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
            id_special_condition=self.scp_id_special_condition,
            title=self.scp_title.strip() or None,  # type: ignore[arg-type]
            number=self.scp_number.strip() or None,  # type: ignore[arg-type]
            description=self.scp_description.strip() or None,  # type: ignore[arg-type]
            date_of_issue=self.scp_date_of_issue,
        )
        if 0 <= self.scp_index < len(self.special_conditions_person):
            self.special_conditions_person[self.scp_index] = item
        else:
            self.special_conditions_person.append(item)
        self.scp_open = False
        self._reset_scp_dialog()

    @rx.event
    def delete_scp(self, index: int):
        if 0 <= index < len(self.special_conditions_person):
            del self.special_conditions_person[index]

    # ============================================================
    # Specialty (priority) dialog
    # ============================================================

    def _reset_sp_dialog(self):
        self.sp_index = -1
        self.sp_combined = ""
        self.sp_id_form_of_study = 0
        self.sp_priority = 1

    @rx.event
    def open_sp_add(self):
        self._reset_sp_dialog()
        next_priority = len(self.specialties) + 1
        self.sp_priority = next_priority
        self.sp_open = True

    @rx.event
    def open_sp_edit(self, index: int):
        if index < 0 or index >= len(self.specialties):
            return
        item = self.specialties[index]
        self.sp_index = index
        self.sp_combined = f"{item.id_speciality_code}|{item.id_speciality_department}"
        self.sp_id_form_of_study = item.id_form_of_study or 0
        self.sp_priority = item.priority or 1
        self.sp_open = True

    @rx.event
    def close_sp(self):
        self.sp_open = False
        self._reset_sp_dialog()

    @rx.event
    def set_sp_combined(self, value: str):
        self.sp_combined = value

    @rx.var
    def sp_id_form_of_study_str(self) -> str:
        return str(self.sp_id_form_of_study) if self.sp_id_form_of_study else ""

    @rx.event
    def set_sp_id_form_of_study(self, value: str):
        try:
            self.sp_id_form_of_study = int(value) if value else 0
        except (ValueError, TypeError):
            self.sp_id_form_of_study = 0
        # Форма обирається першою; зміна форми скидає спеціальність — набір доступних
        # спеціальностей залежить від форми (DK-26).
        self.sp_combined = ""

    @rx.event
    def set_sp_priority(self, value: str):
        try:
            self.sp_priority = int(value) if value else 1
        except (ValueError, TypeError):
            self.sp_priority = 1

    @rx.event
    def save_sp(self):
        if not self.sp_combined:
            yield rx.toast.warning("Оберіть спеціальність!")
            return
        try:
            code, dept = self.sp_combined.split("|", 1)
            id_speciality_code = code
            id_speciality_department = int(dept)
        except Exception:
            yield rx.toast.warning("Некоректна спеціальність!")
            return
        if not self.sp_id_form_of_study:
            yield rx.toast.warning("Оберіть форму навчання!")
            return
        if self.sp_priority < 1:
            yield rx.toast.warning("Пріоритет має бути додатнім!")
            return

        # Дозволяємо ту саму спеціальність з різними формами навчання, але не двічі
        # з однаковою формою (це порушило б ключ specialties_entrants) — DK-26.
        for i, sp in enumerate(self.specialties):
            if (
                sp.id_speciality_code == id_speciality_code
                and sp.id_speciality_department == id_speciality_department
                and sp.id_form_of_study == self.sp_id_form_of_study
                and i != self.sp_index
            ):
                yield rx.toast.warning("Цю спеціальність з обраною формою навчання вже додано!")
                return

        item = SpecialtieEntrantModel(
            id_entrant=self.entrant_id if self.entrant_id > 0 else 0,
            id_speciality_code=id_speciality_code,
            id_speciality_department=id_speciality_department,
            id_form_of_study=self.sp_id_form_of_study,
            priority=self.sp_priority,
        )
        if 0 <= self.sp_index < len(self.specialties):
            self.specialties[self.sp_index] = item
        else:
            self.specialties.append(item)
        self.sp_open = False
        self._reset_sp_dialog()

    @rx.event
    def delete_sp(self, index: int):
        if 0 <= index < len(self.specialties):
            del self.specialties[index]

    # ============================================================
    # ZNO result dialog
    # ============================================================

    def _reset_rz_dialog(self):
        self.rz_index = -1
        self.rz_id_items_zno = 0
        self.rz_points = 0

    @rx.event
    def open_rz_add(self):
        self._reset_rz_dialog()
        self.rz_open = True

    @rx.event
    def open_rz_edit(self, index: int):
        if index < 0 or index >= len(self.results_zno):
            return
        item = self.results_zno[index]
        self.rz_index = index
        self.rz_id_items_zno = item.id_items_zno or 0
        self.rz_points = item.points or 0
        self.rz_open = True

    @rx.event
    def close_rz(self):
        self.rz_open = False
        self._reset_rz_dialog()

    @rx.var
    def rz_id_items_zno_str(self) -> str:
        return str(self.rz_id_items_zno) if self.rz_id_items_zno else ""

    @rx.event
    def set_rz_id_items_zno(self, value: str):
        try:
            self.rz_id_items_zno = int(value) if value else 0
        except (ValueError, TypeError):
            self.rz_id_items_zno = 0

    @rx.event
    def set_rz_points(self, value: str):
        try:
            self.rz_points = int(value) if value else 0
        except (ValueError, TypeError):
            self.rz_points = 0

    @rx.event
    def save_rz(self):
        if not self.rz_id_items_zno:
            yield rx.toast.warning("Оберіть предмет ЗНО!")
            return
        if self.rz_points < 0 or self.rz_points > 200:
            yield rx.toast.warning("Бали мають бути у межах 0-200!")
            return

        item = ResultZnoModel(
            id_items_zno=self.rz_id_items_zno,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
            points=self.rz_points,
        )
        if 0 <= self.rz_index < len(self.results_zno):
            self.results_zno[self.rz_index] = item
        else:
            self.results_zno.append(item)
        self.rz_open = False
        self._reset_rz_dialog()

    @rx.event
    def delete_rz(self, index: int):
        if 0 <= index < len(self.results_zno):
            del self.results_zno[index]

    # ============================================================
    # Save / Cancel
    # ============================================================

    def _validate_main(self) -> Optional[str]:
        if not self.edbo or not self.edbo.strip():
            return "Поле коду ЄДБО обов'язкове!"
        if not self.pib:
            return "Поле ПІБ обов'язкове!"
        if not self.sex:
            return "Оберіть стать!"
        if not self.date_of_birth:
            return "Введіть дату народження!"
        if not self.place_of_registration:
            return "Введіть адресу реєстрації!"
        if not self.mokpp:
            return "Введіть МОКПП!"
        if not self.phone_number:
            return "Введіть номер телефону!"
        if not self.id_source_of_funding:
            return "Оберіть джерело фінансування!"
        if not self.id_entry_base:
            return "Оберіть базу вступу!"
        if not self.id_application_status:
            return "Оберіть статус заявки!"
        return None

    def _build_person(self) -> PersonModel:
        return PersonModel(
            id=self.entrant_id if self.entrant_id > 0 else None,  # type: ignore[arg-type]
            edbo=self.edbo.strip(),
            pib=self.pib.strip(),
            photo=self.photo_bytes,
            photo_mime_type=self.photo_mime,
            citizenship=self.citizenship,
            sex=self.sex,
            date_of_birth=self.date_of_birth,
            place_of_registration_city=self.place_of_registration_city.strip() or None,  # type: ignore[arg-type]
            place_of_registration=self.place_of_registration.strip(),
            mokpp=self.mokpp.strip(),
            email=self.email.strip() or None,  # type: ignore[arg-type]
            phone_number=self.phone_number.strip(),
            the_need_for_a_dormitory=self.the_need_for_a_dormitory,
            id_source_of_funding=self.id_source_of_funding,
            id_entry_base=self.id_entry_base,
            is_deleted=False,
        )

    def _build_entrant(self, person_id: int) -> EntrantModel:
        return EntrantModel(
            id=person_id,
            id_application_status=self.id_application_status,
            id_entrant_group=self.id_entrant_group if self.id_entrant_group > 0 else None,
            comment=self.comment.strip() or None,  # type: ignore[arg-type]
            is_deleted=False,
        )

    @rx.event
    def on_save(self):
        err = self._validate_main()
        if err:
            yield rx.toast.warning(err)
            return

        service = EntrantService()
        try:
            person = self._build_person()
            entrant = self._build_entrant(person_id=self.entrant_id if self.entrant_id > 0 else 0)

            if self.mode == "edit":
                if not self.has_permission(Actions.ENTRANT_EDIT):
                    yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
                    return
                saved = service.edit_one(
                    person=person,
                    entrant=entrant,
                    identity_documents=list(self.identity_documents),
                    documents_about_education=list(self.documents_about_education),
                    military_accountings=list(self.military_accountings),
                    medical_references=list(self.medical_references),
                    information_about_relatives=list(self.information_about_relatives),
                    special_conditions=list(self.special_conditions_person),
                    specialties=list(self.specialties),
                    results_zno=list(self.results_zno),
                )
                yield rx.toast.success("Запис змінено!")
                yield rx.redirect(routes.ENTRANT_VIEW + str(saved.id))
            else:
                if not self.has_permission(Actions.ENTRANT_ADD):
                    yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
                    return
                saved = service.add_one(
                    person=person,
                    entrant=entrant,
                    identity_documents=list(self.identity_documents),
                    documents_about_education=list(self.documents_about_education),
                    military_accountings=list(self.military_accountings),
                    medical_references=list(self.medical_references),
                    information_about_relatives=list(self.information_about_relatives),
                    special_conditions=list(self.special_conditions_person),
                    specialties=list(self.specialties),
                    results_zno=list(self.results_zno),
                )
                yield rx.toast.success("Запис додано!")
                yield rx.redirect(routes.ENTRANT_VIEW + str(saved.id))
        except ValueError as e:
            # Бекенд-валідація (наприклад, недоступна спеціальність) — показуємо текст.
            yield rx.toast.error(str(e))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        if self.mode == "edit" and self.entrant_id > 0:
            return rx.redirect(routes.ENTRANT_VIEW + str(self.entrant_id))
        return rx.redirect(routes.ENTRANT_LIST)
