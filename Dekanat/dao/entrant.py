from typing import Sequence, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload, make_transient

from Dekanat.models import (
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    IdentityDocumentModel,
    DocumentAboutEducationModel,
    MilitaryAccountingModel,
    MedicalReferenceModel,
    InformationAboutRelativesModel,
    SpecialConditionPersonModel,
    ResultZnoModel,
)


def _entrant_loaders():
    """Eager-load all relationships needed to render an entrant page."""
    return [
        selectinload(EntrantModel.application_status),
        selectinload(EntrantModel.entrant_group),
        selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality),
        selectinload(EntrantModel.person).selectinload(PersonModel.source_of_funding),
        selectinload(EntrantModel.person).selectinload(PersonModel.entry_base),
        selectinload(EntrantModel.person).selectinload(PersonModel.identity_document).selectinload(IdentityDocumentModel.type),
        selectinload(EntrantModel.person).selectinload(PersonModel.document_about_education),
        selectinload(EntrantModel.person).selectinload(PersonModel.military_accounting),
        selectinload(EntrantModel.person).selectinload(PersonModel.medical_reference),
        selectinload(EntrantModel.person).selectinload(PersonModel.information_about_relatives).selectinload(InformationAboutRelativesModel.kinship),
        selectinload(EntrantModel.person).selectinload(PersonModel.special_conditions),
        selectinload(EntrantModel.person).selectinload(PersonModel.results_zno).selectinload(ResultZnoModel.item_zno),
    ]


class EntrantDao:
    @staticmethod
    def get_all(session: Session, with_del: bool = False) -> Sequence[EntrantModel]:
        statement = select(EntrantModel).options(*_entrant_loaders())
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[EntrantModel]:
        statement = select(EntrantModel).options(*_entrant_loaders()).where(EntrantModel.id == id)
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def add_person(person: PersonModel, session: Session) -> PersonModel:
        session.add(person)
        session.flush()
        return person

    @staticmethod
    def add_entrant(entrant: EntrantModel, session: Session) -> EntrantModel:
        session.add(entrant)
        session.flush()
        return entrant

    @staticmethod
    def edit_person(person: PersonModel, session: Session) -> PersonModel:
        return session.merge(person)

    @staticmethod
    def edit_entrant(entrant: EntrantModel, session: Session) -> EntrantModel:
        return session.merge(entrant)

    # --- child collection sync helpers ---

    # Note on `make_transient`: items приходять із попередньої (вже закритої) сесії і
    # SQLAlchemy зберігає для них identity-key. На session.add() це породжує UPDATE,
    # який не знаходить рядка (бо ми тільки що видалили оригінали). make_transient
    # знімає identity, і add() робить чистий INSERT.

    @staticmethod
    def replace_identity_documents(person_id: int, items: list[IdentityDocumentModel], session: Session) -> None:
        for old in session.exec(select(IdentityDocumentModel).where(IdentityDocumentModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_documents_about_education(person_id: int, items: list[DocumentAboutEducationModel], session: Session) -> None:
        for old in session.exec(select(DocumentAboutEducationModel).where(DocumentAboutEducationModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_military_accountings(person_id: int, items: list[MilitaryAccountingModel], session: Session) -> None:
        for old in session.exec(select(MilitaryAccountingModel).where(MilitaryAccountingModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_medical_references(person_id: int, items: list[MedicalReferenceModel], session: Session) -> None:
        for old in session.exec(select(MedicalReferenceModel).where(MedicalReferenceModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id = None
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_information_about_relatives(person_id: int, items: list[InformationAboutRelativesModel], session: Session) -> None:
        for old in session.exec(select(InformationAboutRelativesModel).where(InformationAboutRelativesModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id = None
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_special_conditions(person_id: int, items: list[SpecialConditionPersonModel], session: Session) -> None:
        for old in session.exec(select(SpecialConditionPersonModel).where(SpecialConditionPersonModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_results_zno(person_id: int, items: list[ResultZnoModel], session: Session) -> None:
        for old in session.exec(select(ResultZnoModel).where(ResultZnoModel.id_person == person_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id = None
            item.id_person = person_id
            session.add(item)

    @staticmethod
    def replace_specialties(entrant_id: int, items: list[SpecialtieEntrantModel], session: Session) -> None:
        for old in session.exec(select(SpecialtieEntrantModel).where(SpecialtieEntrantModel.id_entrant == entrant_id)).all():
            session.delete(old)
        session.flush()
        for item in items:
            make_transient(item)
            item.id_entrant = entrant_id
            session.add(item)
