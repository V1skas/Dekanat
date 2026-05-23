import reflex as rx

from typing import List, Sequence

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import ActionModel, RoleModel, WorkerModel
from Dekanat.services.worker import WorkerService
from Dekanat.services.role import RoleService
from Dekanat.services.action import ActionService


class ListWorkerState(AppState):
    items: Sequence[WorkerModel] = []
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.WORKER_LIST):
            yield rx.redirect(routes.DASHBOARD)
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            return

        try:
            self.in_progress = True
            service = WorkerService()
            self.items = service.get_list_items()
            self.in_progress = False
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка. Спробуйте ще раз.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.WORKERS_ADD)


class AddWorkerState(AppState):
    pib: str = ""
    login: str = ""
    password: str = ""
    phone_number: str = ""
    email: str = ""
    photo: str = ""

    all_roles: Sequence[RoleModel] = []
    selected_role_ids: List[int] = []

    all_actions: Sequence[ActionModel] = []
    selected_action_ids: List[int] = []

    in_process: bool = True

    def _reload(self):
        self.all_roles = RoleService().get_list_items()
        self.all_actions = ActionService().get_list_items()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.WORKER_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        self.pib = ""
        self.login = ""
        self.password = ""
        self.phone_number = ""
        self.email = ""
        self.photo = ""
        self.selected_role_ids = []
        self.selected_action_ids = []
        try:
            self._reload()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def set_pib(self, value: str):
        self.pib = value

    @rx.event
    def set_login(self, value: str):
        self.login = value

    @rx.event
    def set_password(self, value: str):
        self.password = value

    @rx.event
    def set_phone_number(self, value: str):
        self.phone_number = value

    @rx.event
    def set_email(self, value: str):
        self.email = value

    @rx.event
    def set_photo(self, value: str):
        self.photo = value

    @rx.event
    def toggle_role(self, role_id: int):
        if role_id in self.selected_role_ids:
            self.selected_role_ids = [r for r in self.selected_role_ids if r != role_id]
        else:
            self.selected_role_ids = self.selected_role_ids + [role_id]

    @rx.event
    def toggle_action(self, action_id: int):
        if action_id in self.selected_action_ids:
            self.selected_action_ids = [a for a in self.selected_action_ids if a != action_id]
        else:
            self.selected_action_ids = self.selected_action_ids + [action_id]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.WORKER_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.pib == "":
            yield rx.toast.warning("Поле ПІБ повинно бути заповненим!")
            return

        if self.login == "":
            yield rx.toast.warning("Поле логіну повинно бути заповненим!")
            return

        if self.password == "":
            yield rx.toast.warning("Поле паролю повинно бути заповненим!")
            return

        service = WorkerService()
        try:
            if service.is_login_taken(self.login):
                yield rx.toast.warning("Користувач з таким логіном вже існує!")
                return

            new_id = service.add_one(
                pib=self.pib,
                login=self.login,
                password=self.password,
                phone_number=self.phone_number or None,
                email=self.email or None,
                photo=self.photo or None,
                role_ids=self.selected_role_ids,
                action_ids=self.selected_action_ids,
            )
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.WORKERS_VIEW+str(new_id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.WORKERS_LIST)


class EditWorkerState(AppState):
    worker_id: int = 0
    pib: str = ""
    login: str = ""
    password: str = ""
    phone_number: str = ""
    email: str = ""
    photo: str = ""

    all_roles: Sequence[RoleModel] = []
    selected_role_ids: List[int] = []

    all_actions: Sequence[ActionModel] = []
    selected_action_ids: List[int] = []

    in_process: bool = True

    def _reload(self):
        worker = WorkerService().get_by_id_full(int(self._route_param("id", "-1")))
        if worker is None:
            self.worker_id = 0
            return
        self.worker_id = worker.id
        self.pib = worker.pib
        self.login = worker.login
        self.password = ""
        self.phone_number = worker.phone_number or ""
        self.email = worker.email or ""
        self.photo = worker.photo or ""
        self.selected_role_ids = [r.id for r in (worker.roles or [])]
        self.selected_action_ids = [a.id for a in (worker.actions or [])]
        self.all_roles = RoleService().get_list_items()
        self.all_actions = ActionService().get_list_items()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.WORKER_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload()
            if self.worker_id == 0:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.WORKERS_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")
        return

    @rx.event
    def set_pib(self, value: str):
        self.pib = value

    @rx.event
    def set_login(self, value: str):
        self.login = value

    @rx.event
    def set_password(self, value: str):
        self.password = value

    @rx.event
    def set_phone_number(self, value: str):
        self.phone_number = value

    @rx.event
    def set_email(self, value: str):
        self.email = value

    @rx.event
    def set_photo(self, value: str):
        self.photo = value

    @rx.event
    def toggle_role(self, role_id: int):
        if role_id in self.selected_role_ids:
            self.selected_role_ids = [r for r in self.selected_role_ids if r != role_id]
        else:
            self.selected_role_ids = self.selected_role_ids + [role_id]

    @rx.event
    def toggle_action(self, action_id: int):
        if action_id in self.selected_action_ids:
            self.selected_action_ids = [a for a in self.selected_action_ids if a != action_id]
        else:
            self.selected_action_ids = self.selected_action_ids + [action_id]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.WORKER_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.pib == "":
            yield rx.toast.warning("Поле ПІБ повинно бути заповненим!")
            return

        if self.login == "":
            yield rx.toast.warning("Поле логіну повинно бути заповненим!")
            return

        service = WorkerService()
        try:
            if service.is_login_taken(self.login, exclude_id=self.worker_id):
                yield rx.toast.warning("Користувач з таким логіном вже існує!")
                return

            ok = service.edit_one(
                id=self.worker_id,
                pib=self.pib,
                login=self.login,
                password=self.password or None,
                phone_number=self.phone_number or None,
                email=self.email or None,
                photo=self.photo or None,
                role_ids=self.selected_role_ids,
                action_ids=self.selected_action_ids,
            )
            if not ok:
                yield rx.toast.error("Запис не знайдено!")
                return
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.WORKERS_VIEW+str(self.worker_id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.WORKERS_VIEW+str(self.worker_id))


class ViewWorkerState(AppState):
    item: WorkerModel = WorkerModel(login="", password="", password_salt="", pib="", roles=[], actions=[])
    in_process: bool = True

    def _reload_item(self):
        loaded = WorkerService().get_by_id_full(int(self._route_param("id", "-1")))
        if loaded is not None:
            self.item = loaded
        else:
            self.item = None  # type: ignore

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.WORKER_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.WORKERS_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def pib(self) -> str:
        return self.item.pib if self.item is not None else ""

    @rx.var
    def login(self) -> str:
        return self.item.login if self.item is not None else ""

    @rx.var
    def phone_number(self) -> str:
        return self.item.phone_number if self.item is not None and self.item.phone_number is not None else ""

    @rx.var
    def email(self) -> str:
        return self.item.email if self.item is not None and self.item.email is not None else ""

    @rx.var
    def photo(self) -> str:
        return self.item.photo if self.item is not None and self.item.photo is not None else ""

    @rx.var
    def roles(self) -> List[RoleModel]:
        return self.item.roles if self.item is not None and self.item.roles is not None else []

    @rx.var
    def actions(self) -> List[ActionModel]:
        return self.item.actions if self.item is not None and self.item.actions is not None else []

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.WORKER_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.WORKERS_EDIT+str(self.item.id))

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.WORKER_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = WorkerService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.WORKERS_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return
