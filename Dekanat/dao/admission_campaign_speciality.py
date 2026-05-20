from typing import Sequence
from sqlmodel import Session, select, delete
from sqlalchemy.orm import selectinload

from Dekanat.models import AdmissionCampaignSpecialityModel, SpecialityModel


class AdmissionCampaignSpecialityDao:
    @staticmethod
    def get_by_campaign(id_campaign: int, session: Session) -> Sequence[AdmissionCampaignSpecialityModel]:
        statement = (
            select(AdmissionCampaignSpecialityModel)
            .options(
                selectinload(AdmissionCampaignSpecialityModel.speciality).selectinload(
                    SpecialityModel.department
                )
            )
            .where(AdmissionCampaignSpecialityModel.id_admission_campaign == id_campaign)
        )
        return session.exec(statement).all()

    @staticmethod
    def delete_by_campaign(id_campaign: int, session: Session):
        stmt = delete(AdmissionCampaignSpecialityModel).where(
            AdmissionCampaignSpecialityModel.id_admission_campaign == id_campaign
        )
        session.exec(stmt)  # type: ignore[arg-type]

    @staticmethod
    def add_one(item: AdmissionCampaignSpecialityModel, session: Session) -> AdmissionCampaignSpecialityModel:
        session.add(item)
        return item
