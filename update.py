import reflex as rx
from sqlmodel import select

from Dekanat.models import ActionModel
from Dekanat.actions import Actions as SystemAction
from Dekanat.services.app_update import AppUpdateService

def sync_actions(session: rx.session):
    print("\n\n\nПочинаю синхронізацію дій (Actions)...")
    
    existing_actions_list = session.exec(select(ActionModel)).all()
    existing_actions = {act.code: act for act in existing_actions_list}
    
    added_count = 0
    updated_count = 0

    for sys_action in SystemAction:
        if sys_action.value not in existing_actions:
            new_action = ActionModel(
                code=sys_action.value,
                title=sys_action.title_attr,
                description=sys_action.description_attr
            )
            session.add(new_action)
            added_count += 1
        else:
            db_action = existing_actions[sys_action.value]
            is_changed = False
            
            if db_action.title != sys_action.title_attr:
                db_action.title = sys_action.title_attr
                is_changed = True
                
            if db_action.description != sys_action.description_attr:
                db_action.description = sys_action.description_attr
                is_changed = True
                
            if is_changed:
                session.add(db_action)
                updated_count += 1

    session.commit()
    print(f"Виконано! Додано: {added_count} дій, Оновлено описів: {updated_count}")

if __name__ == "__main__":
    with rx.session() as session:
        sync_actions(session)
        AppUpdateService().sync_updates(session)