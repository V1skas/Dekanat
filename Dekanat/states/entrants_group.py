import reflex as rx

from datetime import datetime
from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import EntrantGroupModel, EntrantModel, EntrantExamModel, AdmissionCampaignModel
from Dekanat.services.entrants_group import EntrantsGroupService
from Dekanat.services.admission_campaign import AdmissionCampaignService


# ---------- List page ----------

class ListEntrantsGroupState(AppState):
    items: Optional[Sequence[EntrantGroupModel]] = None
    in_progress: bool = True

    # Стан панелі фільтрів
    filter_open: bool = False
    filter_title: str = ""
    filter_campaign_id: int = 0  # 0 — без фільтра по кампанії
    campaigns: List[AdmissionCampaignModel] = []

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

    def _reload_items(self):
        service = EntrantsGroupService()
        self.items = service.get_list_items(
            title=self.filter_title.strip() or None,
            created_between=self._campaign_range(),
        )

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
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
        return rx.redirect(routes.ENTRANTS_GROUP_ADD)

    # --- filter panel ---

    @rx.event
    def toggle_filter(self):
        self.filter_open = not self.filter_open

    @rx.event
    def set_filter_title(self, value: str):
        self.filter_title = value
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
        self.filter_title = ""
        self.filter_campaign_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False


# ---------- Form state helpers ----------

def _entrant_to_row(e: EntrantModel) -> Dict[str, str]:
    return {
        "value": str(e.id),
        "label": e.person.pib if e.person is not None else f"Абітурієнт #{e.id}",
        "subtitle": e.person.phone_number if (e.person is not None and e.person.phone_number) else "",
    }


def _filter_assignable(entrants: List[EntrantModel], chosen_ids: set, query: str) -> List[Dict[str, str]]:
    """Кандидати на додавання: доступні мінус уже обрані, з пошуком за ПІБ/телефоном."""
    avail = [e for e in entrants if e.id not in chosen_ids]
    q = (query or "").lower().strip()
    if q:
        def _hit(e: EntrantModel) -> bool:
            if e.person is None:
                return False
            pib = (e.person.pib or "").lower()
            phone = (e.person.phone_number or "").lower()
            return q in pib or q in phone
        avail = [e for e in avail if _hit(e)]
    return [_entrant_to_row(e) for e in avail]


# ---------- Add page ----------

class AddEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = False

    # Список абітурієнтів, які належатимуть до групи (поки що тільки в пам'яті форми).
    entrants_in_group: List[EntrantModel] = []
    # Усі абітурієнти, доступні для додавання (вільні від інших груп).
    assignable_entrants: List[EntrantModel] = []

    add_entrant_dialog_open: bool = False
    add_entrant_dialog_search: str = ""

    def _reload_item(self):
        self.item = EntrantGroupModel()
        self.entrants_in_group = []
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""
        service = EntrantsGroupService()
        self.assignable_entrants = list(service.get_assignable_entrants(None))

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    # --- entrants management ---

    @rx.var
    def available_to_add_rows(self) -> List[Dict[str, str]]:
        return _filter_assignable(
            self.assignable_entrants,
            {e.id for e in self.entrants_in_group},
            self.add_entrant_dialog_search,
        )

    @rx.event
    def set_add_entrant_dialog_search(self, value: str):
        self.add_entrant_dialog_search = value

    @rx.event
    def open_add_entrant_dialog(self):
        self.add_entrant_dialog_search = ""
        self.add_entrant_dialog_open = True

    @rx.event
    def close_add_entrant_dialog(self):
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def pick_entrant_to_add(self, entrant_id_str: str):
        try:
            eid = int(entrant_id_str)
        except (ValueError, TypeError):
            return
        match = next((e for e in self.assignable_entrants if e.id == eid), None)
        if match is None:
            return
        if any(e.id == match.id for e in self.entrants_in_group):
            return
        self.entrants_in_group.append(match)
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def remove_entrant_from_group(self, index: int):
        if 0 <= index < len(self.entrants_in_group):
            del self.entrants_in_group[index]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntrantsGroupService()
        try:
            entrant_ids = [e.id for e in self.entrants_in_group]
            self.item = service.add_one(self.item, entrant_ids=entrant_ids)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_LIST)


# ---------- Edit page ----------

class EditEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True

    entrants_in_group: List[EntrantModel] = []
    assignable_entrants: List[EntrantModel] = []

    add_entrant_dialog_open: bool = False
    add_entrant_dialog_search: str = ""

    def _reload_item(self):
        service = EntrantsGroupService()
        group_id = int(self._route_param("id", "-1"))
        loaded = service.get_by_id(group_id)
        if loaded is not None:
            self.item = loaded
            self.entrants_in_group = list(service.get_entrants(loaded.id))
            self.assignable_entrants = list(service.get_assignable_entrants(loaded.id))
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def available_to_add_rows(self) -> List[Dict[str, str]]:
        return _filter_assignable(
            self.assignable_entrants,
            {e.id for e in self.entrants_in_group},
            self.add_entrant_dialog_search,
        )

    @rx.event
    def set_add_entrant_dialog_search(self, value: str):
        self.add_entrant_dialog_search = value

    @rx.event
    def open_add_entrant_dialog(self):
        self.add_entrant_dialog_search = ""
        self.add_entrant_dialog_open = True

    @rx.event
    def close_add_entrant_dialog(self):
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def pick_entrant_to_add(self, entrant_id_str: str):
        try:
            eid = int(entrant_id_str)
        except (ValueError, TypeError):
            return
        match = next((e for e in self.assignable_entrants if e.id == eid), None)
        if match is None:
            return
        if any(e.id == match.id for e in self.entrants_in_group):
            return
        self.entrants_in_group.append(match)
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def remove_entrant_from_group(self, index: int):
        if 0 <= index < len(self.entrants_in_group):
            del self.entrants_in_group[index]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntrantsGroupService()
        try:
            entrant_ids = [e.id for e in self.entrants_in_group]
            self.item = service.edit_one(self.item, entrant_ids=entrant_ids)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))


# ---------- View page ----------

class ViewEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True

    entrants_in_group: List[EntrantModel] = []
    exams: List[EntrantExamModel] = []
    # Передзібрані рядки для таблиці іспитів: дата відформатована на сервері,
    # бо у Var[datetime] немає зручного локалізованого форматування на фронті.
    exams_display: List[Dict[str, str]] = []

    def _reload_item(self):
        service = EntrantsGroupService()
        group_id = int(self._route_param("id", "-1"))
        loaded = service.get_by_id(group_id)
        if loaded is not None:
            self.item = loaded
            self.entrants_in_group = list(service.get_entrants(loaded.id))
            self.exams = list(service.get_exams(loaded.id))
            self.exams_display = [
                {
                    "subject": (e.item_zno.title if e.item_zno is not None else "—"),
                    "date_time": f"{e.date} {e.time_start}—{e.time_end}" if e.date else "—",
                }
                for e in self.exams
            ]

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_VIEW):
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
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ENTRANTS_GROUP_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = EntrantsGroupService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""
