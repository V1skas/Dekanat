import reflex as rx

from typing import Optional

from Dekanat.models import WorkerModel
from Dekanat.dao.worker import WorkerDao

class WorkerService:
    def get_by_id(self, id: int) -> Optional[WorkerModel]:
        try:
            with rx.session() as session:
                list = WorkerDao.get_by_id(id, session)
                if list:
                    session.expunge_all()
                return list
        except Exception as e:
            print(f"[WorkerService][get_by_id][ERROR] {e}")
            return
