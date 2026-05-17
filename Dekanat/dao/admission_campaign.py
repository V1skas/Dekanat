from typing import Sequence, Optional
from sqlmodel import Session, select

from Dekanat.models import AdmissionCampaignModel


class AdmissionCampaignDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[AdmissionCampaignModel]:
        statement = select(AdmissionCampaignModel).order_by(AdmissionCampaignModel.start_date.desc())
        if not with_del:
            statement = statement.where(AdmissionCampaignModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[AdmissionCampaignModel]:
        statement = select(AdmissionCampaignModel).where(AdmissionCampaignModel.id == id)
        if not with_del:
            statement = statement.where(AdmissionCampaignModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: AdmissionCampaignModel, session: Session) -> AdmissionCampaignModel:
        session.add(item)
        return item

    @staticmethod
    def edit_one(item: AdmissionCampaignModel, session: Session) -> AdmissionCampaignModel:
        merged = session.merge(item)
        session.add(merged)
        return merged
