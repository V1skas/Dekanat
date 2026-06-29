from typing import Optional, Sequence, List
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.models import (
    RatingSnapshotModel,
    RatingEntryModel,
    EntrantModel,
    PersonModel,
)


class RatingDao:
    @staticmethod
    def get_latest_for_campaign(id_campaign: int, session: Session) -> Optional[RatingSnapshotModel]:
        statement = (
            select(RatingSnapshotModel)
            .where(RatingSnapshotModel.id_campaign == id_campaign)
            .order_by(RatingSnapshotModel.generated_at.desc())
        )
        return session.exec(statement).first()

    @staticmethod
    def get_entries(id_snapshot: int, session: Session) -> Sequence[RatingEntryModel]:
        statement = (
            select(RatingEntryModel)
            .options(
                selectinload(RatingEntryModel.speciality),
                selectinload(RatingEntryModel.entrant).selectinload(EntrantModel.person),
            )
            .where(RatingEntryModel.id_snapshot == id_snapshot)
            .order_by(
                RatingEntryModel.id_speciality_code,
                RatingEntryModel.id_speciality_department,
                RatingEntryModel.position,
            )
        )
        return session.exec(statement).all()

    @staticmethod
    def delete_for_campaign(id_campaign: int, session: Session) -> None:
        old_snapshots = session.exec(
            select(RatingSnapshotModel).where(RatingSnapshotModel.id_campaign == id_campaign)
        ).all()
        for snap in old_snapshots:
            for entry in session.exec(
                select(RatingEntryModel).where(RatingEntryModel.id_snapshot == snap.id)
            ).all():
                session.delete(entry)
            session.flush()
            session.delete(snap)
        session.flush()

    @staticmethod
    def add_snapshot(
        snapshot: RatingSnapshotModel, entries: List[RatingEntryModel], session: Session
    ) -> RatingSnapshotModel:
        session.add(snapshot)
        session.flush()
        for e in entries:
            e.id_snapshot = snapshot.id
            session.add(e)
        session.flush()
        return snapshot
