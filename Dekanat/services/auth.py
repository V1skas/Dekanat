from typing import Optional, List, Set, Tuple

import reflex as rx

from Dekanat.dao.auth_token import AuthTokenDao
from Dekanat.dao.worker import WorkerDao
from Dekanat.models import AuthTokenModel, WorkerModel
from Dekanat.utils import generators

class AuthService:
    def get_auth_token(self, cache_token: str) -> Optional[AuthTokenModel]:
        with rx.session() as session:
            return AuthTokenDao.get_by_token(cache_token, session)

    def get_list_worker_actions(self, id_worker: int) -> List[str]:
        worker_actions: List[str] = []
        with rx.session() as session:
            worker_actions = [action.code for action in WorkerDao.get_worker_actions_by_id(id_worker, session)]
            worker_actions = worker_actions + [action.code for action in WorkerDao.get_worker_actions_in_roles_by_id(id_worker, session)]
            return list(worker_actions)

    def logout(self, token: AuthTokenModel):
        with rx.session() as session:
            AuthTokenDao.delete(token, session)

    def auth(self, login: str, password: str) -> Optional[Tuple[WorkerModel, AuthTokenModel]]:
        worker: Optional[WorkerModel] = None
        with rx.session() as session:
            worker = WorkerDao.get_by_login(login, session)
            if worker is None:
                return worker

            calculated_hash = generators.generate_password_hash(password, worker.password_salt)

            if calculated_hash != worker.password:
                return None

            auth_token = AuthTokenModel(token=generators.generate_auth_token(), id_worker=worker.id)
            AuthTokenDao.add_one(auth_token, session)
            session.commit()
            session.refresh(auth_token)
            return (worker, auth_token)

