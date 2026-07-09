import reflex as rx

from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import SourceOfFundingModel
from Dekanat.services.source_of_funding import SourceOfFundingService


class ListSourceOfFundingState(AppState):
    items: Optional[Sequence[SourceOfFundingModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True

            service = SourceOfFundingService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.SOURCE_OF_FUNDING_ADD)


class _SourceOfFundingFormBase(AppState):
    """Спільний код для форм: sequence/color/eligibility (DK-52)."""

    item: SourceOfFundingModel = SourceOfFundingModel()
    # Інші активні ресурси (крім цього) — для вибору "також бере участь у конкурсі...".
    other_resource_options: List[Dict[str, str]] = []
    # Обрані id ресурсів (рядками) — сортуються лише "вперед" (sequence більший за свій).
    eligible_ids: List[str] = []

    def _load_other_resources(self):
        items = SourceOfFundingService().get_list_items()
        self.other_resource_options = [
            {"value": str(r.id), "label": r.title, "sequence": str(r.sequence)}
            for r in items
            if r.id != self.item.id
        ]

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def sequence_str(self) -> str:
        return str(self.item.sequence) if self.item is not None and self.item.sequence is not None else "0"

    @rx.event
    def set_sequence(self, value: str):
        try:
            self.item.sequence = int(value) if value else 0
        except (ValueError, TypeError):
            self.item.sequence = 0

    @rx.var
    def color(self) -> str:
        return self.item.color if self.item is not None and self.item.color else "#22c55e"

    @rx.event
    def set_color(self, value: str):
        self.item.color = value

    @rx.event
    def toggle_eligible(self, id_str: str):
        if id_str in self.eligible_ids:
            self.eligible_ids = [i for i in self.eligible_ids if i != id_str]
        else:
            self.eligible_ids = self.eligible_ids + [id_str]

    def _validate_eligibility(self) -> Optional[str]:
        seq_by_id = {opt["value"]: int(opt["sequence"]) for opt in self.other_resource_options}
        for id_str in self.eligible_ids:
            target_seq = seq_by_id.get(id_str)
            if target_seq is not None and target_seq <= (self.item.sequence or 0):
                return "Можна обирати лише ресурси з вищим пріоритетом (більшим числом послідовності)!"
        return None


class AddSourceOfFundingState(_SourceOfFundingFormBase):
    in_process: bool = False

    def _reload_item(self):
        self.item = SourceOfFundingModel()
        self.eligible_ids = []

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self._reload_item()
        self._load_other_resources()
        self.in_process = False
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        err = self._validate_eligibility()
        if err:
            yield rx.toast.warning(err)
            return

        service = SourceOfFundingService()
        try:
            eligible_ids = [int(i) for i in self.eligible_ids]
            self.item = service.add_one(self.item, eligible_ids=eligible_ids, actor_id=self._actor_id())
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SOURCE_OF_FUNDING_LIST)


class EditSourceOfFundingState(_SourceOfFundingFormBase):
    in_process: bool = True

    def _reload_item(self):
        service = SourceOfFundingService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded
            self.eligible_ids = [str(i) for i in service.get_eligible_ids(loaded.id)]

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.SOURCE_OF_FUNDING_LIST)
                return
            self._load_other_resources()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        err = self._validate_eligibility()
        if err:
            yield rx.toast.warning(err)
            return

        service = SourceOfFundingService()
        try:
            eligible_ids = [int(i) for i in self.eligible_ids]
            self.item = service.edit_one(self.item, eligible_ids=eligible_ids, actor_id=self._actor_id())
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self._route_param("id", "")))


class ViewSourceOfFundingState(AppState):
    item: SourceOfFundingModel = SourceOfFundingModel()
    eligible_titles: List[str] = []
    in_process: bool = True

    def _reload_item(self):
        service = SourceOfFundingService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded
            eligible_ids = set(service.get_eligible_ids(loaded.id))
            self.eligible_titles = [
                r.title for r in service.get_list_items() if r.id in eligible_ids
            ]

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_VIEW):
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

    @rx.var
    def eligible_titles_str(self) -> str:
        return ", ".join(self.eligible_titles) if self.eligible_titles else "—"

    @rx.var
    def sequence_str(self) -> str:
        return str(self.item.sequence) if self.item is not None and self.item.sequence is not None else "0"

    @rx.var
    def color(self) -> str:
        return self.item.color if self.item is not None and self.item.color else "#22c55e"

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.SOURCE_OF_FUNDING_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = SourceOfFundingService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(routes.SOURCE_OF_FUNDING_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""
