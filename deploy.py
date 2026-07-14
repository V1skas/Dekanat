import os

import reflex as rx
from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.models import ActionModel, RoleModel, WorkerModel
from Dekanat.actions import Actions
from Dekanat.dao.app_update import AppUpdateDao
from Dekanat.services.app_setting import AppSettingService
from Dekanat.services.app_update import AppUpdateService
from Dekanat.utils.generators import generate_password_hash
from update import sync_actions


ADMIN_ROLE_TITLE = "Адміністратор"
ADMIN_ROLE_DESCRIPTION = "Управління користувачами та ролями"

ADMIN_LOGIN = "admin"
ADMIN_DEFAULT_PASSWORD = "admin"
ADMIN_PIB = "Головний Адміністратор"

ADMIN_ROLE_ACTION_CODES = [
    Actions.WORKER_LIST.value,
    Actions.WORKER_ADD.value,
    Actions.WORKER_EDIT.value,
    Actions.WORKER_DELETE.value,
    Actions.WORKER_VIEW.value,
    Actions.ROLE_LIST.value,
    Actions.ROLE_ADD.value,
    Actions.ROLE_EDIT.value,
    Actions.ROLE_DELETE.value,
    Actions.ROLE_VIEW.value,
]


def ensure_admin_role(session) -> RoleModel:
    required_actions = session.exec(
        select(ActionModel).where(ActionModel.code.in_(ADMIN_ROLE_ACTION_CODES))
    ).all()

    missing_codes = set(ADMIN_ROLE_ACTION_CODES) - {a.code for a in required_actions}
    if missing_codes:
        raise RuntimeError(
            f"В БД відсутні наступні дії, спочатку запустіть update.py: {sorted(missing_codes)}"
        )

    role = session.exec(
        select(RoleModel)
        .options(selectinload(RoleModel.actions))
        .where(RoleModel.title == ADMIN_ROLE_TITLE)
    ).first()

    if role is None:
        print(f"Створюємо роль '{ADMIN_ROLE_TITLE}' з {len(required_actions)} правами.")
        role = RoleModel(
            title=ADMIN_ROLE_TITLE,
            description=ADMIN_ROLE_DESCRIPTION,
            actions=list(required_actions),
        )
        session.add(role)
        session.flush()
        return role

    if role.is_deleted:
        print(f"Відновлюємо раніше видалену роль '{ADMIN_ROLE_TITLE}'.")
        role.is_deleted = False

    existing_ids = {a.id for a in (role.actions or [])}
    to_add = [a for a in required_actions if a.id not in existing_ids]

    if to_add:
        print(f"Додаємо до ролі '{ADMIN_ROLE_TITLE}' відсутні права: {len(to_add)} шт.")
        if role.actions is None:
            role.actions = []
        role.actions.extend(to_add)
        session.add(role)
        session.flush()
    else:
        print(f"Роль '{ADMIN_ROLE_TITLE}' вже має всі необхідні права.")

    return role


def ensure_admin_user(session, admin_role: RoleModel) -> WorkerModel:
    worker = session.exec(
        select(WorkerModel)
        .options(selectinload(WorkerModel.roles))
        .where(WorkerModel.login == ADMIN_LOGIN)
    ).first()

    if worker is None:
        print(f"Створюємо користувача '{ADMIN_LOGIN}'.")
        salt = os.urandom(16).hex()
        pwd_hash = generate_password_hash(ADMIN_DEFAULT_PASSWORD, salt)
        # Адмін не повинен бачити тост про оновлення, вже наявні на момент деплою (DK-32).
        worker = WorkerModel(
            pib=ADMIN_PIB,
            login=ADMIN_LOGIN,
            password_salt=salt,
            password=pwd_hash,
            roles=[admin_role],
            last_seen_update_id=AppUpdateDao.get_max_id(session),
        )
        session.add(worker)
        print(f"  Логін: {ADMIN_LOGIN}")
        print(f"  Пароль: {ADMIN_DEFAULT_PASSWORD}")
        return worker

    if worker.is_deleted:
        print(f"Відновлюємо раніше видаленого користувача '{ADMIN_LOGIN}'.")
        worker.is_deleted = False

    existing_role_ids = {r.id for r in (worker.roles or [])}
    if admin_role.id not in existing_role_ids:
        print(f"Призначаємо роль '{ADMIN_ROLE_TITLE}' користувачу '{ADMIN_LOGIN}'.")
        if worker.roles is None:
            worker.roles = []
        worker.roles.append(admin_role)
        session.add(worker)
    else:
        print(f"Користувач '{ADMIN_LOGIN}' вже має роль '{ADMIN_ROLE_TITLE}'.")

    return worker


def initial_deploy():
    with rx.session() as session:
        sync_actions(session)
        print()

        AppUpdateService().sync_updates(session)
        print()

        admin_role = ensure_admin_role(session)
        ensure_admin_user(session, admin_role)

        session.commit()

    AppSettingService().ensure_defaults()
    print("\nДеплой успішно завершено!")


if __name__ == "__main__":
    initial_deploy()
