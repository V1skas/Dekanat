from typing import Sequence

import reflex as rx
from sqlmodel import Session, select

from Dekanat.dao.app_update import AppUpdateDao
from Dekanat.dao.worker import WorkerDao
from Dekanat.models import AppUpdateModel, WorkerModel
from Dekanat.declared.updates import UPDATES


class AppUpdateService:
    def get_list_items(self) -> Sequence[AppUpdateModel]:
        try:
            with rx.session() as session:
                return AppUpdateDao.get_all(session)
        except Exception as e:
            print(f"[AppUpdateService][get_list_items][ERROR] {e}")
            raise

    def get_latest_id(self) -> int:
        """Read-only — безпечно викликати з `require_auth` (hot path авторизації,
        жодних INSERT'ів, див. CLAUDE.md про SQLite database is locked)."""
        try:
            with rx.session() as session:
                return AppUpdateDao.get_max_id(session)
        except Exception as e:
            print(f"[AppUpdateService][get_latest_id][ERROR] {e}")
            return 0

    def mark_seen(self, worker_id: int, up_to_id: int) -> None:
        try:
            with rx.session() as session:
                WorkerDao.set_last_seen_update(worker_id, up_to_id, session)
                session.commit()
        except Exception as e:
            print(f"[AppUpdateService][mark_seen][ERROR] {e}")
            raise

    def sync_updates(self, session: Session) -> None:
        """Синхронізує `Dekanat/declared/updates.py:UPDATES` у БД (за зразком
        `update.py:sync_actions`) — джерело правди залишається в git. Викликається
        з `update.py`/`deploy.py`, не з hot path авторизації.

        Захист від спаму при першому розгортанні (DK-32): якщо до синку таблиця
        була порожня, а після — ні, усім наявним воркерам виставляється
        `last_seen_update_id = max(id)`, щоб перший-же changelog не «вистрелив»
        тостом «систему оновлено» одразу всім."""
        was_empty = session.exec(select(AppUpdateModel)).first() is None

        added_count = 0
        for item in UPDATES:
            existing = AppUpdateDao.get_by_version(item.version, session)
            if existing is not None:
                continue
            session.add(AppUpdateModel(version=item.version, title=item.title, body=item.body))
            added_count += 1

        session.commit()
        print(f"Синхронізація оновлень (changelog): додано {added_count} шт.")

        if was_empty and added_count > 0:
            max_id = AppUpdateDao.get_max_id(session)
            workers = session.exec(select(WorkerModel)).all()
            for worker in workers:
                worker.last_seen_update_id = max_id
                session.add(worker)
            session.commit()
            print(f"Перше розгортання changelog'у: {len(workers)} користувачів позначено як таких, що вже бачили.")
