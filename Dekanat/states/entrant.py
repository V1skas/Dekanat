import reflex as rx

from pydantic import BaseModel
from typing import Sequence, Optional, List, Dict
from datetime import date, datetime

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import (
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialtieEntrantSourceOfFundingModel,
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
from Dekanat.services.app_setting import AppSettingService
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.utils.clock import now_local
from Dekanat.services.admission_campaign_speciality import AdmissionCampaignSpecialityService
from Dekanat.models import AdmissionCampaignModel
from Dekanat.utils.display import format_grade


# Значення query-параметра ?from, з яким картку абітурієнта відкрито зі списку заявок
# (DK-35). Керує тим, куди веде кнопка «назад» і чи зберігається контекст крізь
# редагування.
FROM_APPLICATIONS = "applications"


def _from_suffix(came_from: str) -> str:
    """Query-суфікс для збереження контексту «прийшли зі списку заявок» при переходах
    картка → редагування → картка. Порожній рядок, якщо контексту немає."""
    return f"?from={FROM_APPLICATIONS}" if came_from == FROM_APPLICATIONS else ""


# Представлення списку абітурієнтів (DK-49). Перемикаються кнопками над таблицею;
# кожне вантажить лише свої дані окремим методом, дані іншого представлення в память
# не тримаються.
VIEW_GENERAL = "general"       # поточна таблиця з загальною інформацією по заявці
VIEW_PRIORITIES = "priorities"  # ПІБ + теги спеціальностей по пріоритетах (стовпці 1, 2, 3…)


class PriorityCell(BaseModel):
    """Одна клітинка пласкої сітки представлення «Пріоритетні спеціальності» (DK-49).

    Сітку рендеримо пласким списком клітинок (row-major) через один `rx.foreach`,
    щоб уникнути вкладеного `rx.foreach` по атрибуту-списку моделі (заборонено Reflex)
    і при цьому мати динамічну кількість стовпців (пріоритетів)."""
    text: str = ""
    kind: str = "tag"       # "header" | "name" | "tag"
    entrant_id: int = 0     # для kind == "name" — id картки абітурієнта (посилання)


# ---------- List page ----------

class ListEntrantState(AppState):
    items: Optional[Sequence[EntrantModel]] = None
    in_progress: bool = True

    # Активне представлення таблиці (DK-49).
    current_view: str = VIEW_GENERAL

    # Дані представлення «Пріоритетні спеціальності» (DK-49): плаский список клітинок
    # (заголовок + рядки) та кількість стовпців-пріоритетів. Заповнюється лише коли це
    # представлення активне; при перемиканні на загальне — очищається.
    priority_cells: List[PriorityCell] = []
    priority_max: int = 0
    # Окремі фільтри представлення пріоритетів (незалежні від фільтрів загального списку).
    # p_filter_speciality_key — фільтр по пріоритетній спеціальності (№1) — DK-49.
    p_filter_speciality_key: str = "__all__"
    # Фільтр по базі вступу у представленні пріоритетів (DK-51). 0 — без фільтра.
    p_filter_entry_base_id: int = 0
    p_filter_date_mode: str = "day"  # "day" | "period"
    p_filter_date_day: str = ""
    p_filter_date_from: str = ""
    p_filter_date_to: str = ""
    # Одноразова ініціалізація дефолтів фільтра пріоритетів (період активної кампанії).
    p_initialized: bool = False

    # Стан панелі фільтрів
    filter_open: bool = False
    filter_pib: str = ""
    filter_phone: str = ""
    # Пошук по ІПН абітурієнта (DK-61).
    filter_mokpp: str = ""
    filter_status_id: int = 0
    filter_entry_base_id: int = 0
    filter_campaign_id: int = 0  # 0 — без фільтра по кампанії
    # "code|id_department"; "__all__" — без фільтра (Radix забороняє value="" в rx.select.item).
    # filter_top_speciality_key — фільтр по пріоритетній спеціальності (пріоритет №1) — DK-36.
    filter_top_speciality_key: str = "__all__"
    # Фільтр по спеціальній умові особи (DK-51). "__all__" — без фільтра.
    filter_special_condition_key: str = "__all__"
    # Фільтр по маркеру «подано в електронному вигляді» (DK-51):
    # "__all__" | "yes" | "no".
    filter_submitted: str = "__all__"
    # Фільтр по даті створення (DK-34). Режим "day" — конкретний день; "period" — діапазон.
    filter_date_mode: str = "day"  # "day" | "period"
    filter_date_day: str = ""  # YYYY-MM-DD; порожньо — без фільтра
    filter_date_from: str = ""  # YYYY-MM-DD; порожньо — відкрита нижня межа
    filter_date_to: str = ""  # YYYY-MM-DD; порожньо — відкрита верхня межа
    application_status_options: List[Dict[str, str]] = []
    entry_base_options: List[Dict[str, str]] = []
    # Опции спеціальностей — обмежені квотами активної кампанії (як у формі абітурієнта).
    speciality_options: List[Dict[str, str]] = []
    # Опції спеціальних умов для фільтра (DK-51).
    special_condition_options: List[Dict[str, str]] = []
    campaigns: List[AdmissionCampaignModel] = []

    # Сортування. sort_field == "" — за замовчуванням (created_at desc).
    sort_field: str = ""
    sort_dir: str = "asc"  # "asc" | "desc"

    # --- масова зміна статусу (DK-68) ---
    # Режим вибору карток чекбоксами (лише у загальному представленні). Тулбар над
    # таблицею дозволяє виділити набір і застосувати до нього новий статус заяви.
    select_mode: bool = False
    selected_ids: List[int] = []
    # Діалог вибору цільового статусу.
    bulk_status_open: bool = False
    bulk_status_id: int = 0

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
        """Діапазон created_at з фільтра по даті (DK-34). У режимі "day" — межі обраного
        дня; у режимі "period" — [from 00:00, to 23:59:59] з відкритими кінцями
        (datetime.min/max), якщо одна з меж не задана. Повертає None, коли фільтр порожній."""
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
        # period
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
        # Ключ спеціальності — тепер сурогатний id (DK-38). "__all__" — без фільтра.
        if not key or key == "__all__":
            return None
        try:
            return int(key)
        except (ValueError, TypeError):
            return None

    def _submitted_filter(self) -> Optional[bool]:
        """Фільтр по маркеру «подано в електронному вигляді» (DK-51)."""
        if self.filter_submitted == "yes":
            return True
        if self.filter_submitted == "no":
            return False
        return None

    def _reload_items(self):
        service = EntrantService()
        top_id = self._parse_spec_key(self.filter_top_speciality_key)
        cond_code = (
            self.filter_special_condition_key
            if self.filter_special_condition_key and self.filter_special_condition_key != "__all__"
            else None
        )
        self.items = service.get_list_items(
            pib=self.filter_pib.strip() or None,
            phone=self.filter_phone.strip() or None,
            mokpp=self.filter_mokpp.strip() or None,
            status_id=self.filter_status_id or None,
            entry_base_id=self.filter_entry_base_id or None,
            created_between=self._campaign_range(),
            created_date_between=self._date_range(),
            top_priority_speciality_id=top_id,
            special_condition_code=cond_code,
            submitted_electronically=self._submitted_filter(),
            sort_field=self.sort_field or None,
            sort_dir=self.sort_dir,
        )

    # --- priority-specialities view (DK-49) ---

    def _p_date_range(self):
        """Діапазон created_at для фільтра дати представлення пріоритетів (аналог
        `_date_range`, але на окремих полях `p_filter_*`)."""
        if self.p_filter_date_mode == "day":
            if not self.p_filter_date_day:
                return None
            try:
                day = datetime.strptime(self.p_filter_date_day, "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
            return (
                day.replace(hour=0, minute=0, second=0),
                day.replace(hour=23, minute=59, second=59),
            )
        if not self.p_filter_date_from and not self.p_filter_date_to:
            return None
        start_dt = datetime.min
        end_dt = datetime.max
        if self.p_filter_date_from:
            try:
                start_dt = datetime.strptime(self.p_filter_date_from, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            except (ValueError, TypeError):
                pass
        if self.p_filter_date_to:
            try:
                end_dt = datetime.strptime(self.p_filter_date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except (ValueError, TypeError):
                pass
        return (start_dt, end_dt)

    def _reload_priority(self):
        """Перезбирає плаский список клітинок представлення «Пріоритетні спеціальності».
        Полегшену вибірку тримаємо локально — у стан кладемо лише готові клітинки."""
        items = EntrantService().get_priority_items(
            top_priority_speciality_id=self._parse_spec_key(self.p_filter_speciality_key),
            entry_base_id=self.p_filter_entry_base_id or None,
            created_date_between=self._p_date_range(),
        )
        if not items:
            self.priority_cells = []
            self.priority_max = 0
            return

        max_p = 0
        rows: List[tuple] = []  # (entrant_id, pib, base, {priority: tag})
        for e in items:
            pib = e.person.pib if e.person is not None and e.person.pib else "—"
            base = (
                e.person.entry_base.title
                if e.person is not None and e.person.entry_base is not None and e.person.entry_base.title
                else "—"
            )
            by_prio: Dict[int, str] = {}
            for sp in (e.specialties or []):
                if sp.priority is None:
                    continue
                tag = sp.speciality.tag if sp.speciality is not None and sp.speciality.tag else "—"
                by_prio.setdefault(sp.priority, tag)
                if sp.priority > max_p:
                    max_p = sp.priority
            rows.append((e.id, pib, base, by_prio))

        cells: List[PriorityCell] = [
            PriorityCell(text="ПІБ", kind="header"),
            PriorityCell(text="База вступу", kind="header"),
        ]
        for i in range(1, max_p + 1):
            cells.append(PriorityCell(text=str(i), kind="header"))
        for entrant_id, pib, base, by_prio in rows:
            cells.append(PriorityCell(text=pib, kind="name", entrant_id=entrant_id))
            cells.append(PriorityCell(text=base, kind="base"))
            for i in range(1, max_p + 1):
                cells.append(PriorityCell(text=by_prio.get(i, "—"), kind="tag"))
        self.priority_cells = cells
        self.priority_max = max_p

    @rx.var
    def priority_grid_template(self) -> str:
        """CSS grid-template-columns: широкий стовпець ПІБ + стовпець бази вступу +
        N рівних стовпців-пріоритетів."""
        if self.priority_max <= 0:
            return "1fr"
        return "minmax(12rem, 1.5fr) minmax(8rem, 1fr) " + " ".join(["minmax(4rem, 1fr)"] * self.priority_max)

    @rx.event
    def switch_view(self, view: str):
        """Перемикання представлення таблиці (DK-49). Дані попереднього представлення
        очищаємо, щоб не тримати їх у памʼяті, і вантажимо дані нового."""
        if view not in (VIEW_GENERAL, VIEW_PRIORITIES) or view == self.current_view:
            return
        self.current_view = view
        # Режим вибору живе лише у загальному представленні (DK-68) — скидаємо.
        self.select_mode = False
        self.selected_ids = []
        self.in_progress = True
        yield
        try:
            if view == VIEW_PRIORITIES:
                self.items = None
                self._reload_priority()
            else:
                self.priority_cells = []
                self.priority_max = 0
                self._reload_items()
        finally:
            self.in_progress = False

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
            # Спеціальні умови для фільтра (DK-51). Перший пункт — sentinel «__all__».
            self.special_condition_options = [{"value": "__all__", "label": "— Будь-яка —"}]
            self.special_condition_options.extend(
                {"value": s.subcategory_code, "label": f"{s.subcategory_code} {s.title}"}
                for s in SpecialConditionService().get_list_items()
            )
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            active = campaign_service.get_active_campaign()
            self.filter_campaign_id = active.id if active is not None else 0
            self._reload_speciality_options()
            # Дефолт фільтра пріоритетів — період активної кампанії (одноразово).
            if not self.p_initialized:
                if active is not None:
                    self.p_filter_date_mode = "period"
                    self.p_filter_date_from = active.start_date or ""
                    self.p_filter_date_to = active.end_date or ""
                self.p_initialized = True
            # Вантажимо дані активного представлення; неактивне — тримаємо порожнім.
            if self.current_view == VIEW_PRIORITIES:
                self.items = None
                self._reload_priority()
            else:
                self.priority_cells = []
                self.priority_max = 0
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

    @rx.event
    def set_filter_phone(self, value: str):
        self.filter_phone = value
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_mokpp(self, value: str):
        # ІПН — лише цифри, максимум 10 (DK-61), за зразком EntrantFormState.set_mokpp.
        self.filter_mokpp = "".join(c for c in value if c.isdigit())[:10]
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
    def set_filter_special_condition_key(self, value: str):
        self.filter_special_condition_key = value or "__all__"
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_submitted(self, value: str):
        self.filter_submitted = value if value in ("__all__", "yes", "no") else "__all__"
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
        self.filter_mokpp = ""
        self.filter_status_id = 0
        self.filter_entry_base_id = 0
        self.filter_campaign_id = 0
        self.filter_top_speciality_key = "__all__"
        self.filter_special_condition_key = "__all__"
        self.filter_submitted = "__all__"
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

    # --- date filter (DK-34) ---

    @rx.event
    def set_filter_date_mode(self, value: str):
        # value приходить як мітка радіо ("День"/"Період") або як код ("day"/"period").
        # Зміна режиму скидає поля іншого режиму, щоб не лишати "прихований" фільтр.
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
    def set_filter_top_speciality_key(self, value: str):
        self.filter_top_speciality_key = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- priority-view filters (DK-49) ---

    @rx.event
    def set_p_filter_speciality_key(self, value: str):
        self.p_filter_speciality_key = value or "__all__"
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.var
    def p_filter_entry_base_id_str(self) -> str:
        return str(self.p_filter_entry_base_id) if self.p_filter_entry_base_id else ""

    @rx.event
    def set_p_filter_entry_base_id(self, value: str):
        try:
            self.p_filter_entry_base_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.p_filter_entry_base_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.var
    def is_p_date_mode_period(self) -> bool:
        return self.p_filter_date_mode == "period"

    @rx.event
    def set_p_filter_date_mode(self, value: str):
        self.p_filter_date_mode = "period" if value in ("period", "Період") else "day"
        self.p_filter_date_day = ""
        self.p_filter_date_from = ""
        self.p_filter_date_to = ""
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.event
    def set_p_filter_date_day(self, value: str):
        self.p_filter_date_day = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.event
    def set_p_filter_date_from(self, value: str):
        self.p_filter_date_from = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.event
    def set_p_filter_date_to(self, value: str):
        self.p_filter_date_to = value or ""
        self.in_progress = True
        yield
        try:
            self._reload_priority()
        finally:
            self.in_progress = False

    @rx.event
    def clear_priority_filters(self):
        self.p_filter_speciality_key = "__all__"
        self.p_filter_entry_base_id = 0
        self.p_filter_date_mode = "day"
        self.p_filter_date_day = ""
        self.p_filter_date_from = ""
        self.p_filter_date_to = ""
        self.in_progress = True
        yield
        try:
            self._reload_priority()
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
            "created_at": arrow if self.sort_field == "created_at" else "",
            "phone_number": arrow if self.sort_field == "phone_number" else "",
            "email": arrow if self.sort_field == "email" else "",
            "entry_base": arrow if self.sort_field == "entry_base" else "",
            "source_of_funding": arrow if self.sort_field == "source_of_funding" else "",
            "speciality": arrow if self.sort_field == "speciality" else "",
            "entrant_group": arrow if self.sort_field == "entrant_group" else "",
            "application_status": arrow if self.sort_field == "application_status" else "",
        }

    # --- масова зміна статусу (DK-68) ---

    @rx.event
    def toggle_select_mode(self):
        """Вхід/вихід із режиму вибору карток. Гейт правом ENTRANT_EDIT_STATUS —
        те саме право, що й на зміну статусу в картці."""
        if not self.select_mode and not self.has_permission(Actions.ENTRANT_EDIT_STATUS):
            yield rx.toast.error("У Вас немає дозволу на зміну статусу заявок!")
            return
        self.select_mode = not self.select_mode
        if not self.select_mode:
            self.selected_ids = []

    @rx.event
    def select_all(self):
        if self.items is None:
            self.selected_ids = []
            return
        self.selected_ids = [it.id for it in self.items if it.id is not None]

    @rx.event
    def clear_selection(self):
        self.selected_ids = []

    @rx.event
    def toggle_selected(self, entrant_id: int):
        if entrant_id in self.selected_ids:
            self.selected_ids = [i for i in self.selected_ids if i != entrant_id]
        else:
            self.selected_ids = self.selected_ids + [entrant_id]

    @rx.var
    def selected_set(self) -> List[str]:
        """`contains`-перевірка для рендеру стану чекбокса (порівняння з типом
        списку Var; id конвертуємо в рядки)."""
        return [str(i) for i in self.selected_ids]

    @rx.var
    def selected_count(self) -> int:
        return len(self.selected_ids)

    @rx.event
    def open_bulk_status_dialog(self):
        if not self.has_permission(Actions.ENTRANT_EDIT_STATUS):
            yield rx.toast.error("У Вас немає дозволу на зміну статусу заявок!")
            return
        if not self.selected_ids:
            yield rx.toast.warning("Оберіть принаймні одного абітурієнта.")
            return
        self.bulk_status_id = 0
        self.bulk_status_open = True

    @rx.event
    def set_bulk_status_open(self, value: bool):
        self.bulk_status_open = value

    @rx.var
    def bulk_status_id_str(self) -> str:
        return str(self.bulk_status_id) if self.bulk_status_id else ""

    @rx.event
    def set_bulk_status_id(self, value: str):
        try:
            self.bulk_status_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.bulk_status_id = 0

    @rx.event
    def apply_bulk_status(self):
        if not self.has_permission(Actions.ENTRANT_EDIT_STATUS):
            yield rx.toast.error("У Вас немає дозволу на зміну статусу заявок!")
            return
        if not self.selected_ids:
            yield rx.toast.warning("Оберіть принаймні одного абітурієнта.")
            return
        if not self.bulk_status_id:
            yield rx.toast.warning("Оберіть новий статус заяви.")
            return
        try:
            changed = EntrantService().bulk_change_status(
                self.selected_ids, self.bulk_status_id, actor_id=self._actor_id(),
            )
        except Exception:
            yield rx.toast.error("Під час зміни статусу сталася помилка :( Спробуйте знову.")
            return
        self.bulk_status_open = False
        self.select_mode = False
        self.selected_ids = []
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False
        yield rx.toast.success(f"Статус змінено для {changed} абітурієнт(ів).")


# ---------- View page ----------

class ViewEntrantState(AppState):
    item: Optional[EntrantModel] = None
    in_process: bool = True
    # Звідки відкрито картку (query ?from). "applications" — зі списку заявок (DK-35):
    # тоді кнопка «назад» і переходи ведуть назад у список заявок.
    came_from: str = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.came_from = self.router.url.query_parameters.get("from", "") or ""
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

    @rx.var
    def back_route(self) -> str:
        """Куди веде кнопка «назад» у шапці картки: список заявок, якщо картку
        відкрито звідти (DK-35), інакше — звичайний список абітурієнтів."""
        if self.came_from == FROM_APPLICATIONS:
            return routes.ENTRANT_APPLICATION_LIST
        return routes.ENTRANT_LIST

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ENTRANT_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        if self.item is None:
            return None
        # Зберігаємо контекст «зі списку заявок» крізь редагування.
        return rx.redirect(routes.ENTRANT_EDIT + str(self.item.id) + _from_suffix(self.came_from))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRANT_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return
        if self.item is None:
            return

        service = EntrantService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(self.back_route)
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

    @rx.var
    def sp_source_titles(self) -> Dict[str, str]:
        """Назви прийнятних ресурсів фінансування, зведені у рядок через кому, для
        кожного пріоритету (ключ "id_speciality|id_form_of_study") — DK-59."""
        if self.item is None:
            return {}
        result: Dict[str, str] = {}
        for sp in self.item.specialties or []:
            titles = [
                src.source_of_funding.title
                for src in (sp.accepted_sources or [])
                if src.source_of_funding is not None
            ]
            if titles:
                result[f"{sp.id_speciality}|{sp.id_form_of_study}"] = ", ".join(titles)
        return result


# ---------- Add / Edit (shared form state) ----------

CITIZENSHIP_OPTIONS = ["Україна", "Інше"]
SEX_OPTIONS = ["Чоловіча", "Жіноча"]


class EntrantFormState(AppState):
    """Combined form state for both /add and /edit/{id} entrant pages."""

    # ---- Mode / loading ----
    mode: str = "add"  # "add" | "edit"
    entrant_id: int = -1
    in_process: bool = True
    # Контекст «прийшли зі списку заявок» (query ?from) — щоб після збереження/скасування
    # повернутися саме на картку з тим самим контекстом, а звідти — у список заявок (DK-35).
    came_from: str = ""
    # Лічильник для key= на date-інпутах діалогів: змінюється при кожному відкритті
    # діалогу, форсуючи ремоунт інпута, щоб порожнє значення стейту реально показувало
    # пусте поле (нативний <input type=date> інакше може лишати попередню дату). DK-36.
    date_nonce: int = 0

    # ---- Photo (kept as separate bytes/mime; persisted into PersonModel on save) ----
    photo_bytes: Optional[bytes] = None
    photo_mime: Optional[str] = None

    # ---- Person fields (flat for easy form binding) ----
    edbo: str = ""
    # ЄДБО, з яким картку завантажено (edit) — для серверного захисту від зміни
    # без права ENTRANT_EDIT_EDBO (DK-37), за зразком loaded_status_id.
    loaded_edbo: str = ""
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
    # Статус, з яким картку завантажено (edit) — для серверного захисту від зміни
    # без права ENTRANT_EDIT_STATUS (DK-36).
    loaded_status_id: int = 0
    id_entrant_group: int = 0  # 0 means "not assigned"
    # Група, до якої абітурієнт належав на момент завантаження (edit) — щоб не
    # рахувати самого абітурієнта за «зайвого» у попередженні про ліміт (DK-48).
    loaded_entrant_group_id: int = 0
    # Автопідбір групи (DK-48): якщо підбір запропонував НОВУ групу, її назва
    # тримається тут до збереження картки (id_entrant_group при цьому = 0). Реальний
    # запис у БД створюється лише при збереженні.
    pending_new_group_title: str = ""
    # Кількість активних абітурієнтів у кожній групі: {str(group_id): count} —
    # для попередження про досягнутий ліміт при ручному виборі групи (DK-48).
    entrant_group_counts: Dict[str, int] = {}
    # Глобальний ліміт розміру екз. групи (з налаштувань) — DK-48.
    max_entrants_per_group: int = 25
    comment: str = ""
    # «Подано в електронному вигляді» (DK-51).
    submitted_electronically: bool = False

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
    # id предмета ЗНО (str) -> ваговий коефіцієнт (DK-40).
    item_zno_coeffs: Dict[str, float] = {}

    # ---- Child collections ----
    identity_documents: List[IdentityDocumentModel] = []
    documents_about_education: List[DocumentAboutEducationModel] = []
    military_accountings: List[MilitaryAccountingModel] = []
    medical_references: List[MedicalReferenceModel] = []
    information_about_relatives: List[InformationAboutRelativesModel] = []
    special_conditions_person: List[SpecialConditionPersonModel] = []
    specialties: List[SpecialtieEntrantModel] = []
    # Прийнятні ресурси фінансування по кожному пріоритету (DK-59) — довідкова
    # інформація, не впливає на формування рейтингу.
    specialty_sources: List[SpecialtieEntrantSourceOfFundingModel] = []
    results_zno: List[ResultZnoModel] = []

    # ---- Identity document dialog ----
    iddoc_open: bool = False
    iddoc_index: int = -1
    iddoc_id_type: int = 0
    iddoc_number: str = ""
    iddoc_series: str = ""
    iddoc_code: str = ""
    iddoc_unzr: str = ""
    iddoc_issued_by: str = ""
    iddoc_date_of_issue: str = ""
    iddoc_date_of_expiry: str = ""

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
    # Обрані у діалозі ресурси фінансування, прийнятні для цього пріоритету (DK-59).
    sp_accepted_sources: List[int] = []

    # ---- ZNO result dialog ----
    rz_open: bool = False
    rz_index: int = -1
    rz_id_items_zno: int = 0
    # Сирий (введений) бал — редагуємо як рядок, щоб не заважати введенню дробу
    # (DK-47): зберігаємо буквально введене, парсимо у float лише на збереженні.
    rz_points_input: str = ""
    # Калькулятор комплексного балу (DK-47): середнє/сума компонентів (напр. НМТ).
    rz_calc_open: bool = False
    rz_calc_mode: str = "avg"  # "avg" | "sum"
    rz_calc_components: str = ""

    # ---- Duplicate warning dialog (DK-60) ----
    dup_open: bool = False
    # Рядки знайдених можливих дублікатів: id, pib, phone, mokpp, edbo, matched (укр. назви полів через кому).
    dup_rows: List[Dict[str, str]] = []
    # Зведений список полів, за якими знайдено збіги (для тексту попередження).
    dup_fields: str = ""

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
        eg_service = EntrantsGroupService()
        eg = eg_service.get_list_items()
        self.entrant_group_options = [{"value": str(g.id), "label": g.title} for g in eg]
        # Кількості абітурієнтів у групах + глобальний ліміт — для попередження
        # про досягнутий ліміт при виборі групи в картці (DK-48).
        raw_counts = eg_service.get_entrant_counts([g.id for g in eg if g.id is not None])
        self.entrant_group_counts = {str(gid): cnt for gid, cnt in raw_counts.items()}
        self.max_entrants_per_group = AppSettingService().get_max_entrants_per_group()
        sp = SpecialityService().get_list_items()
        sp_by_key: Dict[str, str] = {
            str(s.id): f"{s.code} {s.title} ({s.tag})" for s in sp
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
                    "spec_key": str(q.id_speciality),
                    "base_id": str(q.id_entry_base),
                    "form_id": str(q.id_form_of_study),
                })
        self.campaign_quota_rows = rows
        idt = IdentityDocumentTypeService().get_list_items()
        self.identity_document_type_options = [{"value": str(t.id), "label": t.title} for t in idt]
        ks = KinshipService().get_list_items()
        self.kinship_options = [{"value": str(k.id), "label": k.title} for k in ks]
        sc = SpecialConditionService().get_list_items()
        self.special_condition_options = [
            {"value": s.subcategory_code, "label": f"{s.subcategory_code} {s.title}"} for s in sc
        ]
        iz = ItemZnoService().get_list_items()
        self.item_zno_options = [{"value": str(i.id), "label": i.title} for i in iz]
        self.item_zno_coeffs = {
            str(i.id): (i.coefficient if i.coefficient is not None else 1.0) for i in iz
        }

    def _reset_form(self):
        self.entrant_id = -1
        self.photo_bytes = None
        self.photo_mime = None
        self.edbo = ""
        self.loaded_edbo = ""
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
        self.loaded_status_id = 0
        self.id_entrant_group = 0
        self.loaded_entrant_group_id = 0
        self.pending_new_group_title = ""
        self.comment = ""
        self.submitted_electronically = False
        self.identity_documents = []
        self.documents_about_education = []
        self.military_accountings = []
        self.medical_references = []
        self.information_about_relatives = []
        self.special_conditions_person = []
        self.specialties = []
        self.specialty_sources = []
        self.results_zno = []
        self.dup_open = False
        self.dup_rows = []
        self.dup_fields = ""

    @rx.event
    def on_load_add(self):
        if not self.has_permission(Actions.ENTRANT_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.mode = "add"
        self.came_from = ""
        self.in_process = True
        try:
            self._reset_form()
            self._load_dropdowns()
            # При створенні картки статус виставляється автоматично з дефолтного (DK-36).
            default_status = ApplicationStatusService().get_default()
            if default_status is not None and default_status.id is not None:
                self.id_application_status = default_status.id
                self.loaded_status_id = default_status.id
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
        self.came_from = self.router.url.query_parameters.get("from", "") or ""
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
            self.loaded_edbo = person.edbo or ""
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
            self.loaded_status_id = entrant.id_application_status or 0
            self.id_entrant_group = entrant.id_entrant_group or 0
            self.loaded_entrant_group_id = entrant.id_entrant_group or 0
            self.comment = entrant.comment or ""
            self.submitted_electronically = bool(entrant.submitted_electronically)

            self.identity_documents = list(person.identity_document or [])
            self.documents_about_education = list(person.document_about_education or [])
            self.military_accountings = list(person.military_accounting or [])
            self.medical_references = list(person.medical_reference or [])
            self.information_about_relatives = list(person.information_about_relatives or [])
            self.special_conditions_person = list(person.special_conditions or [])
            self.specialties = list(entrant.specialties or [])
            self.specialty_sources = [
                src
                for sp in (entrant.specialties or [])
                for src in (sp.accepted_sources or [])
            ]
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
        # Ручний вибір групи скасовує запропоновану автопідбором нову групу (DK-48).
        self.pending_new_group_title = ""

    @rx.var
    def pending_group_note(self) -> str:
        """Підказка про заплановану до створення нову групу (автопідбір) — DK-48."""
        if self.pending_new_group_title:
            return f"Буде створено нову групу: {self.pending_new_group_title}"
        return ""

    @rx.var
    def group_limit_warning(self) -> str:
        """Попередження, якщо в обраній (наявній) групі вже досягнуто ліміту (DK-48).
        Самого абітурієнта, якщо він уже в цій групі, за «зайвого» не рахуємо."""
        if self.pending_new_group_title or not self.id_entrant_group:
            return ""
        count = self.entrant_group_counts.get(str(self.id_entrant_group), 0)
        if self.id_entrant_group == self.loaded_entrant_group_id and count > 0:
            count -= 1
        if count >= self.max_entrants_per_group:
            return (
                f"Увага: у цій групі вже {count} абітурієнт(ів) — "
                f"досягнуто ліміту ({self.max_entrants_per_group})."
            )
        return ""

    @rx.event
    def on_click_autodetect_group(self):
        """Автопідбір екзаменаційної групи для цього абітурієнта (DK-48).

        Той самий процес, що й при автоформуванні, але для одного абітурієнта та з
        урахуванням наявних груп. Бере поточну (в памʼяті форми) базу вступу та
        спеціальність найвищого пріоритету. Якщо підходящу наявну групу з вільним
        місцем не знайдено — пропонує нову (запис у БД лише при збереженні картки)."""
        if not self.specialties:
            yield rx.toast.warning("Спочатку додайте хоча б одну спеціальність.")
            return
        if not self.id_entry_base:
            yield rx.toast.warning("Спочатку оберіть базу вступу.")
            return
        # Спеціальність найвищого пріоритету (найменше число пріоритету).
        top = min(
            self.specialties,
            key=lambda s: s.priority if s.priority is not None else 10_000,
        )
        result = EntrantsGroupService().suggest_group_for_entrant(
            top.id_speciality, self.id_entry_base, top.id_form_of_study,
            self.max_entrants_per_group,
        )
        status = result.get("status")
        if status == "error":
            yield rx.toast.error(result.get("message") or "Не вдалося підібрати групу.")
            return
        if status == "existing":
            self.id_entrant_group = int(result.get("group_id") or 0)
            self.pending_new_group_title = ""
            yield rx.toast.success(f"Обрано наявну групу: {result.get('title')}")
            return
        # status == "new"
        self.id_entrant_group = 0
        self.pending_new_group_title = result.get("title") or ""
        yield rx.toast.info(f"Буде створено нову групу: {self.pending_new_group_title}")

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
        # ІПН — лише цифри, максимум 10 (DK-37). Нецифрові символи відкидаємо на вводі.
        self.mokpp = "".join(c for c in value if c.isdigit())[:10]

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

    @rx.event
    def set_submitted_electronically(self, value: bool):
        self.submitted_electronically = value

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
    def set_iddoc_unzr(self, value: str):
        self.iddoc_unzr = value

    @rx.event
    def set_iddoc_issued_by(self, value: str):
        self.iddoc_issued_by = value

    @rx.event
    def set_iddoc_date_of_issue(self, value: str):
        self.iddoc_date_of_issue = value

    @rx.event
    def set_iddoc_date_of_expiry(self, value: str):
        self.iddoc_date_of_expiry = value

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
        # Обмеження розміру фото — 5 МБ (DK-37). Без цього великі файли падали при
        # збереженні у БД на проді (MariaDB).
        if len(data) > 5 * 1024 * 1024:
            yield rx.toast.error("Розмір фото не має перевищувати 5 МБ")
            return
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
        return now_local().date().isoformat()

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
    def sp_source_titles(self) -> Dict[str, str]:
        """Назви прийнятних ресурсів фінансування, зведені у рядок через кому, для
        кожного пріоритету (ключ "id_speciality|id_form_of_study") — DK-59."""
        titles = {opt["value"]: opt["label"] for opt in self.source_of_funding_options}
        result: Dict[str, str] = {}
        for src in self.specialty_sources:
            key = f"{src.id_speciality}|{src.id_form_of_study}"
            label = titles.get(str(src.id_source_of_funding), str(src.id_source_of_funding))
            result[key] = f"{result[key]}, {label}" if key in result else label
        return result

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
    def sp_accepted_sources_str(self) -> List[str]:
        """Рядкові id обраних ресурсів (DK-59) — для contains-перевірки чекбоксів."""
        return [str(s) for s in self.sp_accepted_sources]

    @rx.var
    def sp_speciality_options(self) -> List[Dict[str, str]]:
        """Спеціальності, доступні для (база вступу + обрана форма навчання). Поки
        форма не обрана — порожньо (поле спеціальності неактивне) — DK-26."""
        if not self.id_entry_base or not self.sp_id_form_of_study:
            return []
        base = str(self.id_entry_base)
        form = str(self.sp_id_form_of_study)
        allowed: set = set()
        for row in self.campaign_quota_rows:
            if row["base_id"] != base or row["form_id"] != form:
                continue
            allowed.add(row["spec_key"])
        # all_speciality_options уже впорядкований за кодом спеціальності (SpecialityDao.get_all),
        # тому фільтруємо по ньому — це зберігає сортування у діалозі вибору спеціальності (DK-39).
        return [opt for opt in self.all_speciality_options if opt["value"] in allowed]

    # ============================================================
    # Identity document dialog
    # ============================================================

    def _reset_iddoc_dialog(self):
        self.iddoc_index = -1
        self.iddoc_id_type = 0
        self.iddoc_number = ""
        self.iddoc_series = ""
        self.iddoc_code = ""
        self.iddoc_unzr = ""
        self.iddoc_issued_by = ""
        self.iddoc_date_of_issue = ""
        self.iddoc_date_of_expiry = ""

    @rx.event
    def open_iddoc_add(self):
        self._reset_iddoc_dialog()
        self.date_nonce += 1
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
        self.iddoc_unzr = item.unzr or ""
        self.iddoc_issued_by = item.issued_by or ""
        self.iddoc_date_of_issue = item.date_of_issue or ""
        self.iddoc_date_of_expiry = item.date_of_expiry or ""
        self.date_nonce += 1
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
            unzr=self.iddoc_unzr.strip() or None,
            issued_by=self.iddoc_issued_by.strip(),
            date_of_issue=self.iddoc_date_of_issue,
            date_of_expiry=self.iddoc_date_of_expiry or None,
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
        self.date_nonce += 1
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
        self.date_nonce += 1
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

        item = DocumentAboutEducationModel(
            title=self.docedu_title.strip(),
            number=self.docedu_number.strip() or None,  # type: ignore[arg-type]
            series=self.docedu_series.strip() or None,  # type: ignore[arg-type]
            issued_by=self.docedu_issued_by.strip() or None,  # type: ignore[arg-type]
            date_of_issue=self.docedu_date_of_issue or None,  # type: ignore[arg-type]
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
        self.date_nonce += 1
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
        self.date_nonce += 1
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
        self.date_nonce += 1
        self.med_open = True

    @rx.event
    def open_med_edit(self, index: int):
        if index < 0 or index >= len(self.medical_references):
            return
        item = self.medical_references[index]
        self.med_index = index
        self.med_number = item.number or ""
        self.med_date_of_issue = item.date_of_issue or ""
        self.date_nonce += 1
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
        self.date_nonce += 1
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
        self.date_nonce += 1
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
        self.sp_accepted_sources = []

    @rx.event
    def open_sp_add(self):
        if not self.id_entry_base:
            yield rx.toast.error("Спочатку оберіть базу вступу")
            return
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
        self.sp_combined = str(item.id_speciality) if item.id_speciality else ""
        self.sp_id_form_of_study = item.id_form_of_study or 0
        self.sp_priority = item.priority or 1
        self.sp_accepted_sources = [
            src.id_source_of_funding
            for src in self.specialty_sources
            if src.id_speciality == item.id_speciality and src.id_form_of_study == item.id_form_of_study
        ]
        self.sp_open = True

    @rx.event
    def toggle_sp_source(self, id_source: int, checked: bool):
        if checked:
            if id_source not in self.sp_accepted_sources:
                self.sp_accepted_sources = self.sp_accepted_sources + [id_source]
        else:
            self.sp_accepted_sources = [s for s in self.sp_accepted_sources if s != id_source]

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
            id_speciality = int(self.sp_combined)
        except (ValueError, TypeError):
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
                sp.id_speciality == id_speciality
                and sp.id_form_of_study == self.sp_id_form_of_study
                and i != self.sp_index
            ):
                yield rx.toast.warning("Цю спеціальність з обраною формою навчання вже додано!")
                return

        item = SpecialtieEntrantModel(
            id_entrant=self.entrant_id if self.entrant_id > 0 else 0,
            id_speciality=id_speciality,
            id_form_of_study=self.sp_id_form_of_study,
            priority=self.sp_priority,
        )
        # Прибираємо старі позначки ресурсів для цього рядка (за старим ключем — на
        # випадок редагування зі зміною спеціальності/форми) і додаємо нові (DK-59).
        if 0 <= self.sp_index < len(self.specialties):
            old = self.specialties[self.sp_index]
            self.specialty_sources = [
                src
                for src in self.specialty_sources
                if not (src.id_speciality == old.id_speciality and src.id_form_of_study == old.id_form_of_study)
            ]
            self.specialties[self.sp_index] = item
        else:
            self.specialties.append(item)
        self.specialty_sources = self.specialty_sources + [
            SpecialtieEntrantSourceOfFundingModel(
                id_entrant=self.entrant_id if self.entrant_id > 0 else 0,
                id_speciality=id_speciality,
                id_form_of_study=self.sp_id_form_of_study,
                id_source_of_funding=src_id,
            )
            for src_id in self.sp_accepted_sources
        ]
        self.sp_open = False
        self._reset_sp_dialog()

    @rx.event
    def delete_sp(self, index: int):
        if 0 <= index < len(self.specialties):
            removed = self.specialties[index]
            self.specialty_sources = [
                src
                for src in self.specialty_sources
                if not (src.id_speciality == removed.id_speciality and src.id_form_of_study == removed.id_form_of_study)
            ]
            del self.specialties[index]

    # ============================================================
    # ZNO result dialog
    # ============================================================

    def _reset_rz_dialog(self):
        self.rz_index = -1
        self.rz_id_items_zno = 0
        self.rz_points_input = ""
        self.rz_calc_open = False
        self.rz_calc_mode = "avg"
        self.rz_calc_components = ""

    @rx.event
    def open_rz_add(self):
        self._reset_rz_dialog()
        self.rz_open = True

    @rx.event
    def open_rz_edit(self, index: int):
        if index < 0 or index >= len(self.results_zno):
            return
        item = self.results_zno[index]
        self._reset_rz_dialog()
        self.rz_index = index
        self.rz_id_items_zno = item.id_items_zno or 0
        # У діалозі редагуємо сирий (введений) бал, а не домножений (DK-40), щоб
        # повторне збереження не множило вдруге. points_raw бекфілиться з points.
        raw = item.points_raw if item.points_raw is not None else item.points
        self.rz_points_input = format_grade(raw)
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
    def set_rz_points_input(self, value: str):
        self.rz_points_input = value

    @rx.var
    def rz_coefficient_hint(self) -> str:
        coeff = self.item_zno_coeffs.get(str(self.rz_id_items_zno), 1.0)
        return f"Цей бал буде домножено на коефіцієнт предмета (×{coeff})."

    # ---- Complex-grade calculator (avg / sum of components) ----

    @rx.event
    def toggle_rz_calc(self):
        self.rz_calc_open = not self.rz_calc_open

    @rx.event
    def set_rz_calc_mode(self, mode: str):
        self.rz_calc_mode = mode if mode in ("avg", "sum") else "avg"

    @rx.event
    def set_rz_calc_components(self, value: str):
        self.rz_calc_components = value

    @rx.var
    def is_rz_calc_avg(self) -> bool:
        return self.rz_calc_mode == "avg"

    def _rz_calc_numbers(self) -> List[float]:
        nums: List[float] = []
        raw = (self.rz_calc_components or "").replace(";", " ").replace(",", " ")
        for tok in raw.split():
            try:
                nums.append(float(tok))
            except (ValueError, TypeError):
                continue
        return nums

    def _rz_calc_value(self) -> Optional[float]:
        nums = self._rz_calc_numbers()
        if not nums:
            return None
        if self.rz_calc_mode == "sum":
            return round(sum(nums), 2)
        return round(sum(nums) / len(nums), 2)

    @rx.var
    def rz_calc_result_str(self) -> str:
        value = self._rz_calc_value()
        return format_grade(value) if value is not None else "—"

    @rx.event
    def rz_calc_apply(self):
        value = self._rz_calc_value()
        if value is None:
            yield rx.toast.warning("Введіть компоненти для розрахунку!")
            return
        self.rz_points_input = format_grade(value)
        self.rz_calc_open = False

    @rx.event
    def save_rz(self):
        if not self.rz_id_items_zno:
            yield rx.toast.warning("Оберіть предмет ЗНО!")
            return
        raw = (self.rz_points_input or "").strip()
        if raw == "":
            yield rx.toast.warning("Введіть бал!")
            return
        try:
            points = float(raw.replace(",", "."))
        except (ValueError, TypeError):
            yield rx.toast.warning("Бал має бути числом!")
            return
        if points < 0 or points > 200:
            yield rx.toast.warning("Бали мають бути у межах 0-200!")
            return

        # Домножуємо введений бал на коефіцієнт предмета при збереженні (DK-40).
        coeff = self.item_zno_coeffs.get(str(self.rz_id_items_zno), 1.0)
        weighted = round(points * coeff, 2)
        item = ResultZnoModel(
            id_items_zno=self.rz_id_items_zno,
            id_person=self.entrant_id if self.entrant_id > 0 else 0,
            points=weighted,
            points_raw=points,
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
        # ЄДБО необов'язковий (DK-37).
        if not self.pib:
            return "Поле ПІБ обов'язкове!"
        if not self.sex:
            return "Оберіть стать!"
        if not self.date_of_birth:
            return "Введіть дату народження!"
        if not self.place_of_registration:
            return "Введіть адресу реєстрації!"
        # ІПН необов'язковий (DK-38), але якщо вказаний — рівно 10 цифр.
        if self.mokpp and not (self.mokpp.isdigit() and len(self.mokpp) == 10):
            return "ІПН має містити рівно 10 цифр!"
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
            edbo=self.edbo.strip() or None,  # type: ignore[arg-type]
            pib=self.pib.strip(),
            photo=self.photo_bytes,
            photo_mime_type=self.photo_mime,
            citizenship=self.citizenship,
            sex=self.sex,
            date_of_birth=self.date_of_birth,
            place_of_registration_city=self.place_of_registration_city.strip() or None,  # type: ignore[arg-type]
            place_of_registration=self.place_of_registration.strip(),
            mokpp=self.mokpp.strip() or None,  # type: ignore[arg-type]
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
            submitted_electronically=self.submitted_electronically,
            is_deleted=False,
        )

    def _build_specialty_sources(self) -> list[SpecialtieEntrantSourceOfFundingModel]:
        """Нові інстанси для передачі в сервіс (DK-59): DAO робить `make_transient`
        на переданих обʼєктах і додає їх у сесію, що після `commit` (expire_on_commit)
        робить їх detached — якщо передати ті самі обʼєкти, що лежать у
        `self.specialty_sources`, наступне звернення до їхніх атрибутів (напр. у
        `sp_source_titles` при обчисленні дельти стану) впаде з DetachedInstanceError."""
        return [
            SpecialtieEntrantSourceOfFundingModel(
                id_entrant=s.id_entrant,
                id_speciality=s.id_speciality,
                id_form_of_study=s.id_form_of_study,
                id_source_of_funding=s.id_source_of_funding,
            )
            for s in self.specialty_sources
        ]

    @rx.event
    def on_save(self):
        # Серверний захист статусу: без права ENTRANT_EDIT_STATUS поле статусу
        # недоступне в UI, але клієнт міг би надіслати інше значення — відкидаємо його
        # і повертаємо вихідний статус (для edit) або дефолтний (для add). DK-36.
        if not self.has_permission(Actions.ENTRANT_EDIT_STATUS):
            self.id_application_status = self.loaded_status_id

        # Серверний захист ЄДБО: без права ENTRANT_EDIT_EDBO поле недоступне в UI,
        # але клієнт міг би надіслати інше значення — відкидаємо його і повертаємо
        # вихідний ЄДБО (для edit) або порожній (для add). DK-37.
        if not self.has_permission(Actions.ENTRANT_EDIT_EDBO):
            self.edbo = self.loaded_edbo

        err = self._validate_main()
        if err:
            yield rx.toast.warning(err)
            return

        # Попередження про можливий дублікат картки (DK-60): шукаємо збіги за
        # ПІБ/телефоном/ІПН/ЄДБО серед не видалених абітурієнтів (крім себе при
        # редагуванні). Якщо є хоч один збіг — показуємо діалог і НЕ зберігаємо,
        # доки користувач сам не підтвердить продовження.
        try:
            matches = EntrantService().find_duplicates(
                pib=self.pib.strip() or None,
                phone=self.phone_number.strip() or None,
                mokpp=self.mokpp.strip() or None,
                edbo=self.edbo.strip() or None,
                exclude_id=self.entrant_id if self.entrant_id > 0 else None,
            )
        except Exception:
            matches = []
        if matches:
            self._open_duplicate_dialog(matches)
            return

        yield from self._persist_entrant()

    def _open_duplicate_dialog(self, matches: Sequence[EntrantModel]):
        """Формує рядки таблиці й зведений список полів-збігів для діалогу
        попередження про дублікат (DK-60)."""
        pib_q = self.pib.strip().lower()
        phone_q = self.phone_number.strip()
        mokpp_q = self.mokpp.strip()
        edbo_q = self.edbo.strip().lower()

        rows: List[Dict[str, str]] = []
        fields_found: set = set()
        for e in matches:
            p = e.person
            matched: List[str] = []
            if pib_q and p is not None and p.pib and p.pib.strip().lower() == pib_q:
                matched.append("ПІБ")
            if phone_q and p is not None and p.phone_number and p.phone_number.strip() == phone_q:
                matched.append("Телефон")
            if mokpp_q and p is not None and p.mokpp and p.mokpp.strip() == mokpp_q:
                matched.append("ІПН")
            if edbo_q and p is not None and p.edbo and p.edbo.strip().lower() == edbo_q:
                matched.append("ЄДБО")
            fields_found.update(matched)
            rows.append({
                "id": str(e.id),
                "pib": p.pib if p is not None and p.pib else "—",
                "phone": p.phone_number if p is not None and p.phone_number else "—",
                "mokpp": p.mokpp if p is not None and p.mokpp else "—",
                "edbo": p.edbo if p is not None and p.edbo else "—",
                "matched": ", ".join(matched),
            })
        self.dup_rows = rows
        self.dup_fields = ", ".join(sorted(fields_found))
        self.dup_open = True

    @rx.event
    def set_dup_open(self, value: bool):
        self.dup_open = value

    @rx.event
    def on_cancel_duplicate(self):
        self.dup_open = False

    @rx.event
    def on_confirm_duplicate(self):
        self.dup_open = False
        yield from self._persist_entrant()

    @rx.event
    def open_duplicate_card(self, entrant_id: int):
        """Відкриває картку знайденого можливого дублікату у новій вкладці (DK-60) —
        щоб не втратити незбережені дані поточної форми."""
        return rx.redirect(routes.ENTRANT_VIEW + str(entrant_id), is_external=True)

    def _persist_entrant(self):
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
                    specialty_sources=self._build_specialty_sources(),
                    new_group_title=self.pending_new_group_title or None,
                    actor_id=self._actor_id(),
                )
                yield rx.toast.success("Запис змінено!")
                yield rx.redirect(routes.ENTRANT_VIEW + str(saved.id) + _from_suffix(self.came_from))
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
                    specialty_sources=self._build_specialty_sources(),
                    new_group_title=self.pending_new_group_title or None,
                    actor_id=self._actor_id(),
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
            return rx.redirect(routes.ENTRANT_VIEW + str(self.entrant_id) + _from_suffix(self.came_from))
        return rx.redirect(routes.ENTRANT_LIST)
