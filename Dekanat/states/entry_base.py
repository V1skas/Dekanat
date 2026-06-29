import reflex as rx

from typing import Sequence, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import EntryBaseModel
from Dekanat.services.entry_base import EntryBaseService


class ListEntryBaseState(AppState):
    items: Optional[Sequence[EntryBaseModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRY_BASE_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            service = EntryBaseService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ENTRY_BASE_ADD)


class AddEntryBaseState(AppState):
    item: EntryBaseModel = EntryBaseModel()
    in_process: bool = False

    def _reload_item(self):
        self.item = EntryBaseModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRY_BASE_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self._reload_item()
        self.in_process = False
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def prefix(self) -> str:
        return self.item.prefix if self.item is not None and self.item.prefix is not None else ""

    @rx.event
    def set_prefix(self, value: str):
        self.item.prefix = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRY_BASE_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntryBaseService()
        try:
            self.item = service.add_one(self.item)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ENTRY_BASE_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRY_BASE_LIST)


class EditEntryBaseState(AppState):
    item: EntryBaseModel = EntryBaseModel()
    in_process: bool = True

    def _reload_item(self):
        service = EntryBaseService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRY_BASE_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRY_BASE_LIST)
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
    def prefix(self) -> str:
        return self.item.prefix if self.item is not None and self.item.prefix is not None else ""

    @rx.event
    def set_prefix(self, value: str):
        self.item.prefix = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRY_BASE_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntryBaseService()
        try:
            self.item = service.edit_one(self.item)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ENTRY_BASE_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRY_BASE_VIEW + str(self.item.id))


class ViewEntryBaseState(AppState):
    item: EntryBaseModel = EntryBaseModel()
    in_process: bool = True

    def _reload_item(self):
        service = EntryBaseService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRY_BASE_VIEW):
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
        if not self.has_permission(Actions.ENTRY_BASE_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ENTRY_BASE_EDIT + str(self.item.id))

    @rx.var
    def prefix(self) -> str:
        return self.item.prefix if self.item is not None and self.item.prefix is not None else ""

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRY_BASE_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = EntryBaseService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ENTRY_BASE_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""
