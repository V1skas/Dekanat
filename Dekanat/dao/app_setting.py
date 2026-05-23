from typing import Optional, Sequence
from sqlmodel import Session, select

from Dekanat.models import AppSettingModel


class AppSettingDao:
    @staticmethod
    def get_all(session: Session) -> Sequence[AppSettingModel]:
        return session.exec(select(AppSettingModel).order_by(AppSettingModel.category, AppSettingModel.title)).all()

    @staticmethod
    def get_by_key(key: str, session: Session) -> Optional[AppSettingModel]:
        return session.exec(select(AppSettingModel).where(AppSettingModel.key == key)).one_or_none()

    @staticmethod
    def get_by_category(category: str, session: Session) -> Sequence[AppSettingModel]:
        return session.exec(
            select(AppSettingModel)
            .where(AppSettingModel.category == category)
            .order_by(AppSettingModel.title)
        ).all()

    @staticmethod
    def upsert(item: AppSettingModel, session: Session) -> AppSettingModel:
        return session.merge(item)
