import reflex as rx

from typing import Sequence, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import EntrantGroupModel
from Dekanat.services.entrants_group import EntrantsGroupService


class ListEntrantsGroupState(AppState):
    items: Optional[Sequence[EntrantGroupModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            service = EntrantsGroupService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ENTRANTS_GROUP_ADD)


class AddEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = False

    def _reload_item(self):
        self.item = EntrantGroupModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_ADD):
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
            self.item = service.add_one(self.item)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_LIST)


class EditEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True

    def _reload_item(self):
        service = EntrantsGroupService()
        loaded = service.get_by_id(int(self.router.page.params.get("id", -1)))
        if loaded is not None:
            self.item = loaded

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
            self.item = service.edit_one(self.item)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))


class ViewEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True

    def _reload_item(self):
        service = EntrantsGroupService()
        loaded = service.get_by_id(int(self.router.page.params.get("id", -1)))
        if loaded is not None:
            self.item = loaded

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
