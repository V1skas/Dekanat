import reflex as rx

from typing import Sequence, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import KinshipModel
from Dekanat.services.kinship import KinshipService

class ListKinshipState(AppState):
    items: Optional[Sequence[KinshipModel]]
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.KINSHIP_LIST):
            yield rx.redirect(routes.DASHBOARD)
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            return

        try:
            self.in_progress = True

            service = KinshipService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.KINSHIP_ADD)


class AddKinshipState(AppState):
    item = KinshipModel()
    in_process = False

    def _reload_item(self):
        self.item = KinshipModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.KINSHIP_ADD):
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
        if not self.has_permission(Actions.KINSHIP_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = KinshipService()
        try:
            self.item = service.add_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.KINSHIP_VIEW+str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.KINSHIP_LIST)


class EditKinshipState(AppState):
    item: KinshipModel = KinshipModel()
    in_process = False

    def _reload_item(self):
        service = KinshipService()
        loaded = service.get_by_id(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.KINSHIP_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.KINSHIP_LIST)
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
        if not self.has_permission(Actions.KINSHIP_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = KinshipService()
        try:
            self.item = service.edit_one(self.item, actor_id=self._actor_id())
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.KINSHIP_VIEW+str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.KINSHIP_VIEW+str(self.item.id))


class ViewKinshipState(AppState):
    item: KinshipModel = KinshipModel()
    in_process = True

    def _reload_item(self):
        service = KinshipService()
        self.item = service.get_by_id(int(self._route_param("id", "-1")))

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.KINSHIP_VIEW):
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
        if not self.has_permission(Actions.KINSHIP_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.KINSHIP_EDIT+str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.KINSHIP_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = KinshipService()
        if service.delete_one(self.item, actor_id=self._actor_id()):
            yield rx.redirect(routes.KINSHIP_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""
