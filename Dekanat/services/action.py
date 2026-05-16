import reflex as rx

from typing import Optional, Sequence

from Dekanat.dao.action import ActionDao
from Dekanat.models import ActionModel


class ActionService:
    def get_list_items(self) ->  Sequence[ActionModel]:
        try:
            with rx.session() as session:
                return ActionDao.get_all(session)
        except Exception as e:
            print(f"[ActionService][get_all][ERROR] {e}")
            raise
