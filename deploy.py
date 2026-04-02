import reflex as rx
import os
from sqlmodel import select

from Dekanat.models import ActionModel, RoleModel, WorkerModel
from update import sync_actions
from Dekanat.utils.generators import generate_password_hash

def initial_deploy():
    with rx.session() as session:
        sync_actions(session)
        
        print("\n\n\n")

        admin_user = session.exec(select(WorkerModel).where(WorkerModel.login == "admin")).first()
        if admin_user:
            print("Система вже ініціалізована (користувач 'admin' існує). Вихід.")
            return

        print("Створюємо першого користувача...")

        salt = os.urandom(16).hex()
        password = "admin"
        pwd_hash = generate_password_hash(password, salt)
        
        worker = WorkerModel(
            pib="Головний Адміністратор",
            login="admin",
            password_salt=salt,
            password=pwd_hash
        )
        session.add(worker)

        admin_role = RoleModel(
            title="Супер-Адміністратор",
            description="Повний доступ до усіх функцій системи"
        )
        
        all_actions = session.exec(select(ActionModel)).all()
        admin_role.actions = all_actions
        
        session.add(admin_role)
        
        worker.roles = [admin_role]
        
        session.commit()
        
        print("\n")
        print(f"Деплой усішно завершено!")
        print(f"Логін: admin")
        print(f"Пароль: {password}")
        print(f"Роль: {admin_role.title} з {len(all_actions)} правами.")
        print("\n\n\n")

if __name__ == "__main__":
    initial_deploy()