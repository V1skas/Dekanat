from typing import Optional, Tuple

import reflex as rx

from Dekanat.models import AuthTokenModel, WorkerModel
from Dekanat.services.auth import AuthService
from Dekanat.states.app import AppState
from Dekanat import routes

class AuthState(AppState):
    worker: Optional[WorkerModel] = None
    error_text: Optional[str] = None

    @rx.event
    def on_load(self):
        if self.is_auth:
            return rx.redirect(routes.DASHBOARD)
        self.worker = WorkerModel(login=None, password=None)

    @rx.var
    def login(self) -> str:
        return self.worker.login if self.worker is not None and self.worker.login is not None else ""

    @rx.var
    def password(self) -> str:
        return self.worker.password if self.worker is not None and self.worker.password is not None else ""

    @rx.event
    def on_change_login(self, value: str):
        self.error_text = None
        self.worker.login = value if value != "" else None

    @rx.event
    def on_change_password(self, value: str):
        self.error_text = None
        self.worker.password = value if value != "" else None

    @rx.event
    def on_auth(self):
        if self.worker.login is None or self.worker.password is None:
            self.error_text = "Заповніть поля логіну та пароля."
            return

        self.error_text = None

        result: Optional[Tuple[WorkerModel, AuthTokenModel]] = self._auth_service.auth(self.worker.login, self.worker.password)
        if result is None:
            self.error_text = "Помилка авторизації! Невірний логін або пароль."
            return

        self.worker, self.auth_token = result
        self.token = self.auth_token.token

        self.actions_worker = list(self._auth_service.get_list_worker_actions(self.worker.id))

        return rx.redirect(routes.DASHBOARD)
