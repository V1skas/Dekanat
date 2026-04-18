from typing import Optional, List

import reflex as rx

from Dekanat import routes

from Dekanat.services.auth import AuthService, WorkerModel, AuthTokenModel
from Dekanat.dao.worker import WorkerDao
from Dekanat.actions import Actions


class AppState(rx.State):
    _auth_service: AuthService = AuthService()
    
    worker: Optional[WorkerModel] = None
    actions_worker: Optional[List[str]] = None
    auth_token: Optional[AuthTokenModel] = None
    token: str = rx.Cookie(name="auth_token")

    page_title: str = "Головна"
    sidebar_open: bool = True

    def toggle_sidebar(self):
        """Инвертирует состояние панели (открыто/закрыто)"""
        self.sidebar_open = not self.sidebar_open

    def has_permission(self, action: Actions) -> bool:
        try:
            if not self.worker:
                self.worker = WorkerDao.get_by_id(self.auth_token.id_worker)
            if not self.actions_worker:
                self.actions_worker = self._auth_service.get_list_worker_actions(self.worker.id)
            return action.value in self.actions_worker
        except Exception as e:
            print(f"[AppState][has_permission][ERROR] {e}")
            return False

    @rx.var
    def is_auth(self) -> bool:
        try:
            if self.auth_token:
                return True

            if self.token == "":
                return False
            
            self.auth_token = self._auth_service.get_auth_token(self.token)

            if self.auth_token is None:
                return False
            else:
                return True
        except Exception as e:
            print(f"[AppState][is_auth][ERROR] {e}")
            return False
        
    @rx.var
    def worker_pib(self) -> str:
        try:
            if not self.is_auth:
                return "Not Auth"
            if self.worker and self.worker.pib:
                return self.worker.pib
            self.worker = WorkerDao.get_by_id(self.auth_token.id_worker)
            return self.worker.pib if self.worker and self.worker.pib else ""
        except Exception as e:
            print(f"[AppState][worker_pib][ERROR] {e}")
            return "Not Auth"
        
    @rx.event
    def logout(self):
        try:
            self._auth_service.logout(self.auth_token)
            yield rx.redirect(routes.LOGIN)
            self.worker = None
            self.auth_token = None
            self.actions_worker = None
            rx.remove_cookie("auth_token")
        except Exception as e:
            print(f"[AppState][logout][ERROR] {e}")
            return
