import reflex as rx

from typing import Optional, List, Sequence

from Dekanat.actions import Actions
from Dekanat.models import IdentityDocumentTypeModel
from Dekanat.services.identity_document_type import IdentityDocumentTypeService
from Dekanat.states.app import AppState
from Dekanat import routes

class ListIdentityDocumentTypeState(AppState):
    items: Optional[Sequence[IdentityDocumentTypeModel]] = None
    process_items: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.process_items = True

            service = IdentityDocumentTypeService()
            self.items = service.get_list_items()
            self.process_items = False
            return

        except:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return


    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_ADD)


class AddIdentityDocumentTypeState(AppState):
    item = IdentityDocumentTypeModel()
    in_process = False

    def _reload_item(self):
        self.item = IdentityDocumentTypeModel()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self._reload_item()
        self.in_process = False
        return

    @rx.var
    def title(self) -> str:
        return self.item.title

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

    @rx.event
    def set_description(self, value: str):
        self.item.description = value if value != "" else None

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = IdentityDocumentTypeService()
        try:
            self.item = service.add_one(self.item)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_VIEW+str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_LIST)


class EditIdentityDocumentTypeState(AppState):
    item: IdentityDocumentTypeModel = IdentityDocumentTypeModel()
    in_process = True

    def _reload_item(self):
        service = IdentityDocumentTypeService()
        self.item = service.get_by_id(int(self._route_param("id", "-1")))

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Такого запису не існує!")
            else:
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

    @rx.event
    def set_description(self, value: str):
        self.item.description = value if value != "" else None

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = IdentityDocumentTypeService()
        try:
            self.item = service.edit_one(self.item)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_VIEW+str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_VIEW+str(self._route_param("id", "")))


class ViewIdentityDocumentTypeState(AppState):
    item: IdentityDocumentTypeModel = IdentityDocumentTypeModel()
    in_process = True

    def _reload_item(self):
        service = IdentityDocumentTypeService()
        self.item = service.get_by_id(int(self._route_param("id", "-1")))

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Такого запису не існує!")
                yield rx.redirect(routes.DASHBOARD)
            else:
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_EDIT+str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.IDENTITY_DOCUMENT_TYPE_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = IdentityDocumentTypeService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.IDENTITY_DOCUMENT_TYPE_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item.description is not None else ""

