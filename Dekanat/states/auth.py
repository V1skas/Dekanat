from typing import Optional, Tuple

import reflex as rx

from Dekanat.models import WorkerModel
from Dekanat.states.app import AppState


class AuthState(AppState):
    worker: WorkerModel = WorkerModel(login=None, password=None)
    error_text: Optional[str] = None

    @rx.event
    def on_load(self):
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
            self.error_text = "Заповніть поля логіну та поролю."
            return
        
        self.error_text = None

        result: Optional[Tuple[WorkerModel, str]] = self._auth_service.auth(self.worker.login, self.worker.password)
        if result is None:
            self.error_text = "Помилка авторизації! Невірний логін або пароль."
            return
        
        self.worker, self.auth_token = result
        self.token = self.auth_token.token
