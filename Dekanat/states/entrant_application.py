import reflex as rx

from typing import Optional, List, Dict
from datetime import datetime

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.entrant_application import (
    EntrantApplicationService,
    EntrantApplicationRow,
)
from Dekanat.services.application_status import ApplicationStatusService
from Dekanat.services.entry_base import EntryBaseService
from Dekanat.services.speciality import SpecialityService
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.admission_campaign_speciality import AdmissionCampaignSpecialityService


class ListEntrantApplicationState(AppState):
    """Список заявок абітурієнтів (DK-35): один рядок на кожну спеціальність з
    пріоритетного списку. Фільтри — ті самі, що у списку абітурієнтів; сортування —
    завжди композитне з фіксованим порядком ключів (ПІБ → пріоритет → спеціальність).
    Клік по заголовку лише перемикає напрямок відповідного стовпця, не змінюючи
    пріоритет ключів."""

    items: Optional[List[EntrantApplicationRow]] = None
    in_progress: bool = True

    # --- Стан панелі фільтрів (дзеркало ListEntrantState) ---
    filter_open: bool = False
    filter_pib: str = ""
    filter_phone: str = ""
    filter_status_id: int = 0
    filter_entry_base_id: int = 0
    filter_campaign_id: int = 0
    filter_speciality_key: str = "__all__"
    filter_top_speciality_key: str = "__all__"
    filter_date_mode: str = "day"  # "day" | "period"
    filter_date_day: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""
    application_status_options: List[Dict[str, str]] = []
    entry_base_options: List[Dict[str, str]] = []
    speciality_options: List[Dict[str, str]] = []
    campaigns: List[AdmissionCampaignModel] = []

    # Сортування. Порядок ключів фіксований (ПІБ → пріоритет → спеціальність);
    # напрямок кожного стовпця незалежний, клік по заголовку тоглить лише його.
    sort_dirs: Dict[str, str] = {"pib": "asc", "priority": "asc", "speciality": "asc"}

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

    def _date_range(self):
        if self.filter_date_mode == "day":
            if not self.filter_date_day:
                return None
            try:
                day = datetime.strptime(self.filter_date_day, "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
            return (
                day.replace(hour=0, minute=0, second=0),
                day.replace(hour=23, minute=59, second=59),
            )
        if not self.filter_date_from and not self.filter_date_to:
            return None
        start_dt = datetime.min
        end_dt = datetime.max
        if self.filter_date_from:
            try:
                start_dt = datetime.strptime(self.filter_date_from, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            except (ValueError, TypeError):
                pass
        if self.filter_date_to:
            try:
                end_dt = datetime.strptime(self.filter_date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except (ValueError, TypeError):
                pass
        return (start_dt, end_dt)

    @staticmethod
    def _parse_spec_key(key: str) -> Optional[int]:
        if not key or key == "__all__":
            return None
        try:
            return int(key)
        except (ValueError, TypeError):
            return None

    def _reload_items(self):
        service = EntrantApplicationService()
        spec_id = self._parse_spec_key(self.filter_speciality_key)
        top_id = self._parse_spec_key(self.filter_top_speciality_key)
        self.items = service.get_list_items(
            pib=self.filter_pib.strip() or None,
            phone=self.filter_phone.strip() or None,
            status_id=self.filter_status_id or None,
            entry_base_id=self.filter_entry_base_id or None,
            created_between=self._campaign_range(),
            created_date_between=self._date_range(),
            priority_speciality_id=spec_id,
            top_priority_speciality_id=top_id,
            sort_dirs=self.sort_dirs,
        )

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_APPLICATION_LIST):
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

    @rx.event
    def set_filter_phone(self, value: str):
        self.filter_phone = value
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
        self.filter_phone = ""
        self.filter_status_id = 0
        self.filter_entry_base_id = 0
        self.filter_campaign_id = 0
        self.filter_speciality_key = "__all__"
        self.filter_top_speciality_key = "__all__"
        self.filter_date_mode = "day"
        self.filter_date_day = ""
        self.filter_date_from = ""
        self.filter_date_to = ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- date filter ---

    @rx.event
    def set_filter_date_mode(self, value: str):
        self.filter_date_mode = "period" if value in ("period", "Період") else "day"
        self.filter_date_day = ""
        self.filter_date_from = ""
        self.filter_date_to = ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_date_day(self, value: str):
        self.filter_date_day = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_date_from(self, value: str):
        self.filter_date_from = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_date_to(self, value: str):
        self.filter_date_to = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def is_date_mode_period(self) -> bool:
        return self.filter_date_mode == "period"

    # --- speciality filter ---

    def _reload_speciality_options(self):
        opts: List[Dict[str, str]] = [{"value": "__all__", "label": "— Будь-яка —"}]
        active = AdmissionCampaignService().get_active_campaign()
        if active is not None and active.id is not None:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(active.id)
            seen_keys: set = set()
            for q in quotas:
                if q.speciality is None:
                    continue
                key = str(q.id_speciality)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                opts.append({
                    "value": key,
                    "label": f"{q.speciality.code} {q.speciality.title} ({q.speciality.tag})",
                })
        if len(opts) == 1:
            for s in SpecialityService().get_list_items():
                opts.append({
                    "value": str(s.id),
                    "label": f"{s.code} {s.title} ({s.tag})",
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

    @rx.event
    def set_filter_top_speciality_key(self, value: str):
        self.filter_top_speciality_key = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- sorting ---

    @rx.event
    def on_click_sort(self, field: str):
        # Порядок ключів не чіпаємо — лише перемикаємо напрямок цього стовпця.
        if field not in ("pib", "priority", "speciality"):
            return
        new_dirs = dict(self.sort_dirs)
        new_dirs[field] = "desc" if new_dirs.get(field, "asc") == "asc" else "asc"
        self.sort_dirs = new_dirs
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def sort_indicator(self) -> Dict[str, str]:
        # Усі три стовпці завжди активні у сортуванні — показуємо стрілку напрямку кожного.
        def _arrow(field: str) -> str:
            return " ↑" if self.sort_dirs.get(field, "asc") == "asc" else " ↓"

        return {
            "pib": _arrow("pib"),
            "priority": _arrow("priority"),
            "speciality": _arrow("speciality"),
        }
