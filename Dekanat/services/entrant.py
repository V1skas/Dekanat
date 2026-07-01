import reflex as rx
import base64

from datetime import datetime
from typing import Optional, Sequence, Tuple

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
    def get_list_items(
        self,
        pib: Optional[str] = None,
        phone: Optional[str] = None,
        status_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        priority_speciality_id: Optional[int] = None,
        top_priority_speciality_id: Optional[int] = None,
        sort_field: Optional[str] = None,
        sort_dir: str = "asc",
    ) -> Sequence[EntrantModel]:
        """Повертає абітурієнтів із серверною фільтрацією та сортуванням."""
        try:
            with rx.session() as session:
                return EntrantDao.get_all(
                    session,
                    pib_substring=pib,
                    phone_substring=phone,
                    application_status_id=status_id,
                    entry_base_id=entry_base_id,
                    created_between=created_between,
                    created_date_between=created_date_between,
                    priority_speciality_id=priority_speciality_id,
                    top_priority_speciality_id=top_priority_speciality_id,
                    sort_field=sort_field,
                    sort_dir=sort_dir,
                )
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

    @staticmethod
    def _validate_mokpp(person: PersonModel) -> None:
        """ІПН — обов'язковий і рівно 10 цифр (DK-37). Дублюємо клієнтську перевірку
        на сервері, бо клієнт може надіслати будь-що."""
        mokpp = (person.mokpp or "").strip()
        if not (mokpp.isdigit() and len(mokpp) == 10):
            raise ValueError("ІПН має містити рівно 10 цифр")

    def _validate_specialties(
        self, person: PersonModel, specialties: list[SpecialtieEntrantModel]
    ) -> None:
        """Перевіряє, що кожна обрана абітурієнтом спеціальність доступна для його бази
        вступу та обраної форми навчання в активній кампанії (DK-26). Викликається до
        відкриття пишучої сесії, щоб не плодити вкладені сесії на hot path."""
        if not specialties:
            return
        from Dekanat.services.admission_campaign import AdmissionCampaignService
        from Dekanat.services.admission_campaign_speciality import (
            AdmissionCampaignSpecialityService,
        )

        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None or campaign.id is None:
            return  # немає активної кампанії — немає з чим звіряти
        quotas = AdmissionCampaignSpecialityService().get_by_campaign(campaign.id)
        valid = {
            (q.id_speciality, q.id_entry_base, q.id_form_of_study)
            for q in quotas
        }
        base = person.id_entry_base
        for sp in specialties:
            key = (sp.id_speciality, base, sp.id_form_of_study)
            if key not in valid:
                raise ValueError(
                    "Обрана спеціальність недоступна для цієї бази вступу та форми "
                    "навчання в активній кампанії."
                )

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
            self._validate_mokpp(person)
            self._validate_specialties(person, specialties)
            with rx.session() as session:
                # Перевірка дублікатів по ІПН (mokpp): двох абітурієнтів з одним ІПН бути
                # не може. По ПІБ не перевіряємо — можливі повні тезки (DK-36).
                if person.mokpp and EntrantDao.get_person_by_mokpp(person.mokpp, session) is not None:
                    raise ValueError(f"Абітурієнт з ІПН {person.mokpp} вже існує.")
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
            self._validate_mokpp(person)
            self._validate_specialties(person, specialties)
            with rx.session() as session:
                # Дублікат по ІПН (виключаючи саму картку, що редагується) — DK-36.
                if person.mokpp and EntrantDao.get_person_by_mokpp(person.mokpp, session, exclude_id=person.id) is not None:
                    raise ValueError(f"Абітурієнт з ІПН {person.mokpp} вже існує.")
                # Preserve timestamps from existing rows and bump status_changed_at only if status really changed.
                existing_person = session.get(PersonModel, person.id)
                if existing_person is not None:
                    person.created_at = existing_person.created_at
                existing_entrant = session.get(EntrantModel, entrant.id)
                if existing_entrant is not None:
                    entrant.created_at = existing_entrant.created_at
                    if existing_entrant.id_application_status != entrant.id_application_status:
                        entrant.application_status_changed_at = datetime.now()
                    else:
                        entrant.application_status_changed_at = existing_entrant.application_status_changed_at

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
