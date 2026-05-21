import reflex as rx

from typing import Sequence, List, Optional

from Dekanat.dao.result_zno import ResultZnoDao
from Dekanat.models import ResultZnoModel


class ResultZnoService:
    def get_by_subject_and_persons(
        self, id_items_zno: int, person_ids: List[int]
    ) -> Sequence[ResultZnoModel]:
        try:
            with rx.session() as session:
                return ResultZnoDao.get_by_subject_and_persons(
                    id_items_zno, person_ids, session
                )
        except Exception as e:
            print(f"[ResultZnoService][get_by_subject_and_persons][ERROR] {e}")
            raise

    def upsert(self, id_items_zno: int, id_person: int, points: Optional[int]) -> None:
        """Якщо `points is None` — видаляє існуючу оцінку. Інакше — створює/оновлює."""
        try:
            with rx.session() as session:
                if points is None:
                    ResultZnoDao.delete_one(id_items_zno, id_person, session)
                else:
                    ResultZnoDao.upsert(id_items_zno, id_person, points, session)
                session.commit()
        except Exception as e:
            print(f"[ResultZnoService][upsert][ERROR] {e}")
            raise
