from typing import Sequence, Optional
from sqlmodel import Session, select, delete

from Dekanat.models import SourceOfFundingModel, SourceOfFundingEligibilityModel


class SourceOfFundingDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[SourceOfFundingModel]:
        statement = select(SourceOfFundingModel)
        if not with_del:
            statement = statement.where(SourceOfFundingModel.is_deleted == False)
        statement = statement.order_by(SourceOfFundingModel.sequence)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[SourceOfFundingModel]:
        statement = select(SourceOfFundingModel).where(SourceOfFundingModel.id == id)
        if not with_del:
            statement = statement.where(SourceOfFundingModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_one(item: SourceOfFundingModel, session: Session):
        session.add(item)

    @staticmethod
    def edit_one(item: SourceOfFundingModel, session: Session):
        merged = session.merge(item)
        session.add(merged)
        return merged


class SourceOfFundingEligibilityDao:
    @staticmethod
    def get_eligible_ids(id_source_of_funding: int, session: Session) -> Sequence[int]:
        statement = select(SourceOfFundingEligibilityModel.id_eligible_source_of_funding).where(
            SourceOfFundingEligibilityModel.id_source_of_funding == id_source_of_funding
        )
        return session.exec(statement).all()

    @staticmethod
    def delete_for_source(id_source_of_funding: int, session: Session):
        stmt = delete(SourceOfFundingEligibilityModel).where(
            SourceOfFundingEligibilityModel.id_source_of_funding == id_source_of_funding
        )
        session.exec(stmt)  # type: ignore[arg-type]

    @staticmethod
    def add_one(item: SourceOfFundingEligibilityModel, session: Session):
        session.add(item)
