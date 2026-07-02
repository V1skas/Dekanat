from sqlmodel import Field, Relationship
from sqlalchemy import Column, LargeBinary, DateTime, Text, Boolean, func
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.sql import expression
from typing import Optional, List
from datetime import datetime

import reflex as rx


@rx.ModelRegistry.register
class RolesActionsModel(rx.Model, table=True):
    __tablename__ = "roles_actions"

    # Table columns
    id_role: int = Field(default=None, foreign_key="roles.id", primary_key=True)
    id_action: int = Field(default=None, foreign_key="actions.id", primary_key=True)


@rx.ModelRegistry.register
class WorkersActionsModel(rx.Model, table=True):
    __tablename__ = "workers_actions"

    # Table columns
    id_worker: int = Field(default=None, foreign_key="workers.id", primary_key=True)
    id_action: int = Field(default=None, foreign_key="actions.id", primary_key=True)

@rx.ModelRegistry.register
class WorkersRolesModel(rx.Model, table=True):
    __tablename__ = "workers_roles"

    # Table columns
    id_worker: int = Field(default=None, foreign_key="workers.id", primary_key=True)
    id_role: int = Field(default=None, foreign_key="roles.id", primary_key=True)


@rx.ModelRegistry.register
class RoleModel(rx.Model, table=True):
    __tablename__ = "roles"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    is_deleted: bool = False
    # ad_tag: Optional[str]

    # Relationships
    actions: Optional[List['ActionModel']] = Relationship(link_model=RolesActionsModel)
    # workers: Optional[List['Worker']] = Relationship(back_populates="roles", link_model=WorkersRoles)


@rx.ModelRegistry.register
class ActionModel(rx.Model, table=True):
    __tablename__ = "actions"

    # Table columns
    id: int = Field(primary_key=True) # type: ignore
    code: str = Field(default=None, nullable=False, unique=True)
    title: str = Field(default=None, nullable=False)
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)

    # Relationships
    # roles: Optional[List['Role']] = Relationship(back_populates="actions", link_model=RolesActions)
    # workers: Optional[List['Worker']] = Relationship(back_populates="actions", link_model=WorkersActions)

    
@rx.ModelRegistry.register
class AuthTokenModel(rx.Model, table=True):
    __tablename__ = "auth_tokens" # type: ignore

    # Table columns
    id: int = Field(primary_key=True, nullable=True) # type: ignore
    token: str = Field(nullable=False, unique=True)
    id_worker: int = Field(foreign_key="workers.id", nullable=False)
    expires_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("expires_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    last_activity_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("last_activity_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )

    # Relationships
    worker: Optional['WorkerModel'] = Relationship(back_populates="auth_tokens")


@rx.ModelRegistry.register
class WorkerModel(rx.Model, table=True): # type: ignore
    __tablename__ = "workers"

    # Table columns
    id: int = Field(primary_key=True)
    pib: str
    photo: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    login: str = Field(unique=True)
    password: str
    password_salt: str
    permissions_version: int = Field(default=0, nullable=False)
    is_deleted: bool = False

    # Relationships
    actions: Optional[List[ActionModel]] = Relationship(link_model=WorkersActionsModel)
    roles: Optional[List[RoleModel]] = Relationship(link_model=WorkersRolesModel)
    auth_tokens: Optional[List[AuthTokenModel]] = Relationship(back_populates="worker")


@rx.ModelRegistry.register
class SourceOfFundingModel(rx.Model, table=True):
    __tablename__ = "source_of_funding"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    is_deleted: bool = False

    # Relationships
    # persons: Optional[List['Person']] = Relationship(back_populates="source_of_funding")


@rx.ModelRegistry.register
class EntryBaseModel(rx.Model, table=True):
    __tablename__ = "entry_base"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    # Префікс додається до назви екзаменаційної групи при автоформуванні (DK-26).
    prefix: str = Field(default="")
    is_deleted: bool = False


@rx.ModelRegistry.register
class FormOfStudyModel(rx.Model, table=True):
    __tablename__ = "forms_of_study"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    # Префікс додається до назви екзаменаційної групи при автоформуванні (DK-26).
    prefix: str = Field(default="")
    is_deleted: bool = False


@rx.ModelRegistry.register
class AdmissionCampaignModel(rx.Model, table=True):
    __tablename__ = "admission_campaigns"

    # Table columns
    id: int = Field(primary_key=True)
    title: str = Field(nullable=False)
    start_date: str = Field(nullable=False)  # ISO date YYYY-MM-DD
    end_date: str = Field(nullable=False)    # ISO date YYYY-MM-DD
    is_deleted: bool = False

    # Relationships
    quotas: Optional[List['AdmissionCampaignSpecialityModel']] = Relationship()


@rx.ModelRegistry.register
class AdmissionCampaignSpecialityModel(rx.Model, table=True):
    __tablename__ = "admission_campaigns_specialties"

    # Table columns
    id_admission_campaign: int = Field(primary_key=True, foreign_key="admission_campaigns.id")
    # Сурогатний FK на спеціальність (DK-38).
    id_speciality: int = Field(primary_key=True, foreign_key="specialties.id")
    # База вступу та форма навчання входять до ключа квоти: для однієї спеціальності
    # може існувати кілька квот з різними базою/формою (DK-26).
    id_entry_base: int = Field(primary_key=True, foreign_key="entry_base.id")
    id_form_of_study: int = Field(primary_key=True, foreign_key="forms_of_study.id")
    budget_places: int = Field(default=0)
    contract_places: int = Field(default=0)

    # Relationships
    speciality: Optional['SpecialityModel'] = Relationship()
    entry_base: Optional['EntryBaseModel'] = Relationship()
    form_of_study: Optional['FormOfStudyModel'] = Relationship()


@rx.ModelRegistry.register
class SpecialConditionModel(rx.Model, table=True):
    __tablename__ = "special_conditions"

    # Table columns
    subcategory_code: str = Field(primary_key=True)
    title: str = Field()
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    is_kvota: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


@rx.ModelRegistry.register
class SpecialConditionPersonModel(rx.Model, table=True):
    __tablename__ = "special_conditions_person"

    # Table columns
    id_person: int = Field(primary_key=True, foreign_key="persons.id")
    id_special_condition: str = Field(primary_key=True, foreign_key="special_conditions.subcategory_code")
    title: Optional[str] = Field(default=None, nullable=True)
    number: Optional[str] = Field(default=None, nullable=True)
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    date_of_issue: str = Field(default=None, nullable=False)

    # Relationships
    # person: Optional['Person'] = Relationship(back_populates="special_conditions")
    # special_condition: Optional['SpecialCondition'] = Relationship()


@rx.ModelRegistry.register
class PersonModel(rx.Model, table=True):
    __tablename__ = "persons"

    # Table columns
    id: int = Field(primary_key=True)
    # ЄДБО необов'язковий (DK-37): не всі абітурієнти мають код у ЄДБО на момент подачі.
    edbo: Optional[str] = Field(default=None, nullable=True)
    pib: str = Field(nullable=False)
    # На MySQL/MariaDB звичайний LargeBinary мапиться у BLOB (ліміт 64 КБ) — фото не
    # влазить і INSERT падає. LONGBLOB (до 4 ГБ) через with_variant; на SQLite лишається
    # BLOB без ліміту (DK-37).
    photo: Optional[bytes] = Field(
        default=None,
        sa_column=Column("photo", LargeBinary().with_variant(LONGBLOB(), "mysql"), nullable=True),
    )
    photo_mime_type: Optional[str] = Field(default=None, nullable=True)
    citizenship: str = Field(nullable=False)
    sex: str = Field(nullable=False)
    date_of_birth: str = Field(nullable=False)
    place_of_registration_city: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    place_of_registration: str = Field(sa_type=Text, nullable=False)
    # ІПН необов'язковий (DK-38): у частини заяв абітурієнти його не вказують.
    mokpp: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(nullable=True)
    phone_number: str = Field(nullable=False)
    the_need_for_a_dormitory: bool = Field(nullable=False)
    id_source_of_funding: int = Field(foreign_key="source_of_funding.id")
    id_entry_base: int = Field(foreign_key="entry_base.id")
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    is_deleted: bool = False

    # Relationships
    source_of_funding: Optional['SourceOfFundingModel'] = Relationship()
    entry_base: Optional['EntryBaseModel'] = Relationship()
    document_about_education: Optional[List['DocumentAboutEducationModel']] = Relationship()
    military_accounting: Optional[List['MilitaryAccountingModel']] = Relationship()
    medical_reference: Optional[List['MedicalReferenceModel']] = Relationship()
    identity_document: Optional[List['IdentityDocumentModel']] = Relationship()
    special_conditions: Optional[List['SpecialConditionPersonModel']] = Relationship()
    information_about_relatives: Optional[List['InformationAboutRelativesModel']] = Relationship()
    results_zno: Optional[List['ResultZnoModel']] = Relationship()


@rx.ModelRegistry.register
class EntrantGroupModel(rx.Model, table=True):
    __tablename__ = "entrants_groups"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    is_deleted: bool = False

    # Relationships
    exams: Optional[List['EntrantExamModel']] = Relationship()


@rx.ModelRegistry.register
class ApplicationStatusModel(rx.Model, table=True):
    __tablename__ = "application_statuses"

    # Table colums
    id: int = Field(primary_key=True)
    title: str
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    # Маркер «статус за замовчуванням для нових карток абітурієнтів» — може бути
    # лише в одного статусу (інваріант підтримується в сервісі). DK-36.
    is_default: bool = Field(
        default=False,
        sa_column=Column("is_default", Boolean, nullable=False, server_default=expression.false()),
    )
    # Чи допускається абітурієнт із цим статусом до рейтингового списку (DK-43).
    # False (дефолт) — картка не бере участі в рейтингу: у знімку вона йде у самий
    # низ списку зі статусом "excluded" і показується сірим.
    is_allowed_in_rating: bool = Field(
        default=False,
        sa_column=Column("is_allowed_in_rating", Boolean, nullable=False, server_default=expression.false()),
    )
    is_deleted: bool = False


@rx.ModelRegistry.register
class EntrantModel(rx.Model, table=True):
    __tablename__ = "entrants"

    # Table columns
    id: int = Field(primary_key=True, foreign_key="persons.id")
    id_application_status: int = Field(foreign_key="application_statuses.id")
    id_entrant_group: Optional[int] = Field(default=None, foreign_key="entrants_groups.id", nullable=True)
    comment: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    application_status_changed_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("application_status_changed_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    is_deleted: bool = False

    # Relationships
    person: 'PersonModel' = Relationship()
    application_status: ApplicationStatusModel = Relationship()
    entrant_group: Optional['EntrantGroupModel'] = Relationship()
    specialties: Optional[List['SpecialtieEntrantModel']] = Relationship(back_populates="entrant", sa_relationship_kwargs={"order_by": "SpecialtieEntrantModel.priority"})


@rx.ModelRegistry.register
class DocumentAboutEducationModel(rx.Model, table=True):
    __tablename__ = "document_about_education"

    # Table columns
    # Сурогатний id (DK-38): номер документа та дата видачі стали необов'язковими,
    # тому більше не можуть слугувати природним ключем (title, number).
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    number: Optional[str] = Field(default=None, nullable=True)
    series: str = Field(nullable=True)
    issued_by: str = Field(default=None, sa_type=Text, nullable=True)
    date_of_issue: Optional[str] = Field(default=None, nullable=True)
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="document_about_education")


@rx.ModelRegistry.register
class MilitaryAccountingModel(rx.Model, table=True):
    __tablename__ = "military_accounting"

    # Table columns
    number: str = Field(primary_key=True)
    series: str = Field(primary_key=True)
    issued_by: str = Field(default=None, sa_type=Text, nullable=True)
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="military_accounting")


@rx.ModelRegistry.register
class MedicalReferenceModel(rx.Model, table=True):
    __tablename__ = "medical_reference"

    # Table columns
    id: Optional[int] = Field(default=None, primary_key=True)
    number: str
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="medical_reference")


@rx.ModelRegistry.register
class IdentityDocumentTypeModel(rx.Model, table=True):
    __tablename__ = "identity_document_type" #type: ignore

    # Table columns
    id: int = Field(primary_key=True) #type: ignore
    title: str = ""
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    is_deleted: bool = False


@rx.ModelRegistry.register
class IdentityDocumentModel(rx.Model, table=True):
    __tablename__ = "identity_document"

    # Table columns
    number: str = Field(primary_key=True)
    series: str = Field(nullable=True)
    code: str = Field(nullable=True)
    # УНЗР та дата закінчення строку дії — необов'язкові (DK-33).
    unzr: Optional[str] = Field(default=None, nullable=True)
    date_of_expiry: Optional[str] = Field(default=None, nullable=True)
    issued_by: str = Field(sa_type=Text, nullable=False)
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")
    id_type: int = Field(primary_key=True, foreign_key="identity_document_type.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="identity_document")
    type: Optional['IdentityDocumentTypeModel'] = Relationship()


@rx.ModelRegistry.register
class DepartmentModel(rx.Model, table=True):
    __tablename__ = "departments"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    is_deleted: bool = False

    # Relationships
    specialties: Optional[List['SpecialityModel']] = Relationship(back_populates="department")


@rx.ModelRegistry.register
class SpecialityModel(rx.Model, table=True):
    __tablename__ = "specialties"

    # Table columns
    # Сурогатний PK (DK-38): дозволяє однаковий code+відділення з різними ОПП (tag).
    # Логічна унікальність (code, id_department, tag) перевіряється в сервісі серед
    # не видалених записів (без DB-констрейнта — гнучкіше з soft-delete).
    id: int = Field(primary_key=True)
    code: str
    id_department: int = Field(foreign_key="departments.id")
    title: str
    educational_and_professional_program: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    tag: str
    is_deleted: bool = False

    # Relationships
    department: Optional['DepartmentModel'] = Relationship(back_populates="specialties")


@rx.ModelRegistry.register
class SpecialtieEntrantModel(rx.Model, table=True):
    __tablename__ = "specialties_entrants"

    # Table columns
    id_entrant: int = Field(primary_key=True, foreign_key="entrants.id")
    # Сурогатний FK на спеціальність (DK-38).
    id_speciality: int = Field(primary_key=True, foreign_key="specialties.id")
    # Форма навчання входить до ключа: абітурієнт може подати ту саму спеціальність
    # з різними формами навчання, але не двічі з однаковою (обов'язкова, DK-26).
    id_form_of_study: int = Field(primary_key=True, foreign_key="forms_of_study.id")
    priority: int

    # Relationships
    entrant: Optional['EntrantModel'] = Relationship(back_populates="specialties")
    speciality: Optional['SpecialityModel'] = Relationship()
    form_of_study: Optional['FormOfStudyModel'] = Relationship()


@rx.ModelRegistry.register
class KinshipModel(rx.Model, table=True):
    __tablename__ = "kinship"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    is_deleted: bool = False


@rx.ModelRegistry.register
class InformationAboutRelativesModel(rx.Model, table=True):
    __tablename__ = "information_about_relatives"

    # Table columns
    id: Optional[int] = Field(default=None, primary_key=True)
    id_kinship: int = Field(foreign_key="kinship.id")
    pib: str
    phone_number: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    kinship: Optional['KinshipModel'] = Relationship()
    # person: Optional['PersonModel'] = Relationship(back_populates="information_about_relatives")


@rx.ModelRegistry.register
class ItemZnoModel(rx.Model, table=True):
    __tablename__ = "item_zno"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    # Ваговий коефіцієнт предмета (DK-40): бал, введений оператором або отриманий на
    # тестуванні, домножається на нього при збереженні оцінки. Дефолт 1.0 — без зміни.
    coefficient: float = Field(default=1.0, nullable=False)
    is_deleted: bool = False


@rx.ModelRegistry.register
class ResultZnoModel(rx.Model, table=True):
    __tablename__ = "results_zno"

    # Table columns
    id: int = Field(primary_key=True, default=None)
    id_items_zno: int = Field(foreign_key="item_zno.id")
    id_person: int = Field(foreign_key="persons.id")
    # Підсумковий бал = сирий × коефіцієнт предмета (обчислюється при збереженні, DK-40).
    points: int
    # Сирий бал, введений оператором / отриманий на тестуванні (до множення на
    # коефіцієнт). Потрібен, щоб діалог редагування показував саме те, що ввели,
    # і повторне збереження не домножувало вдруге (DK-40).
    points_raw: Optional[int] = Field(default=None, nullable=True)

    # Relationships
    item_zno: Optional['ItemZnoModel'] = Relationship()
    person: Optional['PersonModel'] = Relationship(back_populates="results_zno")


@rx.ModelRegistry.register
class EntrantExamWorkerModel(rx.Model, table=True):
    __tablename__ = "entrants_exams_workers"

    # Table columns
    id_exam: int = Field(primary_key=True, foreign_key="entrants_exams.id")
    id_worker: int = Field(primary_key=True, foreign_key="workers.id")


@rx.ModelRegistry.register
class EntrantExamModel(rx.Model, table=True):
    __tablename__ = "entrants_exams"

    # Table columns
    id: int = Field(primary_key=True)
    id_group: int = Field(foreign_key="entrants_groups.id")
    id_item_zno: int = Field(foreign_key="item_zno.id")
    date: str = Field(nullable=False)        # ISO date YYYY-MM-DD
    time_start: str = Field(nullable=False)  # HH:MM
    time_end: str = Field(nullable=False)    # HH:MM
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    is_deleted: bool = False

    # Relationships
    group: Optional['EntrantGroupModel'] = Relationship(back_populates="exams")
    item_zno: Optional['ItemZnoModel'] = Relationship()
    responsible_workers: Optional[List['WorkerModel']] = Relationship(link_model=EntrantExamWorkerModel)


@rx.ModelRegistry.register
class AdmissionCampaignReportModel(rx.Model, table=True):
    __tablename__ = "admission_campaign_reports"

    # Table columns
    id: int = Field(primary_key=True)
    id_campaign: int = Field(foreign_key="admission_campaigns.id", nullable=False)
    generated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("generated_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )
    # JSON payload зі звітом (числа за день/тиждень/період, серії, розподіл по
    # специальностях). Зберігаємо як рядок, щоб не плодити окремих таблиць —
    # звіт відображається цілком як знімок (DK-25). Тип Text (а не VARCHAR(255)),
    # бо JSON завідомо довший за 255 символів — на MySQL інакше «Data too long».
    payload: str = Field(sa_column=Column("payload", Text, nullable=False))


@rx.ModelRegistry.register
class AppSettingModel(rx.Model, table=True):
    __tablename__ = "app_settings"

    # Table columns
    key: str = Field(primary_key=True)
    category: str = Field(nullable=False)
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None, sa_type=Text, nullable=True)
    value: str = Field(nullable=False)
    # "int" | "str" | "bool"
    value_type: str = Field(nullable=False)


@rx.ModelRegistry.register
class RatingSnapshotModel(rx.Model, table=True):
    __tablename__ = "rating_snapshots"

    # Table columns
    id: int = Field(primary_key=True)
    id_campaign: int = Field(foreign_key="admission_campaigns.id", nullable=False)
    generated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("generated_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    )

    # Relationships
    entries: Optional[List['RatingEntryModel']] = Relationship()


@rx.ModelRegistry.register
class RatingEntryModel(rx.Model, table=True):
    __tablename__ = "rating_entries"

    # Table columns
    id: Optional[int] = Field(default=None, primary_key=True)
    id_snapshot: int = Field(foreign_key="rating_snapshots.id", nullable=False)
    # Сурогатний FK на спеціальність (DK-38).
    id_speciality: int = Field(foreign_key="specialties.id", nullable=False)
    # Квота рейтингу — за кортежем (спеціальність, база вступу, форма навчання) (DK-26).
    id_entry_base: int = Field(default=0, nullable=False)
    id_form_of_study: int = Field(default=0, nullable=False)
    id_entrant: int = Field(foreign_key="entrants.id", nullable=False)
    position: int = Field(nullable=False)
    total_points: int = Field(default=0, nullable=False)
    # 'budget' | 'contract' | 'kvota' | 'rejected' | 'excluded'
    # 'excluded' (DK-43) — статус картки не допускає до рейтингу: рядок унизу, сірий.
    status: str = Field(nullable=False)

    # Relationships
    speciality: Optional['SpecialityModel'] = Relationship()
    entrant: Optional['EntrantModel'] = Relationship()
