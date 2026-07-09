import os

import reflex as rx

from types import SimpleNamespace
from typing import Optional, Sequence, List

from Dekanat.models import ActionModel, RoleModel, WorkerModel
from Dekanat.dao.worker import WorkerDao
from Dekanat.utils.generators import generate_password_hash
from Dekanat.audit import (
    record_action,
    FieldChange,
    WorkerCreated,
    WorkerUpdated,
    WorkerDeleted,
)


class WorkerService:
    def get_list_items(self) -> Sequence[WorkerModel]:
        try:
            with rx.session() as session:
                return WorkerDao.get_all(session)
        except Exception as e:
            print(f"[WorkerService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[WorkerModel]:
        try:
            with rx.session() as session:
                worker = WorkerDao.get_by_id(id, session)
                if worker:
                    session.expunge_all()
                return worker
        except Exception as e:
            print(f"[WorkerService][get_by_id][ERROR] {e}")
            return None

    def get_by_id_full(self, id: int) -> Optional[WorkerModel]:
        try:
            with rx.session() as session:
                return WorkerDao.get_by_id_with_roles_and_actions(id, session)
        except Exception as e:
            print(f"[WorkerService][get_by_id_full][ERROR] {e}")
            raise

    def is_login_taken(self, login: str, exclude_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                existing = WorkerDao.get_by_login(login, session, with_delete=True)
                if existing is None:
                    return False
                if exclude_id is not None and existing.id == exclude_id:
                    return False
                return True
        except Exception as e:
            print(f"[WorkerService][is_login_taken][ERROR] {e}")
            raise

    def add_one(
        self,
        pib: str,
        login: str,
        password: str,
        phone_number: Optional[str],
        email: Optional[str],
        photo: Optional[str],
        role_ids: List[int],
        action_ids: List[int],
        actor_id: Optional[int] = None,
    ) -> int:
        try:
            with rx.session() as session:
                salt = os.urandom(16).hex()
                pwd_hash = generate_password_hash(password, salt)

                roles = [r for r in (session.get(RoleModel, rid) for rid in role_ids) if r is not None]
                actions = [a for a in (session.get(ActionModel, aid) for aid in action_ids) if a is not None]

                worker = WorkerModel(
                    pib=pib,
                    login=login,
                    password=pwd_hash,
                    password_salt=salt,
                    phone_number=phone_number,
                    email=email,
                    photo=photo,
                    roles=roles,
                    actions=actions,
                )
                session.add(worker)
                session.flush()
                record_action(session, actor_id, worker.id, WorkerCreated(
                    pib=pib, login=login, email=email, phone_number=phone_number,
                ))
                session.commit()
                session.refresh(worker)
                return worker.id
        except Exception as e:
            print(f"[WorkerService][add_one][ERROR] {e}")
            raise

    def edit_one(
        self,
        id: int,
        pib: str,
        login: str,
        password: Optional[str],
        phone_number: Optional[str],
        email: Optional[str],
        photo: Optional[str],
        role_ids: List[int],
        action_ids: List[int],
        actor_id: Optional[int] = None,
    ) -> bool:
        try:
            with rx.session() as session:
                worker = WorkerDao.get_by_id_with_roles_and_actions(id, session)
                if worker is None:
                    return False

                # Знімок старих значень до мутації (для diff журналу).
                old_snap = SimpleNamespace(
                    pib=worker.pib, login=worker.login,
                    email=worker.email, phone_number=worker.phone_number,
                )
                old_roles = sorted(r.title for r in (worker.roles or []))

                worker.pib = pib
                worker.login = login
                worker.phone_number = phone_number
                worker.email = email
                worker.photo = photo

                if password:
                    salt = os.urandom(16).hex()
                    worker.password_salt = salt
                    worker.password = generate_password_hash(password, salt)

                worker.roles = [r for r in (session.get(RoleModel, rid) for rid in role_ids) if r is not None]
                worker.actions = [a for a in (session.get(ActionModel, aid) for aid in action_ids) if a is not None]
                # Бамп версії — щоб залогінені сесії перечитали права на наступний require_auth.
                worker.permissions_version = (worker.permissions_version or 0) + 1

                session.add(worker)
                session.flush()

                action = WorkerUpdated.from_diff(old_snap, worker)
                new_roles = sorted(r.title for r in (worker.roles or []))
                if new_roles != old_roles:
                    action.roles = FieldChange(old=old_roles, new=new_roles)
                record_action(session, actor_id, id, action)

                session.commit()
            return True
        except Exception as e:
            print(f"[WorkerService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: WorkerModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                worker = WorkerDao.get_by_id(item.id, session)
                if worker is None:
                    return False
                worker.is_deleted = True
                session.add(worker)
                record_action(session, actor_id, worker.id, WorkerDeleted(
                    pib=worker.pib, login=worker.login,
                ))
                session.commit()
            return True
        except Exception as e:
            print(f"[WorkerService][delete_one][ERROR] {e}")
            return False
