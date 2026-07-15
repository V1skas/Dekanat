from typing import Optional, List

import reflex as rx

from Dekanat import routes

from Dekanat.services.auth import AuthService, WorkerModel, AuthTokenModel
from Dekanat.services.worker import WorkerService
from Dekanat.services.app_update import AppUpdateService
from Dekanat.actions import Actions
from Dekanat.declared.submenu import SECTION_TITLES


class AppState(rx.State):
    _auth_service: AuthService = AuthService()

    worker: Optional[WorkerModel]
    actions_worker: List[str]
    # Cookie живе до 30 днів; реальне закінчення сесії контролюється серверним
    # AuthTokenModel.expires_at (ковзне вікно з налаштування session_timeout_minutes).
    token: str = rx.Cookie(name="auth_token", max_age=60*60*24*30, same_site="lax", path="/")
    auth_token: Optional[AuthTokenModel]
    # Кеш версії прав воркера — для звірки із актуальною у БД (DK-21).
    permissions_version_seen: int = 0

    # Маркер непрочитаного оновлення (DK-32) — спільний для всіх підстейтів
    # (оголошений лише тут; ChangelogState скидає його при відкритті вікна).
    has_unread_update: bool = False
    # Тост «систему оновлено» показуємо не частіше одного разу за сесію.
    update_notice_shown: bool = False
    # Кеш MAX(id) app_updates — читаємо раз за сесію (оновлення виходять на релізі).
    latest_update_id_cache: int = -1

    page_title: str = "Головна"
    sidebar_open: bool = True
    expanded_groups: List[str] = []
    user_menu_open: bool = False

    def toggle_sidebar(self):
        """Инвертирует состояние панели (открыто/закрыто)"""
        self.sidebar_open = not self.sidebar_open

    def toggle_group(self, group_key: str):
        if group_key in self.expanded_groups:
            self.expanded_groups = [g for g in self.expanded_groups if g != group_key]
        else:
            self.expanded_groups = self.expanded_groups + [group_key]

    @rx.event
    def set_user_menu_open(self, value: bool):
        self.user_menu_open = value

    def _actor_id(self) -> Optional[int]:
        """Id залогіненого воркера для журналу дій (DK-55). None — якщо сесія без
        воркера (не має ставатись у мутуючих обробниках: там спершу йде перевірка прав)."""
        return self.worker.id if self.worker is not None else None

    def has_permission(self, action: Actions) -> bool:
        try:
            if not self.is_auth:
                raise Exception()
            if self.worker is None:
                service = WorkerService()
                self.worker = service.get_by_id(self.auth_token.id_worker)
            if not self.actions_worker:
                self.actions_worker = self._auth_service.get_list_worker_actions(self.worker.id)
            return action.value in self.actions_worker
        except Exception as e:
            print(f"[AppState][has_permission][ERROR] {e}")
            return False

    @rx.var
    def is_auth(self) -> bool:
        try:
            if self.auth_token is not None:
                return True
            return False 
        except Exception as e:
            print(f"[AppState][is_auth][ERROR] {e}")
            return False

    @rx.event
    def require_auth(self):
        if not self.token:
            yield rx.redirect(routes.LOGIN)
            return

        # На кожному виклику тягнемо токен з БД — get_auth_token попутно:
        #   * чистить протерміновані токени;
        #   * перевіряє expires_at цього токена;
        #   * продовжує ковзне вікно (touch).
        # None означає: токен невалідний або протермінований — розлогуємось.
        token = self._auth_service.get_auth_token(self.token)
        if token is None:
            yield AppState.logout
            return

        first_load = self.auth_token is None
        self.auth_token = token

        if first_load or self.worker is None:
            service = WorkerService()
            self.worker = service.get_by_id(self.auth_token.id_worker)
            if self.worker is None:
                yield AppState.logout
                return
            self.actions_worker = self._auth_service.get_list_worker_actions(self.worker.id)
            self.permissions_version_seen = self.worker.permissions_version or 0
            if self._refresh_unread_update_flag():
                yield rx.toast.info("Систему оновлено! 🎉 Перегляньте, що нового.")
            return

        # Перевірка bump'у прав — щоб зміни адміна застосовувалися без релогіну.
        current_version = self._auth_service.get_worker_permissions_version(self.worker.id)
        if current_version != self.permissions_version_seen:
            service = WorkerService()
            refreshed = service.get_by_id(self.worker.id)
            if refreshed is None:
                yield AppState.logout
                return
            self.worker = refreshed
            self.actions_worker = self._auth_service.get_list_worker_actions(self.worker.id)
            self.permissions_version_seen = current_version

        if self._refresh_unread_update_flag():
            yield rx.toast.info("Систему оновлено! 🎉 Перегляньте, що нового.")

    def _refresh_unread_update_flag(self) -> bool:
        """Оновлює `has_unread_update` (DK-32); повертає `True`, якщо саме зараз
        require_auth має показати одноразовий тост «систему оновлено» (щоб не
        плодити вкладені генератори — `yield` лишається за require_auth).
        Read-only (лише `SELECT MAX(id)`) — безпечно на hot path авторизації."""
        if self.worker is None:
            return False
        if self.latest_update_id_cache < 0:
            self.latest_update_id_cache = AppUpdateService().get_latest_id()
        self.has_unread_update = self.latest_update_id_cache > (self.worker.last_seen_update_id or 0)
        if self.has_unread_update and not self.update_notice_shown:
            self.update_notice_shown = True
            return True
        return False

    @rx.var
    def worker_pib(self) -> str:
        try:
            if not self.is_auth:
                return "Not Auth"
            if self.worker and self.worker.pib:
                return self.worker.pib
            service = WorkerService()
            self.worker = service.get_by_id(self.auth_token.id_worker)
            return self.worker.pib if self.worker and self.worker.pib else ""
        except Exception as e:
            print(f"[AppState][worker_pib][ERROR] {e}")
            return "Not Auth"
        
    @rx.var
    def get_user_actions(self) -> List[str]:
        return self.actions_worker

    @rx.var
    def section_title(self) -> str:
        path = self.router.url.path or ""
        best_base = ""
        best_title = ""
        for base, title in SECTION_TITLES.items():
            if path.startswith(base) and len(base) > len(best_base):
                best_base = base
                best_title = title
        return best_title

    def _route_param(self, name: str, default: str = "") -> str:
        """Path-параметр маршруту (наприклад `[id]`).

        Reflex 0.8 рендерить `RouterData.page` депрекейтнутим, але прямого
        публічного API для path-params поки немає. Чита́ємо через приватний
        `router._page.params` — це джерело, з якого старий `router.page.params`
        теж бере дані; deprecation warning при цьому зникає. Якщо у майбутньому
        зʼявиться нормальний геттер — замінимо тут одне місце.
        """
        try:
            return str(self.router._page.params.get(name, default))
        except Exception:
            return default

    @rx.event
    def logout(self):
        try:
            if self.auth_token is not None:
                self._auth_service.logout(self.auth_token)
        except Exception as e:
            print(f"[AppState][logout][ERROR] {e}")

        self.user_menu_open = False
        self.worker = None
        self.auth_token = None
        self.actions_worker = []
        self.permissions_version_seen = 0

        yield rx.remove_cookie("auth_token")
        yield rx.redirect(routes.LOGIN)
