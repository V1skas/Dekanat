from typing import Optional, Sequence
from sqlmodel import Session, select, func

from Dekanat.models import AppUpdateModel


class AppUpdateDao:
    @staticmethod
    def get_all(session: Session) -> Sequence[AppUpdateModel]:
        statement = (
            select(AppUpdateModel)
            .where(AppUpdateModel.is_deleted == False)
            .order_by(AppUpdateModel.published_at.desc(), AppUpdateModel.id.desc())  # type: ignore[attr-defined]
        )
        return session.exec(statement).all()

    @staticmethod
    def get_by_version(version: str, session: Session) -> Optional[AppUpdateModel]:
        statement = select(AppUpdateModel).where(AppUpdateModel.version == version)
        return session.exec(statement).one_or_none()

    @staticmethod
    def get_max_id(session: Session) -> int:
        result = session.exec(select(func.max(AppUpdateModel.id))).one_or_none()
        return result or 0
