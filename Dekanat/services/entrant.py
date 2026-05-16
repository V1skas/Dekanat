import reflex as rx
import base64

from typing import Optional, Sequence

from Dekanat.dao.entrant import EntrantDao
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


def photo_to_data_url(photo_bytes: Optional[bytes], mime: Optional[str]) -> str:
    """Convert stored photo bytes + mime into an inline data URL for rx.image src."""
    if not photo_bytes:
        return ""
    effective_mime = mime if mime else "image/png"
    encoded = base64.b64encode(photo_bytes).decode("ascii")
    return f"data:{effective_mime};base64,{encoded}"


class EntrantService:
    def get_list_items(self) -> Sequence[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantDao.get_all(session)
        except Exception as e:
            print(f"[EntrantService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantService][get_by_id][ERROR] {e}")
            raise

    def add_one(
        self,
        person: PersonModel,
        entrant: EntrantModel,
        identity_documents: list[IdentityDocumentModel],
        documents_about_education: list[DocumentAboutEducationModel],
        military_accountings: list[MilitaryAccountingModel],
        medical_references: list[MedicalReferenceModel],
        information_about_relatives: list[InformationAboutRelativesModel],
        special_conditions: list[SpecialConditionPersonModel],
        specialties: list[SpecialtieEntrantModel],
        results_zno: list[ResultZnoModel],
    ) -> EntrantModel:
        try:
            with rx.session() as session:
                person.id = None  # type: ignore[assignment]
                saved_person = EntrantDao.add_person(person, session)
                person_id = saved_person.id

                entrant.id = person_id  # type: ignore[assignment]
                saved_entrant = EntrantDao.add_entrant(entrant, session)

                EntrantDao.replace_identity_documents(person_id, identity_documents, session)
                EntrantDao.replace_documents_about_education(person_id, documents_about_education, session)
                EntrantDao.replace_military_accountings(person_id, military_accountings, session)
                EntrantDao.replace_medical_references(person_id, medical_references, session)
                EntrantDao.replace_information_about_relatives(person_id, information_about_relatives, session)
                EntrantDao.replace_special_conditions(person_id, special_conditions, session)
                EntrantDao.replace_results_zno(person_id, results_zno, session)
                EntrantDao.replace_specialties(person_id, specialties, session)

                session.commit()
                session.refresh(saved_entrant)
                return saved_entrant
        except Exception as e:
            print(f"[EntrantService][add_one][ERROR] {e}")
            raise

    def edit_one(
        self,
        person: PersonModel,
        entrant: EntrantModel,
        identity_documents: list[IdentityDocumentModel],
        documents_about_education: list[DocumentAboutEducationModel],
        military_accountings: list[MilitaryAccountingModel],
        medical_references: list[MedicalReferenceModel],
        information_about_relatives: list[InformationAboutRelativesModel],
        special_conditions: list[SpecialConditionPersonModel],
        specialties: list[SpecialtieEntrantModel],
        results_zno: list[ResultZnoModel],
    ) -> EntrantModel:
        try:
            with rx.session() as session:
                EntrantDao.edit_person(person, session)
                merged_entrant = EntrantDao.edit_entrant(entrant, session)
                session.flush()

                person_id = person.id

                EntrantDao.replace_identity_documents(person_id, identity_documents, session)
                EntrantDao.replace_documents_about_education(person_id, documents_about_education, session)
                EntrantDao.replace_military_accountings(person_id, military_accountings, session)
                EntrantDao.replace_medical_references(person_id, medical_references, session)
                EntrantDao.replace_information_about_relatives(person_id, information_about_relatives, session)
                EntrantDao.replace_special_conditions(person_id, special_conditions, session)
                EntrantDao.replace_results_zno(person_id, results_zno, session)
                EntrantDao.replace_specialties(entrant.id, specialties, session)

                session.commit()
                session.refresh(merged_entrant)
                return merged_entrant
        except Exception as e:
            print(f"[EntrantService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, entrant: EntrantModel) -> bool:
        try:
            with rx.session() as session:
                entrant.is_deleted = True
                EntrantDao.edit_entrant(entrant, session)
                if entrant.person is not None:
                    entrant.person.is_deleted = True
                    EntrantDao.edit_person(entrant.person, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantService][delete_one][ERROR] {e}")
            return False
