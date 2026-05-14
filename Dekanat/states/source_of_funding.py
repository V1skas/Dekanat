import reflex as rx

from typing import Sequence, Optional

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


class AddSourceOfFundingState(AppState):
    item: SourceOfFundingModel = SourceOfFundingModel()
    in_process: bool = False

    def _reload_item(self):
        self.item = SourceOfFundingModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_ADD):
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
        self.item.title = value.strip()

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = SourceOfFundingService()
        try:
            self.item = service.add_one(self.item)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SOURCE_OF_FUNDING_LIST)


class EditSourceOfFundingState(AppState):
    item: SourceOfFundingModel = SourceOfFundingModel()
    in_process: bool = True

    def _reload_item(self):
        service = SourceOfFundingService()
        loaded = service.get_by_id(int(self.router.page.params.get("id", -1)))
        if loaded is not None:
            self.item = loaded

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
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value.strip()

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SOURCE_OF_FUNDING_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = SourceOfFundingService()
        try:
            self.item = service.edit_one(self.item)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SOURCE_OF_FUNDING_VIEW + str(self.router.page.params.get("id", "")))


class ViewSourceOfFundingState(AppState):
    item: SourceOfFundingModel = SourceOfFundingModel()
    in_process: bool = True

    def _reload_item(self):
        service = SourceOfFundingService()
        loaded = service.get_by_id(int(self.router.page.params.get("id", -1)))
        if loaded is not None:
            self.item = loaded

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
        if service.delete_one(self.item):
            yield rx.redirect(routes.SOURCE_OF_FUNDING_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""
