from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import ActionModel


class ActionDao:
    @staticmethod
    def get_all(session: Session) -> Sequence[ActionModel]:
        statement = select(ActionModel)
        return session.exec(statement).all()
