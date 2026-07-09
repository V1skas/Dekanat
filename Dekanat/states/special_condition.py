import reflex as rx

from typing import Optional, Sequence

from Dekanat.actions import Actions
from Dekanat.models import SpecialConditionModel
from Dekanat.services.special_condition import SpecialConditionService
from Dekanat.states.app import AppState
from Dekanat import routes


class ListSpecialConditionState(AppState):
    items: Optional[Sequence[SpecialConditionModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True

            service = SpecialConditionService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.SPECIAL_CONDITION_ADD)


class AddSpecialConditionState(AppState):
    item: SpecialConditionModel = SpecialConditionModel()
    in_process: bool = False

    def _reload_item(self):
        self.item = SpecialConditionModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self._reload_item()
        self.in_process = False
        return

    @rx.var
    def subcategory_code(self) -> str:
        return self.item.subcategory_code if self.item.subcategory_code is not None else ""

    @rx.event
    def set_subcategory_code(self, value: str):
        self.item.subcategory_code = value

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

    @rx.event
    def set_description(self, value: str):
        self.item.description = value if value != "" else None

    @rx.var
    def is_kvota(self) -> bool:
        return bool(self.item.is_kvota)

    @rx.event
    def set_is_kvota(self, value: bool):
        self.item.is_kvota = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.subcategory_code or self.item.subcategory_code == "":
            yield rx.toast.warning("Поле коду підкатегорії повинно бути заповненим!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = SpecialConditionService()
        try:
            self.item = service.add_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.SPECIAL_CONDITION_VIEW + str(self.item.subcategory_code))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SPECIAL_CONDITION_LIST)


class EditSpecialConditionState(AppState):
    item: SpecialConditionModel = SpecialConditionModel()
    in_process: bool = True

    def _reload_item(self):
        service = SpecialConditionService()
        loaded = service.get_by_code(str(self._route_param("code", "")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.SPECIAL_CONDITION_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def subcategory_code(self) -> str:
        return self.item.subcategory_code if self.item.subcategory_code is not None else ""

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

    @rx.event
    def set_description(self, value: str):
        self.item.description = value if value != "" else None

    @rx.var
    def is_kvota(self) -> bool:
        return bool(self.item.is_kvota)

    @rx.event
    def set_is_kvota(self, value: bool):
        self.item.is_kvota = value

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = SpecialConditionService()
        try:
            self.item = service.edit_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.SPECIAL_CONDITION_VIEW + str(self.item.subcategory_code))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SPECIAL_CONDITION_VIEW + str(self._route_param("code", "")))


class ViewSpecialConditionState(AppState):
    item: SpecialConditionModel = SpecialConditionModel()
    in_process: bool = True

    def _reload_item(self):
        service = SpecialConditionService()
        loaded = service.get_by_code(str(self._route_param("code", "")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_VIEW):
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
        if not self.has_permission(Actions.SPECIAL_CONDITION_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.SPECIAL_CONDITION_EDIT + str(self.item.subcategory_code))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.SPECIAL_CONDITION_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = SpecialConditionService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(routes.SPECIAL_CONDITION_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def subcategory_code(self) -> str:
        return self.item.subcategory_code if self.item.subcategory_code is not None else ""

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item.title is not None else ""

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

    @rx.var
    def is_kvota(self) -> bool:
        return bool(self.item.is_kvota)
