from typing import Optional
from sqlmodel import Session, select

from Dekanat.models import AdmissionCampaignReportModel


class AdmissionCampaignReportDao:
    @staticmethod
    def get_latest_for_campaign(id_campaign: int, session: Session) -> Optional[AdmissionCampaignReportModel]:
        statement = (
            select(AdmissionCampaignReportModel)
            .where(AdmissionCampaignReportModel.id_campaign == id_campaign)
            .order_by(AdmissionCampaignReportModel.generated_at.desc())
        )
        return session.exec(statement).first()

    @staticmethod
    def delete_for_campaign(id_campaign: int, session: Session) -> None:
        old = session.exec(
            select(AdmissionCampaignReportModel).where(AdmissionCampaignReportModel.id_campaign == id_campaign)
        ).all()
        for o in old:
            session.delete(o)
        session.flush()

    @staticmethod
    def add_one(item: AdmissionCampaignReportModel, session: Session) -> AdmissionCampaignReportModel:
        session.add(item)
        session.flush()
        return item
