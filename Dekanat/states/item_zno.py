import reflex as rx

from typing import Sequence, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import ItemZnoModel
from Dekanat.services.item_zno import ItemZnoService


class ListItemZnoState(AppState):
    items: Optional[Sequence[ItemZnoModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ITEM_ZNO_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            service = ItemZnoService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ITEM_ZNO_ADD)


class AddItemZnoState(AppState):
    item: ItemZnoModel = ItemZnoModel()
    in_process: bool = False

    def _reload_item(self):
        self.item = ItemZnoModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ITEM_ZNO_ADD):
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
    def coefficient_str(self) -> str:
        return (
            str(self.item.coefficient)
            if self.item is not None and self.item.coefficient is not None
            else "1"
        )

    @rx.event
    def set_coefficient(self, value: str):
        try:
            self.item.coefficient = float(value.replace(",", ".")) if value else 0.0
        except (ValueError, TypeError):
            self.item.coefficient = 0.0

    @rx.var
    def is_counted_in_rating(self) -> bool:
        return bool(self.item.is_counted_in_rating) if self.item is not None else False

    @rx.event
    def set_is_counted_in_rating(self, value: bool):
        self.item.is_counted_in_rating = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ITEM_ZNO_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return
        if self.item.coefficient is None or self.item.coefficient <= 0:
            yield rx.toast.warning("Коефіцієнт має бути додатним числом!")
            return

        service = ItemZnoService()
        try:
            self.item = service.add_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ITEM_ZNO_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ITEM_ZNO_LIST)


class EditItemZnoState(AppState):
    item: ItemZnoModel = ItemZnoModel()
    in_process: bool = True

    def _reload_item(self):
        service = ItemZnoService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ITEM_ZNO_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ITEM_ZNO_LIST)
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
    def coefficient_str(self) -> str:
        return (
            str(self.item.coefficient)
            if self.item is not None and self.item.coefficient is not None
            else "1"
        )

    @rx.event
    def set_coefficient(self, value: str):
        try:
            self.item.coefficient = float(value.replace(",", ".")) if value else 0.0
        except (ValueError, TypeError):
            self.item.coefficient = 0.0

    @rx.var
    def is_counted_in_rating(self) -> bool:
        return bool(self.item.is_counted_in_rating) if self.item is not None else False

    @rx.event
    def set_is_counted_in_rating(self, value: bool):
        self.item.is_counted_in_rating = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ITEM_ZNO_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return
        if self.item.coefficient is None or self.item.coefficient <= 0:
            yield rx.toast.warning("Коефіцієнт має бути додатним числом!")
            return

        service = ItemZnoService()
        try:
            self.item = service.edit_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ITEM_ZNO_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ITEM_ZNO_VIEW + str(self.item.id))


class ViewItemZnoState(AppState):
    item: ItemZnoModel = ItemZnoModel()
    in_process: bool = True

    def _reload_item(self):
        service = ItemZnoService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ITEM_ZNO_VIEW):
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
        if not self.has_permission(Actions.ITEM_ZNO_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ITEM_ZNO_EDIT + str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ITEM_ZNO_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = ItemZnoService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(routes.ITEM_ZNO_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.var
    def coefficient_str(self) -> str:
        return (
            str(self.item.coefficient)
            if self.item is not None and self.item.coefficient is not None
            else "1"
        )

    @rx.var
    def is_counted_in_rating(self) -> bool:
        return bool(self.item.is_counted_in_rating) if self.item is not None else False
