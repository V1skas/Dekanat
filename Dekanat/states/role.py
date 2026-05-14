import reflex as rx

from typing import List, Sequence

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import ActionModel, RoleModel
from Dekanat.services.role import RoleService
from Dekanat.services.action import ActionService


class ListRoleState(AppState):
    items: Sequence[RoleModel] = []
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ROLE_LIST):
            yield rx.redirect(routes.DASHBOARD)
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            return

        try:
            self.in_progress = True
            service = RoleService()
            self.items = service.get_list_items()
            self.in_progress = False
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка. Спробуйте ще раз.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ROLES_ADD)


class AddRoleState(AppState):
    title: str = ""
    description: str = ""
    all_actions: Sequence[ActionModel] = []
    selected_action_ids: List[int] = []
    in_process: bool = True

    def _reload(self):
        service = ActionService()
        self.all_actions = service.get_list_items()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ROLE_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self.title = ""
        self.description = ""
        self.selected_action_ids = []
        try:
            self._reload()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def set_title(self, value: str):
        self.title = value.strip()

    @rx.event
    def set_description(self, value: str):
        self.description = value.strip()

    @rx.event
    def toggle_action(self, action_id: int):
        if action_id in self.selected_action_ids:
            self.selected_action_ids = [a for a in self.selected_action_ids if a != action_id]
        else:
            self.selected_action_ids = self.selected_action_ids + [action_id]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ROLE_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        if len(self.selected_action_ids) == 0:
            yield rx.toast.warning("Роль не може не містити прав!")
            return

        service = RoleService()
        try:
            new_id = service.add_one(self.title, self.description or None, self.selected_action_ids)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ROLES_VIEW+str(new_id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ROLES_LIST)


class EditRoleState(AppState):
    role_id: int = 0
    title: str = ""
    description: str = ""
    all_actions: Sequence[ActionModel] = []
    selected_action_ids: List[int] = []
    in_process: bool = True

    def _reload(self):
        role_service = RoleService()
        action_service = ActionService()
        role = role_service.get_by_id(int(self.router.page.params.get("id", -1)))
        if role is None:
            self.role_id = 0
            return
        self.role_id = role.id
        self.title = role.title
        self.description = role.description or ""
        self.selected_action_ids = [a.id for a in (role.actions or [])]
        self.all_actions = action_service.get_list_items()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ROLE_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload()
            if self.role_id == 0:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ROLES_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")
        return

    @rx.event
    def set_title(self, value: str):
        self.title = value.strip()

    @rx.event
    def set_description(self, value: str):
        self.description = value.strip()

    @rx.event
    def toggle_action(self, action_id: int):
        if action_id in self.selected_action_ids:
            self.selected_action_ids = [a for a in self.selected_action_ids if a != action_id]
        else:
            self.selected_action_ids = self.selected_action_ids + [action_id]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ROLE_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        if len(self.selected_action_ids) == 0:
            yield rx.toast.warning("Роль не може не містити прав!")
            return

        service = RoleService()
        try:
            ok = service.edit_one(self.role_id, self.title, self.description or None, self.selected_action_ids)
            if not ok:
                yield rx.toast.error("Запис не знайдено!")
                return
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ROLES_VIEW+str(self.role_id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ROLES_VIEW+str(self.role_id))


class ViewRoleState(AppState):
    item: RoleModel = RoleModel(actions=[])
    in_process: bool = True

    def _reload_item(self):
        service = RoleService()
        loaded = service.get_by_id(int(self.router.page.params.get("id", -1)))
        if loaded is not None:
            self.item = loaded
        else:
            self.item = None  # type: ignore

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ROLE_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ROLES_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None else ""

    @rx.var
    def description(self) -> str:
        return self.item.description if self.item is not None and self.item.description is not None else ""

    @rx.var
    def actions(self) -> List[ActionModel]:
        return self.item.actions if self.item is not None and self.item.actions is not None else []

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ROLE_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ROLES_EDIT+str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ROLE_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = RoleService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ROLES_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return
