from datetime import datetime, timedelta
from typing import Optional, List, Tuple

import reflex as rx

from Dekanat.dao.auth_token import AuthTokenDao
from Dekanat.dao.worker import WorkerDao
from Dekanat.models import AuthTokenModel, WorkerModel
from Dekanat.services.app_setting import AppSettingService
from Dekanat.utils import generators
from Dekanat.utils.clock import now_local


class AuthService:
    def _compute_expiry(self) -> datetime:
        minutes = AppSettingService().get_session_timeout_minutes()
        if minutes <= 0:
            minutes = 60
        return now_local() + timedelta(minutes=minutes)

    def get_auth_token(self, cache_token: str) -> Optional[AuthTokenModel]:
        """Повертає валідний (не протермінований) токен та продовжує його (ковзне вікно).
        Протерміновані токени видаляються одразу."""
        try:
            with rx.session() as session:
                # Лінива чистка: при кожній валідації заодно прибираємо протерміновані.
                AuthTokenDao.delete_expired(session)

                token = AuthTokenDao.get_by_token(cache_token, session)
                if token is None:
                    session.commit()
                    return None
                if token.expires_at <= now_local():
                    AuthTokenDao.delete(token, session)
                    session.commit()
                    return None

                AuthTokenDao.touch(token, self._compute_expiry(), session)
                session.commit()
                session.refresh(token)
                session.expunge_all()
                return token
        except Exception as e:
            print(f"[AuthService][get_auth_token][ERROR] {e}")
            return None

    def get_list_worker_actions(self, id_worker: int) -> List[str]:
        worker_actions: List[str] = []
        with rx.session() as session:
            worker_actions = [action.code for action in WorkerDao.get_worker_actions_by_id(id_worker, session)]
            worker_actions = worker_actions + [action.code for action in WorkerDao.get_worker_actions_in_roles_by_id(id_worker, session)]
            return list(worker_actions)

    def get_worker_permissions_version(self, id_worker: int) -> int:
        """Повертає поточну версію прав, для звірки з кешем у AppState."""
        try:
            with rx.session() as session:
                worker = WorkerDao.get_by_id(id_worker, session)
                if worker is None:
                    return 0
                return worker.permissions_version or 0
        except Exception as e:
            print(f"[AuthService][get_worker_permissions_version][ERROR] {e}")
            return 0

    def logout(self, token: AuthTokenModel):
        with rx.session() as session:
            AuthTokenDao.delete(token, session)
            session.commit()

    def auth(self, login: str, password: str) -> Optional[Tuple[WorkerModel, AuthTokenModel]]:
        worker: Optional[WorkerModel] = None
        with rx.session() as session:
            # Заодно прибираємо протерміновані токени при логіні.
            AuthTokenDao.delete_expired(session)

            worker = WorkerDao.get_by_login(login, session)
            if worker is None:
                session.commit()
                return None

            calculated_hash = generators.generate_password_hash(password, worker.password_salt)

            if calculated_hash != worker.password:
                session.commit()
                return None

            auth_token = AuthTokenModel(
                token=generators.generate_auth_token(),
                id_worker=worker.id,
                expires_at=self._compute_expiry(),
                last_activity_at=now_local(),
            )
            AuthTokenDao.add_one(auth_token, session)
            session.commit()
            session.refresh(auth_token)
            return (worker, auth_token)
