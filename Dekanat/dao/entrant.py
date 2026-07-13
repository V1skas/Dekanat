from datetime import datetime
from typing import Sequence, Optional, Tuple
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.orm import selectinload, aliased, make_transient

from Dekanat.models import (
    EntrantModel,
    EntrantGroupModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialtieEntrantSourceOfFundingModel,
    SpecialityModel,
    SourceOfFundingModel,
    EntryBaseModel,
    ApplicationStatusModel,
    IdentityDocumentModel,
    DocumentAboutEducationModel,
    MilitaryAccountingModel,
    MedicalReferenceModel,
    InformationAboutRelativesModel,
    SpecialConditionPersonModel,
    ResultZnoModel,
)
from Dekanat.utils.db import ua_collate, ua_lower


# Поля, доступні для сортування. Маппинг ключа з UI → spec для побудови ORDER BY.
# Реалізація join'ів — у самому get_all (щоб уникнути дублювання таблиць).
SORT_FIELDS = {
    "pib",
    "created_at",
    "phone_number",
    "email",
    "entry_base",
    "source_of_funding",
    "speciality",
    "entrant_group",
    "application_status",
}


def _entrant_loaders():
    """Eager-load all relationships needed to render an entrant page."""
    return [
        selectinload(EntrantModel.application_status),
        selectinload(EntrantModel.entrant_group),
        selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality),
        selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.form_of_study),
        selectinload(EntrantModel.specialties)
        .selectinload(SpecialtieEntrantModel.accepted_sources)
        .selectinload(SpecialtieEntrantSourceOfFundingModel.source_of_funding),
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


def apply_entrant_filters(
    statement,
    *,
    pib_substring: Optional[str] = None,
    phone_substring: Optional[str] = None,
    application_status_id: Optional[int] = None,
    entry_base_id: Optional[int] = None,
    created_between: Optional[Tuple[datetime, datetime]] = None,
    created_date_between: Optional[Tuple[datetime, datetime]] = None,
    priority_speciality_id: Optional[int] = None,
    top_priority_speciality_id: Optional[int] = None,
    special_condition_code: Optional[str] = None,
    submitted_electronically: Optional[bool] = None,
):
    """Додає до statement однакові для списку абітурієнтів та списку заявок (DK-35)
    where-предикати. Передбачається, що у statement уже приєднані EntrantModel та
    PersonModel. Фільтр по is_deleted лишається за викликачем (див. `with_del`)."""
    if pib_substring:
        # ua_lower — кирилиця-aware нижній регістр (SQLite lower() її не бере), DK-36.
        q = pib_substring.strip().lower()
        statement = statement.where(ua_lower(PersonModel.pib).like(f"%{q}%"))
    if phone_substring:
        qp = phone_substring.strip().lower()
        statement = statement.where(func.lower(PersonModel.phone_number).like(f"%{qp}%"))
    if entry_base_id:
        statement = statement.where(PersonModel.id_entry_base == entry_base_id)
    if application_status_id:
        statement = statement.where(EntrantModel.id_application_status == application_status_id)
    if created_between is not None:
        start_dt, end_dt = created_between
        statement = statement.where(EntrantModel.created_at >= start_dt).where(EntrantModel.created_at <= end_dt)
    # Окремий фільтр по даті створення (конкретний день / період) — DK-34.
    # AND'иться з фільтром кампанії: обидва обмежують created_at незалежно.
    if created_date_between is not None:
        date_start, date_end = created_date_between
        statement = statement.where(EntrantModel.created_at >= date_start).where(EntrantModel.created_at <= date_end)

    # Фільтр по специальності з пріоритетів — будь-який пріоритет, не лише перший.
    if priority_speciality_id:
        spec_filter = aliased(SpecialtieEntrantModel)
        statement = statement.where(
            select(spec_filter.id_entrant)
            .where(spec_filter.id_entrant == EntrantModel.id)
            .where(spec_filter.id_speciality == priority_speciality_id)
            .exists()
        )

    # Фільтр по пріоритетній (перший пріоритет) специальності — DK-36.
    if top_priority_speciality_id:
        top_filter = aliased(SpecialtieEntrantModel)
        statement = statement.where(
            select(top_filter.id_entrant)
            .where(top_filter.id_entrant == EntrantModel.id)
            .where(top_filter.id_speciality == top_priority_speciality_id)
            .where(top_filter.priority == 1)
            .exists()
        )

    # Фільтр по спеціальній умові особи (DK-51): є хоча б один запис у
    # special_conditions_person із відповідним кодом умови.
    if special_condition_code:
        scp = aliased(SpecialConditionPersonModel)
        statement = statement.where(
            select(scp.id_person)
            .where(scp.id_person == EntrantModel.id)
            .where(scp.id_special_condition == special_condition_code)
            .exists()
        )

    # Фільтр по маркеру «подано в електронному вигляді» (DK-51).
    if submitted_electronically is not None:
        statement = statement.where(EntrantModel.submitted_electronically == submitted_electronically)
    return statement


def _apply_sort(statement, sort_field: Optional[str], sort_dir: str):
    """Додає ORDER BY до запиту з урахуванням outerjoin'ів зі справочниками.

    Для текстових полів використовуємо collation для коректного сортування
    кирилиці (`Dekanat/utils/db.py:ua_collate`): на SQLite — кастомний `UA_CI`
    (`І` між `И` та `Ї`, а не на початку, як у BINARY), на MySQL — нативний
    `utf8mb4_unicode_ci`.
    """
    direction = (sort_dir or "asc").lower()
    if direction not in ("asc", "desc"):
        direction = "asc"

    def _dir(col):
        return col.desc() if direction == "desc" else col.asc()

    def _txt(col):
        # collation у SQLAlchemy чіпляємо саме на колонку, не на функцію.
        return ua_collate(col)

    if sort_field == "pib":
        return statement.order_by(_dir(_txt(PersonModel.pib)))
    if sort_field == "created_at":
        return statement.order_by(_dir(EntrantModel.created_at))
    if sort_field == "phone_number":
        return statement.order_by(_dir(PersonModel.phone_number))
    if sort_field == "email":
        return statement.order_by(_dir(func.coalesce(PersonModel.email, "")))
    if sort_field == "entry_base":
        eb = aliased(EntryBaseModel)
        return statement.outerjoin(eb, PersonModel.id_entry_base == eb.id).order_by(_dir(_txt(eb.title)))
    if sort_field == "source_of_funding":
        sof = aliased(SourceOfFundingModel)
        return statement.outerjoin(sof, PersonModel.id_source_of_funding == sof.id).order_by(_dir(_txt(sof.title)))
    if sort_field == "entrant_group":
        eg = aliased(EntrantGroupModel)
        return statement.outerjoin(eg, EntrantModel.id_entrant_group == eg.id).order_by(_dir(_txt(eg.title)))
    if sort_field == "application_status":
        ast = aliased(ApplicationStatusModel)
        return statement.outerjoin(ast, EntrantModel.id_application_status == ast.id).order_by(_dir(_txt(ast.title)))
    if sort_field == "speciality":
        # Сортуємо по специальності з першим пріоритетом (та, що відображається у таблиці).
        sp_link = aliased(SpecialtieEntrantModel)
        sp = aliased(SpecialityModel)
        statement = (
            statement
            .outerjoin(
                sp_link,
                (sp_link.id_entrant == EntrantModel.id) & (sp_link.priority == 1),
            )
            .outerjoin(
                sp,
                sp.id == sp_link.id_speciality,
            )
        )
        return statement.order_by(_dir(sp.code), _dir(_txt(sp.title)))
    # Дефолт — за датою створення (новіші вгорі).
    return statement.order_by(EntrantModel.created_at.desc())


class EntrantDao:
    @staticmethod
    def get_all(
        session: Session,
        with_del: bool = False,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        pib_substring: Optional[str] = None,
        phone_substring: Optional[str] = None,
        application_status_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        priority_speciality_id: Optional[int] = None,
        top_priority_speciality_id: Optional[int] = None,
        special_condition_code: Optional[str] = None,
        submitted_electronically: Optional[bool] = None,
        sort_field: Optional[str] = None,
        sort_dir: str = "asc",
    ) -> Sequence[EntrantModel]:
        # Завжди джойнимо PersonModel — він потрібен і для більшості сортувань, і для пошуку по ПІБ.
        statement = (
            select(EntrantModel)
            .options(*_entrant_loaders())
            .join(PersonModel, EntrantModel.id == PersonModel.id)
        )
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        statement = apply_entrant_filters(
            statement,
            pib_substring=pib_substring,
            phone_substring=phone_substring,
            application_status_id=application_status_id,
            entry_base_id=entry_base_id,
            created_between=created_between,
            created_date_between=created_date_between,
            priority_speciality_id=priority_speciality_id,
            top_priority_speciality_id=top_priority_speciality_id,
            special_condition_code=special_condition_code,
            submitted_electronically=submitted_electronically,
        )

        # Сортування. Для полів зі звʼязаних таблиць — окремі outerjoin'и з аліасами,
        # щоб не зачепити інші where'и (ProcessingOrder/Status могли б бути уже додані).
        statement = _apply_sort(statement, sort_field, sort_dir)
        return session.exec(statement).all()

    @staticmethod
    def get_priority_view(
        session: Session,
        with_del: bool = False,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        top_priority_speciality_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
    ) -> Sequence[EntrantModel]:
        """Полегшена вибірка для представлення «Пріоритетні спеціальності» (DK-49).

        На відміну від get_all, підтягує ЛИШЕ person (для ПІБ) та specialties→speciality
        (для тегів по пріоритетах) — решта звʼязків для цієї таблиці не потрібна, тож не
        вантажимо їх у память. Фільтр — по пріоритетній спеціальності (пріоритет №1).
        Сортування — за ПІБ (UA-collation)."""
        statement = (
            select(EntrantModel)
            .options(
                selectinload(EntrantModel.person).selectinload(PersonModel.entry_base),
                selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality),
            )
            .join(PersonModel, EntrantModel.id == PersonModel.id)
        )
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        statement = apply_entrant_filters(
            statement,
            created_between=created_between,
            created_date_between=created_date_between,
            top_priority_speciality_id=top_priority_speciality_id,
            entry_base_id=entry_base_id,
        )
        statement = statement.order_by(ua_collate(PersonModel.pib).asc())
        return session.exec(statement).all()

    @staticmethod
    def get_by_id(id: int, session: Session, with_del: bool = False) -> Optional[EntrantModel]:
        statement = select(EntrantModel).options(*_entrant_loaders()).where(EntrantModel.id == id)
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        return session.exec(statement).one_or_none()

    @staticmethod
    def get_person_by_mokpp(mokpp: str, session: Session, exclude_id: Optional[int] = None) -> Optional[PersonModel]:
        """Шукає не видалену особу за ІПН (mokpp) — для перевірки дублікатів карток
        абітурієнтів (DK-36). `exclude_id` дозволяє не зачепити саму себе при edit."""
        statement = (
            select(PersonModel)
            .where(PersonModel.mokpp == mokpp)
            .where(PersonModel.is_deleted == False)
        )
        if exclude_id is not None:
            statement = statement.where(PersonModel.id != exclude_id)
        return session.exec(statement).first()

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
            item.id = None
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

    @staticmethod
    def delete_specialty_sources(entrant_id: int, session: Session) -> None:
        """Видаляє прийнятні ресурси фінансування абітурієнта (DK-59). Виконується
        ОКРЕМО і ДО `replace_specialties` — це дочірня таблиця з FK-constraint'ом на
        `specialties_entrants`, тож MariaDB не дозволить видалити батьківські рядки
        поки лишаються ці дочірні."""
        for old in session.exec(
            select(SpecialtieEntrantSourceOfFundingModel).where(
                SpecialtieEntrantSourceOfFundingModel.id_entrant == entrant_id
            )
        ).all():
            session.delete(old)
        session.flush()

    @staticmethod
    def insert_specialty_sources(
        entrant_id: int, items: list[SpecialtieEntrantSourceOfFundingModel], session: Session
    ) -> None:
        """Вставляє нові позначки прийнятних ресурсів (DK-59). Викликається ПІСЛЯ
        `replace_specialties`, щоб батьківські рядки `specialties_entrants` уже
        існували на момент вставки (FK-constraint)."""
        for item in items:
            make_transient(item)
            item.id_entrant = entrant_id
            session.add(item)
