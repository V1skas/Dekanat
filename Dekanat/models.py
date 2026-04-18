from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, Relationship, String
from typing import Optional, List
from datetime import datetime

import reflex as rx


@rx.ModelRegistry.register
class RolesActionsModel(rx.Model, table=True):
    __tablename__ = "roles_actions"

    # Table columns
    role_id: int = Field(default=None, foreign_key="roles.id", primary_key=True)
    action_id: str = Field(default=None, foreign_key="actions.id", primary_key=True)


@rx.ModelRegistry.register
class WorkersActionsModel(rx.Model, table=True):
    __tablename__ = "workers_actions"

    # Table columns
    id_user: str = Field(default=None, foreign_key="workers.id", primary_key=True)
    id_action: str = Field(default=None, foreign_key="actions.id", primary_key=True)

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
    description: Optional[str]
    # ad_tag: Optional[str]

    # Relationships
    actions: Optional[List['ActionModel']] = Relationship(link_model=RolesActionsModel)
    # workers: Optional[List['Worker']] = Relationship(back_populates="roles", link_model=WorkersRoles)


@rx.ModelRegistry.register
class ActionModel(rx.Model, table=True):
    __tablename__ = "actions"

    # Table columns
    id: str = Field(primary_key=True)
    code: str = Field(nullable=False)
    title: str
    description: Optional[str]

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

    # Relationships
    worker: Optional['WorkerModel'] = Relationship(back_populates="auth_tokens")


@rx.ModelRegistry.register
class WorkerModel(rx.Model, table=True): # type: ignore
    __tablename__ = "workers"

    # Table columns
    id: int = Field(primary_key=True)
    pib: str
    photo: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    login: str = Field(unique=True)
    password: str
    password_salt: str
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
class SpecialConditionModel(rx.Model, table=True):
    __tablename__ = "special_conditions"

    # Table columns
    subcategory_code: str = Field(primary_key=True)
    title: str = Field()
    description: Optional[str]
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
    description: Optional[str] = Field(default=None, nullable=True)
    date_of_issue: str = Field(default=None, nullable=False)

    # Relationships
    # person: Optional['Person'] = Relationship(back_populates="special_conditions")
    # special_condition: Optional['SpecialCondition'] = Relationship()


@rx.ModelRegistry.register
class PersonModel(rx.Model, table=True):
    __tablename__ = "persons"

    # Table columns
    id: int = Field(primary_key=True)
    edbo: str = Field(default=None, nullable=True)
    pib: str = Field(nullable=False)
    photo: Optional[str] = Field(nullable=True)
    citizenship: str = Field(nullable=False)
    sex: str = Field(nullable=False)
    date_of_birth: str = Field(nullable=False)
    place_of_registration_city: Optional[str] = Field(nullable=True)
    place_of_registration: str = Field(nullable=False)
    mokpp: str = Field(nullable=False)
    email: Optional[str] = Field(nullable=True)
    phone_number: str = Field(nullable=False)
    the_need_for_a_dormitory: bool = Field(nullable=False)
    id_source_of_funding: int = Field(foreign_key="source_of_funding.id")
    entry_base: str = Field(nullable=False)
    is_deleted: bool = False

    # Relationships
    source_of_funding: Optional['SourceOfFundingModel'] = Relationship()
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
    is_deleted: bool = False

    # Relationships
    exams: Optional[List['EntrantExamModel']] = Relationship()


@rx.ModelRegistry.register
class ApplicationStatusModel(rx.Model, table=True):
    __tablename__ = "application_statuses"

    # Table colums
    id: int = Field(primary_key=True)
    title: str
    description: Optional[str]
    is_deleted: bool = False


@rx.ModelRegistry.register
class EntrantModel(rx.Model, table=True):
    __tablename__ = "entrants"

    # Table columns
    id: int = Field(primary_key=True, foreign_key="persons.id")
    id_application_status: int = Field(foreign_key="application_statuses.id")
    comment: Optional[str] = Field(default=None, nullable=True)
    is_deleted: bool = False

    # Relationships
    person: 'PersonModel' = Relationship()
    application_status: ApplicationStatusModel = Relationship()
    specialties: Optional[List['SpecialtieEntrantModel']] = Relationship(sa_relationship_kwargs={"order_by": "SpecialtieEntrantModel.priority"})


@rx.ModelRegistry.register
class DocumentAboutEducationModel(rx.Model, table=True):
    __tablename__ = "document_about_education"

    # Table columns
    title: str = Field(primary_key=True)
    number: str = Field(primary_key=True)
    series: str = Field(nullable=True)
    issued_by: str = Field(nullable=True)
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="document_about_education")


@rx.ModelRegistry.register
class MilitaryAccountingModel(rx.Model, table=True):
    __tablename__ = "military_accounting"

    # Table columns
    number: str = Field(primary_key=True)
    series: str = Field(primary_key=True)
    issued_by: str = Field(nullable=True)
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="military_accounting")


@rx.ModelRegistry.register
class MedicalReferenceModel(rx.Model, table=True):
    __tablename__ = "medical_reference"

    # Table columns
    number: str
    date_of_issue: str
    id_person: int = Field(foreign_key="persons.id")

    # Relationships
    # person: Optional['PersonModel'] = Relationship(back_populates="medical_reference")


@rx.ModelRegistry.register
class IdentityDocumentTypeModel(rx.Model, table=True):
    __tablename__ = "identity_document_type"

    # Table columns
    id: int = Field(primary_key=True)
    title: str
    is_deleted: bool = False


@rx.ModelRegistry.register
class IdentityDocumentModel(rx.Model, table=True):
    __tablename__ = "identity_document"

    # Table columns
    number: str = Field(primary_key=True)
    series: str = Field(nullable=True)
    code: str = Field(nullable=True)
    issued_by: str
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
    code: str = Field(primary_key=True)
    id_department: int = Field(primary_key=True, foreign_key="departments.id")
    title: str
    educational_and_professional_program: str = Field(default=None)
    tag: str
    is_deleted: bool = False

    # Relationships
    department: Optional['DepartmentModel'] = Relationship(back_populates="specialties")


@rx.ModelRegistry.register
class SpecialtieEntrantModel(rx.Model, table=True):
    __tablename__ = "specialties_entrants"

    # Table columns
    id_entrant: int = Field(primary_key=True, foreign_key="entrants.id")
    id_specialties: str = Field(primary_key=True, foreign_key="specialties.code")
    priority: int

    # Relationships
    # entrant: Optional['EntrantModel'] = Relationship(back_populates="specialties")
    speciality: Optional['SpecialityModel'] = Relationship()


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
    is_deleted: bool = False


@rx.ModelRegistry.register
class ResultZnoModel(rx.Model, table=True):
    __tablename__ = "results_zno"

    # Table columns
    id: int = Field(primary_key=True, default=None)
    id_items_zno: int = Field(foreign_key="item_zno.id")
    id_person: int = Field(foreign_key="persons.id")
    points: int

    # Relationships
    item_zno: Optional['ItemZnoModel'] = Relationship()
    person: Optional['PersonModel'] = Relationship(back_populates="results_zno")


@rx.ModelRegistry.register
class EntrantExamModel(rx.Model, table=True):
    __tablename__ = "entrants_exams"

    # Table columns
    id_group: int = Field(primary_key=True, foreign_key="entrants_groups.id")
    id_item_zno: int = Field(primary_key=True, foreign_key="item_zno.id")
    date_time: datetime

    # Relationships
    group: Optional['EntrantGroupModel'] = Relationship(back_populates="exams")
    item_zno: Optional['ItemZnoModel'] = Relationship()
