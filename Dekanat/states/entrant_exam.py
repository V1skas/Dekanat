import reflex as rx

from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import (
    EntrantExamModel,
    EntrantGroupModel,
    ItemZnoModel,
    WorkerModel,
    AdmissionCampaignModel,
)
from Dekanat.services.entrant_exam import EntrantExamService
from Dekanat.services.entrants_group import EntrantsGroupService
from Dekanat.services.item_zno import ItemZnoService
from Dekanat.services.worker import WorkerService
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.result_zno import ResultZnoService
from Dekanat.utils.display import disambiguate_pib


# ============================================================
# List
# ============================================================

class ListEntrantExamState(AppState):
    items: Optional[Sequence[EntrantExamModel]] = None
    in_progress: bool = True

    # Передзібрані рядки для таблиці — на сервері форматуються списки
    # відповідальних співробітників (у Var[List[WorkerModel]] немає зручного join).
    items_display: List[Dict[str, str]] = []

    # ---- Filter panel ----
    filter_open: bool = False
    filter_group_id: int = 0
    filter_item_zno_id: int = 0
    filter_worker_id: int = 0
    filter_campaign_id: int = 0  # 0 — без фільтра по кампанії

    group_options_data: List[EntrantGroupModel] = []
    item_zno_options_data: List[ItemZnoModel] = []
    worker_options_data: List[WorkerModel] = []
    campaigns: List[AdmissionCampaignModel] = []

    def _campaign_date_range(self) -> Optional[tuple]:
        if not self.filter_campaign_id:
            return None
        campaign = next((c for c in self.campaigns if c.id == self.filter_campaign_id), None)
        if campaign is None or not campaign.start_date or not campaign.end_date:
            return None
        return (campaign.start_date, campaign.end_date)

    def _reload_items(self):
        service = EntrantExamService()
        items = list(service.get_list_items(
            id_group=self.filter_group_id or None,
            id_item_zno=self.filter_item_zno_id or None,
            id_worker=self.filter_worker_id or None,
            date_between=self._campaign_date_range(),
        ))
        self.items = items
        self.items_display = [
            {
                "id": str(it.id),
                "group": (it.group.title if it.group is not None else "—"),
                "item_zno": (it.item_zno.title if it.item_zno is not None else "—"),
                "date": it.date or "—",
                "time_start": it.time_start or "—",
                "time_end": it.time_end or "—",
                "workers": ", ".join(
                    (w.pib for w in (it.responsible_workers or [])) if it.responsible_workers else []
                ) or "—",
            }
            for it in items
        ]

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            self.group_options_data = list(EntrantsGroupService().get_list_items())
            self.item_zno_options_data = list(ItemZnoService().get_list_items())
            self.worker_options_data = list(WorkerService().get_list_items())
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            # За замовчуванням — активна кампанія; якщо її немає — без фільтра.
            active = campaign_service.get_active_campaign()
            self.filter_campaign_id = active.id if active is not None else 0
            self._reload_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ENTRANT_EXAM_ADD)

    @rx.event
    def on_click_print(self):
        return rx.redirect(routes.ENTRANT_EXAM_PRINT)

    # --- filter panel ---

    @rx.event
    def toggle_filter(self):
        self.filter_open = not self.filter_open

    @rx.var
    def group_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(g.id), "label": g.title} for g in self.group_options_data)
        return opts

    @rx.var
    def item_zno_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(i.id), "label": i.title} for i in self.item_zno_options_data)
        return opts

    @rx.var
    def worker_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(w.id), "label": w.pib} for w in self.worker_options_data)
        return opts

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(c.id), "label": c.title} for c in self.campaigns)
        return opts

    @rx.var
    def filter_campaign_id_str(self) -> str:
        return str(self.filter_campaign_id) if self.filter_campaign_id else "0"

    @rx.var
    def filter_group_id_str(self) -> str:
        return str(self.filter_group_id) if self.filter_group_id else "0"

    @rx.var
    def filter_item_zno_id_str(self) -> str:
        return str(self.filter_item_zno_id) if self.filter_item_zno_id else "0"

    @rx.var
    def filter_worker_id_str(self) -> str:
        return str(self.filter_worker_id) if self.filter_worker_id else "0"

    def _set_filter_int(self, attr: str, value: str):
        try:
            setattr(self, attr, int(value) if value else 0)
        except (ValueError, TypeError):
            setattr(self, attr, 0)

    @rx.event
    def set_filter_group_id(self, value: str):
        self._set_filter_int("filter_group_id", value)
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_item_zno_id(self, value: str):
        self._set_filter_int("filter_item_zno_id", value)
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_worker_id(self, value: str):
        self._set_filter_int("filter_worker_id", value)
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def set_filter_campaign_id(self, value: str):
        self._set_filter_int("filter_campaign_id", value)
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def clear_filters(self):
        self.filter_group_id = 0
        self.filter_item_zno_id = 0
        self.filter_worker_id = 0
        self.filter_campaign_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False


# ============================================================
# Form (Add / Edit shared base)
# ============================================================

class _ExamFormBase(AppState):
    item: EntrantExamModel = EntrantExamModel()
    #in_process: bool = False

    # Список ID відповідальних співробітників (для дзеркалення у multi-select-подібному UI)
    responsible_worker_ids: List[int] = []

    # Довідники для dropdown'ів
    group_options_data: List[EntrantGroupModel] = []
    item_zno_options_data: List[ItemZnoModel] = []
    worker_options_data: List[WorkerModel] = []

    # ---- Worker picker dialog ----
    w_open: bool = False
    w_search: str = ""

    # ---- Field bindings ----

    @rx.var
    def id_group_str(self) -> str:
        if self.item is None or self.item.id_group is None or self.item.id_group == 0:
            return ""
        return str(self.item.id_group)

    @rx.event
    def set_id_group(self, value: str):
        try:
            self.item.id_group = int(value) if value else 0
        except (ValueError, TypeError):
            self.item.id_group = 0

    @rx.var
    def id_item_zno_str(self) -> str:
        if self.item is None or self.item.id_item_zno is None or self.item.id_item_zno == 0:
            return ""
        return str(self.item.id_item_zno)

    @rx.event
    def set_id_item_zno(self, value: str):
        try:
            self.item.id_item_zno = int(value) if value else 0
        except (ValueError, TypeError):
            self.item.id_item_zno = 0

    @rx.var
    def date(self) -> str:
        return self.item.date if self.item is not None and self.item.date is not None else ""

    @rx.event
    def set_date(self, value: str):
        self.item.date = value

    @rx.var
    def time_start(self) -> str:
        return self.item.time_start if self.item is not None and self.item.time_start is not None else ""

    @rx.event
    def set_time_start(self, value: str):
        self.item.time_start = value

    @rx.var
    def time_end(self) -> str:
        return self.item.time_end if self.item is not None and self.item.time_end is not None else ""

    @rx.event
    def set_time_end(self, value: str):
        self.item.time_end = value

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item is not None and self.item.description is not None else ""

    @rx.event
    def set_description(self, value: str):
        self.item.description = value if value != "" else None  # type: ignore[assignment]

    # ---- Dropdown options ----

    @rx.var
    def group_options(self) -> List[Dict[str, str]]:
        return [{"value": str(g.id), "label": g.title} for g in self.group_options_data]

    @rx.var
    def item_zno_options(self) -> List[Dict[str, str]]:
        return [{"value": str(i.id), "label": i.title} for i in self.item_zno_options_data]

    # ---- Responsible workers ----

    @rx.var
    def chosen_workers_display(self) -> List[Dict[str, str]]:
        index = {w.id: w for w in self.worker_options_data}
        rows: List[Dict[str, str]] = []
        for wid in self.responsible_worker_ids:
            w = index.get(wid)
            if w is not None:
                rows.append({"id": str(wid), "pib": w.pib, "email": w.email or ""})
        return rows

    @rx.var
    def picker_worker_rows(self) -> List[Dict[str, str]]:
        chosen = set(self.responsible_worker_ids)
        q = (self.w_search or "").lower().strip()
        rows: List[Dict[str, str]] = []
        for w in self.worker_options_data:
            if w.id in chosen:
                continue
            if q:
                pib = (w.pib or "").lower()
                login = (w.login or "").lower()
                email = (w.email or "").lower()
                if q not in pib and q not in login and q not in email:
                    continue
            rows.append({"id": str(w.id), "pib": w.pib, "email": w.email or ""})
        return rows

    @rx.event
    def set_w_search(self, value: str):
        self.w_search = value

    @rx.event
    def open_w_picker(self):
        self.w_search = ""
        self.w_open = True

    @rx.event
    def close_w_picker(self):
        self.w_open = False
        self.w_search = ""

    @rx.event
    def set_w_open(self, value: bool):
        self.w_open = value
        if not value:
            self.w_search = ""

    @rx.event
    def pick_worker(self, worker_id_str: str):
        try:
            wid = int(worker_id_str)
        except (ValueError, TypeError):
            return
        if wid in self.responsible_worker_ids:
            return
        if not any(w.id == wid for w in self.worker_options_data):
            return
        self.responsible_worker_ids.append(wid)
        self.w_open = False
        self.w_search = ""

    @rx.event
    def remove_worker(self, worker_id_str: str):
        try:
            wid = int(worker_id_str)
        except (ValueError, TypeError):
            return
        self.responsible_worker_ids = [x for x in self.responsible_worker_ids if x != wid]

    # ---- Validation ----

    def _validate(self) -> Optional[str]:
        if self.item.id_group is None or self.item.id_group <= 0:
            return "Оберіть групу!"
        if self.item.id_item_zno is None or self.item.id_item_zno <= 0:
            return "Оберіть предмет!"
        if not self.item.date:
            return "Вкажіть дату!"
        if not self.item.time_start:
            return "Вкажіть час початку!"
        if not self.item.time_end:
            return "Вкажіть час закінчення!"
        if self.item.time_end <= self.item.time_start:
            return "Час закінчення має бути пізніше часу початку!"
        return None

    def _load_dropdowns(self):
        self.group_options_data = list(EntrantsGroupService().get_list_items())
        self.item_zno_options_data = list(ItemZnoService().get_list_items())
        self.worker_options_data = list(WorkerService().get_list_items())


class AddEntrantExamState(_ExamFormBase):
    in_process: bool = True

    def _reload_item(self):
        self.item = EntrantExamModel()
        self.responsible_worker_ids = []
        self.w_open = False
        self.w_search = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            self._load_dropdowns()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        err = self._validate()
        if err:
            yield rx.toast.warning(err)
            return

        try:
            self.item = EntrantExamService().add_one(self.item, list(self.responsible_worker_ids))
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ENTRANT_EXAM_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANT_EXAM_LIST)


class EditEntrantExamState(_ExamFormBase):
    in_process: bool = True

    def _reload_item(self):
        service = EntrantExamService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded
            self.responsible_worker_ids = [w.id for w in (loaded.responsible_workers or [])]
        self.w_open = False
        self.w_search = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._load_dropdowns()
            self._reload_item()
            if self.item is None or self.item.id is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANT_EXAM_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        err = self._validate()
        if err:
            yield rx.toast.warning(err)
            return

        try:
            self.item = EntrantExamService().edit_one(self.item, list(self.responsible_worker_ids))
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ENTRANT_EXAM_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANT_EXAM_VIEW + str(self.item.id))


# ============================================================
# View
# ============================================================

class ViewEntrantExamState(AppState):
    item: EntrantExamModel = EntrantExamModel()
    in_process: bool = True

    responsible_workers_display: List[Dict[str, str]] = []

    # ---- Grading section ----
    grading_open: bool = False
    # Список абітурієнтів групи, для якої проводиться іспит (передзібрані рядки таблиці).
    grading_rows: List[Dict[str, str]] = []
    # Мапа поточних (домножених) оцінок: id_entrant -> grade (str). Показується в таблиці.
    grades_by_entrant: Dict[str, str] = {}
    # Мапа сирих (введених) оцінок: id_entrant -> raw (str). Редагується в діалозі, щоб
    # повторне збереження не домножувало вдруге (DK-40).
    raw_by_entrant: Dict[str, str] = {}
    # Коефіцієнт предмета цього іспиту (DK-40).
    item_coefficient: float = 1.0
    # Сирий список абітурієнтів (id + pib) — використовується лише на бекенді для
    # пересборки `grading_rows` після зміни оцінок (leading underscore — backend-only).
    _raw_entrants: List[Dict[str, str]] = []

    # ---- Grading dialog ----
    g_open: bool = False
    g_index: int = 0
    g_grade_input: str = ""
    g_grade_original: str = ""

    def _reload_grading_rows(self):
        # Повні тезки в групі розрізняємо телефоном (DK-36).
        display = disambiguate_pib((row["pib"], row.get("phone", "")) for row in self._raw_entrants)
        self.grading_rows = [
            {
                "id": str(row["id"]),
                "pib": shown,
                "grade": self.grades_by_entrant.get(str(row["id"]), ""),
            }
            for row, shown in zip(self._raw_entrants, display)
        ]

    def _reload_item(self):
        service = EntrantExamService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded
            self.item_coefficient = (
                loaded.item_zno.coefficient
                if loaded.item_zno is not None and loaded.item_zno.coefficient is not None
                else 1.0
            )
            self.responsible_workers_display = [
                {"pib": w.pib, "email": w.email or "—", "phone": w.phone_number or "—"}
                for w in (loaded.responsible_workers or [])
            ]
            # Завантажуємо склад групи + існуючі оцінки (з results_zno за поточним предметом).
            entrants = list(EntrantsGroupService().get_entrants(loaded.id_group))
            self._raw_entrants = [
                {
                    "id": str(e.id),
                    "pib": e.person.pib if e.person is not None else f"Абітурієнт #{e.id}",
                    "phone": (e.person.phone_number or "") if e.person is not None else "",
                }
                for e in entrants
            ]
            person_ids = [int(r["id"]) for r in self._raw_entrants]
            results = ResultZnoService().get_by_subject_and_persons(
                loaded.id_item_zno, person_ids
            )
            self.grades_by_entrant = {
                str(r.id_person): str(r.points) for r in results
            }
            self.raw_by_entrant = {
                str(r.id_person): str(r.points_raw if r.points_raw is not None else r.points)
                for r in results
            }
            self._reload_grading_rows()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._raw_entrants = []
            self.grades_by_entrant = {}
            self.raw_by_entrant = {}
            self.item_coefficient = 1.0
            self.grading_rows = []
            self.grading_open = False
            self.g_open = False
            self.g_index = 0
            self.g_grade_input = ""
            self.g_grade_original = ""
            self._reload_item()
            if self.item is None or self.item.id is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANT_EXAM_LIST)
            else:
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ENTRANT_EXAM_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = EntrantExamService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ENTRANT_EXAM_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def group_title(self) -> str:
        if self.item is not None and self.item.group is not None and self.item.group.title is not None:
            return self.item.group.title
        return "—"

    @rx.var
    def item_zno_title(self) -> str:
        if self.item is not None and self.item.item_zno is not None and self.item.item_zno.title is not None:
            return self.item.item_zno.title
        return "—"

    @rx.var
    def date(self) -> str:
        return self.item.date if self.item is not None and self.item.date is not None else "—"

    @rx.var
    def time_start(self) -> str:
        return self.item.time_start if self.item is not None and self.item.time_start is not None else "—"

    @rx.var
    def time_end(self) -> str:
        return self.item.time_end if self.item is not None and self.item.time_end is not None else "—"

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item is not None and self.item.description is not None else ""

    # ============================================================
    # Grading section + dialog
    # ============================================================

    @rx.event
    def toggle_grading_open(self):
        self.grading_open = not self.grading_open

    @rx.var
    def grading_total(self) -> int:
        return len(self.grading_rows)

    @rx.var
    def current_entrant_pib(self) -> str:
        if 0 <= self.g_index < len(self.grading_rows):
            return self.grading_rows[self.g_index]["pib"]
        return "—"

    @rx.var
    def grading_indicator(self) -> str:
        if not self.grading_rows:
            return "0 / 0"
        return f"{self.g_index + 1} / {len(self.grading_rows)}"

    @rx.var
    def has_prev_entrant(self) -> bool:
        return self.g_index > 0

    @rx.var
    def has_next_entrant(self) -> bool:
        return self.g_index < len(self.grading_rows) - 1

    def _load_dialog_for_index(self, index: int):
        if not (0 <= index < len(self.grading_rows)):
            return
        self.g_index = index
        # У діалозі редагуємо сирий (введений) бал, а не домножений (DK-40).
        existing = self.raw_by_entrant.get(self.grading_rows[index]["id"], "")
        self.g_grade_input = existing
        self.g_grade_original = existing

    @rx.var
    def grading_coefficient_hint(self) -> str:
        return f"Цей бал буде домножено на коефіцієнт предмета (×{self.item_coefficient})."

    @rx.event
    def open_grading_dialog(self, index: int = 0):
        if not self.grading_rows:
            return rx.toast.warning("У групі немає абітурієнтів!")
        if not (0 <= index < len(self.grading_rows)):
            index = 0
        self._load_dialog_for_index(index)
        self.g_open = True

    @rx.event
    def open_grading_dialog_for(self, entrant_id_str: str):
        for i, row in enumerate(self.grading_rows):
            if row["id"] == entrant_id_str:
                self._load_dialog_for_index(i)
                self.g_open = True
                return
        return rx.toast.error("Абітурієнта не знайдено в групі!")

    @rx.event
    def close_grading_dialog(self):
        self.g_open = False

    @rx.event
    def set_g_open(self, value: bool):
        self.g_open = value

    @rx.event
    def set_g_grade_input(self, value: str):
        self.g_grade_input = value

    @rx.event
    def reset_grade(self):
        self.g_grade_input = self.g_grade_original

    @rx.event
    def prev_entrant(self):
        if self.g_index > 0:
            self._load_dialog_for_index(self.g_index - 1)

    @rx.event
    def next_entrant(self):
        if self.g_index < len(self.grading_rows) - 1:
            self._load_dialog_for_index(self.g_index + 1)

    @rx.event
    def save_grade(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return
        if self.item is None or self.item.id is None or self.item.id_item_zno is None:
            yield rx.toast.error("Іспит не завантажений!")
            return
        if not (0 <= self.g_index < len(self.grading_rows)):
            return
        row = self.grading_rows[self.g_index]
        try:
            entrant_id = int(row["id"])
        except (ValueError, TypeError):
            yield rx.toast.error("Некоректний ідентифікатор абітурієнта!")
            return

        raw = (self.g_grade_input or "").strip()
        points: Optional[int]
        weighted: Optional[int]
        if raw == "":
            points = None
            weighted = None
        else:
            try:
                points = int(raw)
            except ValueError:
                yield rx.toast.warning("Оцінка має бути цілим числом!")
                return
            # Домножуємо введений бал на коефіцієнт предмета при збереженні (DK-40).
            weighted = int(points * self.item_coefficient + 0.5)

        try:
            ResultZnoService().upsert(
                self.item.id_item_zno, entrant_id, weighted, points_raw=points
            )
            # У таблиці показуємо домножений бал, у діалозі — сирий.
            self.grades_by_entrant[row["id"]] = "" if weighted is None else str(weighted)
            self.raw_by_entrant[row["id"]] = raw
            self.g_grade_original = raw
            self._reload_grading_rows()
            yield rx.toast.success("Оцінку збережено!")
        except Exception:
            yield rx.toast.error("Під час збереження оцінки трапилась помилка. Спробуйте ще раз.")


# ============================================================
# Print
# ============================================================

class PrintEntrantExamState(AppState):
    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANT_EXAM_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return
        # Дозволяємо браузеру намалювати таблицю, потім автоматично відкриваємо діалог друку.
        yield rx.call_script("setTimeout(() => window.print(), 300)")

    @rx.event
    def on_click_back(self):
        return rx.redirect(routes.ENTRANT_EXAM_LIST)

    @rx.event
    def on_click_print(self):
        return rx.call_script("window.print()")
