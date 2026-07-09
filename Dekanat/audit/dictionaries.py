"""Декларативні дії журналу для довідників (DK-55).

Кожна сутність — трійка Created/Updated/Deleted. `FIELD_LABELS` — спільні для
трьох форм (укр. підписи полів), `TRACKED` у Updated перелічує скалярні поля,
що автоматично дифаються `UpdateAction.from_diff`.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange


# --- Kinship (типи родинних звʼязків) --------------------------------------

_KINSHIP_LABELS: Dict[str, str] = {"title": "Назва"}


class KinshipCreated(CreateAction):
    table_name: ClassVar[str] = "kinship"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _KINSHIP_LABELS
    title: str


class KinshipUpdated(UpdateAction):
    table_name: ClassVar[str] = "kinship"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _KINSHIP_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title",)
    title: Optional[FieldChange] = None


class KinshipDeleted(DeleteAction):
    table_name: ClassVar[str] = "kinship"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _KINSHIP_LABELS
    title: str


# --- Source of funding (джерела фінансування) ------------------------------

_SOF_LABELS: Dict[str, str] = {"title": "Назва"}


class SourceOfFundingCreated(CreateAction):
    table_name: ClassVar[str] = "source_of_funding"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SOF_LABELS
    title: str


class SourceOfFundingUpdated(UpdateAction):
    table_name: ClassVar[str] = "source_of_funding"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SOF_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title",)
    title: Optional[FieldChange] = None


class SourceOfFundingDeleted(DeleteAction):
    table_name: ClassVar[str] = "source_of_funding"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SOF_LABELS
    title: str


# --- Department (відділення) -----------------------------------------------

_DEPT_LABELS: Dict[str, str] = {"title": "Назва"}


class DepartmentCreated(CreateAction):
    table_name: ClassVar[str] = "departments"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _DEPT_LABELS
    title: str


class DepartmentUpdated(UpdateAction):
    table_name: ClassVar[str] = "departments"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _DEPT_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title",)
    title: Optional[FieldChange] = None


class DepartmentDeleted(DeleteAction):
    table_name: ClassVar[str] = "departments"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _DEPT_LABELS
    title: str


# --- Entry base (бази вступу) ----------------------------------------------

_ENTRY_BASE_LABELS: Dict[str, str] = {"title": "Назва", "prefix": "Префікс"}


class EntryBaseCreated(CreateAction):
    table_name: ClassVar[str] = "entry_base"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRY_BASE_LABELS
    title: str
    prefix: Optional[str] = None


class EntryBaseUpdated(UpdateAction):
    table_name: ClassVar[str] = "entry_base"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRY_BASE_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "prefix")
    title: Optional[FieldChange] = None
    prefix: Optional[FieldChange] = None


class EntryBaseDeleted(DeleteAction):
    table_name: ClassVar[str] = "entry_base"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ENTRY_BASE_LABELS
    title: str
    prefix: Optional[str] = None


# --- Form of study (форми навчання) ----------------------------------------

_FORM_LABELS: Dict[str, str] = {"title": "Назва", "prefix": "Префікс"}


class FormOfStudyCreated(CreateAction):
    table_name: ClassVar[str] = "forms_of_study"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _FORM_LABELS
    title: str
    prefix: Optional[str] = None


class FormOfStudyUpdated(UpdateAction):
    table_name: ClassVar[str] = "forms_of_study"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _FORM_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "prefix")
    title: Optional[FieldChange] = None
    prefix: Optional[FieldChange] = None


class FormOfStudyDeleted(DeleteAction):
    table_name: ClassVar[str] = "forms_of_study"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _FORM_LABELS
    title: str
    prefix: Optional[str] = None


# --- Identity document type (типи документів) ------------------------------

_IDT_LABELS: Dict[str, str] = {"title": "Назва", "description": "Опис"}


class IdentityDocumentTypeCreated(CreateAction):
    table_name: ClassVar[str] = "identity_document_type"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _IDT_LABELS
    title: str
    description: Optional[str] = None


class IdentityDocumentTypeUpdated(UpdateAction):
    table_name: ClassVar[str] = "identity_document_type"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _IDT_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "description")
    title: Optional[FieldChange] = None
    description: Optional[FieldChange] = None


class IdentityDocumentTypeDeleted(DeleteAction):
    table_name: ClassVar[str] = "identity_document_type"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _IDT_LABELS
    title: str
    description: Optional[str] = None


# --- Special condition (спеціальні умови, str PK subcategory_code) ----------

_SC_LABELS: Dict[str, str] = {
    "subcategory_code": "Код підкатегорії",
    "title": "Назва",
    "description": "Опис",
    "is_kvota": "Квота",
}


class SpecialConditionCreated(CreateAction):
    table_name: ClassVar[str] = "special_conditions"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SC_LABELS
    subcategory_code: str
    title: str
    is_kvota: bool


class SpecialConditionUpdated(UpdateAction):
    table_name: ClassVar[str] = "special_conditions"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SC_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "description", "is_kvota")
    title: Optional[FieldChange] = None
    description: Optional[FieldChange] = None
    is_kvota: Optional[FieldChange] = None


class SpecialConditionDeleted(DeleteAction):
    table_name: ClassVar[str] = "special_conditions"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SC_LABELS
    subcategory_code: str
    title: str


# --- Application status (статуси заявок) ------------------------------------

_AS_LABELS: Dict[str, str] = {
    "title": "Назва",
    "description": "Опис",
    "is_default": "За замовчуванням",
    "is_allowed_in_rating": "Допуск до рейтингу",
}


class ApplicationStatusCreated(CreateAction):
    table_name: ClassVar[str] = "application_statuses"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _AS_LABELS
    title: str
    is_default: bool
    is_allowed_in_rating: bool


class ApplicationStatusUpdated(UpdateAction):
    table_name: ClassVar[str] = "application_statuses"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _AS_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "description", "is_default", "is_allowed_in_rating")
    title: Optional[FieldChange] = None
    description: Optional[FieldChange] = None
    is_default: Optional[FieldChange] = None
    is_allowed_in_rating: Optional[FieldChange] = None


class ApplicationStatusDeleted(DeleteAction):
    table_name: ClassVar[str] = "application_statuses"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _AS_LABELS
    title: str


# --- Item ZNO (предмети ЗНО) ------------------------------------------------

_ITEM_ZNO_LABELS: Dict[str, str] = {
    "title": "Назва",
    "coefficient": "Коефіцієнт",
    "is_counted_in_rating": "Враховується в рейтингу",
}


class ItemZnoCreated(CreateAction):
    table_name: ClassVar[str] = "item_zno"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ITEM_ZNO_LABELS
    title: str
    coefficient: float
    is_counted_in_rating: bool


class ItemZnoUpdated(UpdateAction):
    table_name: ClassVar[str] = "item_zno"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ITEM_ZNO_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "coefficient", "is_counted_in_rating")
    title: Optional[FieldChange] = None
    coefficient: Optional[FieldChange] = None
    is_counted_in_rating: Optional[FieldChange] = None


class ItemZnoDeleted(DeleteAction):
    table_name: ClassVar[str] = "item_zno"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _ITEM_ZNO_LABELS
    title: str


# --- Speciality (спеціальності, сурогатний PK) ------------------------------

_SPEC_LABELS: Dict[str, str] = {
    "code": "Код",
    "title": "Назва",
    "tag": "Тег ОПП",
    "educational_and_professional_program": "ОПП",
    "id_department": "Відділення (id)",
}


class SpecialityCreated(CreateAction):
    table_name: ClassVar[str] = "specialties"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SPEC_LABELS
    code: str
    title: str
    tag: str
    id_department: int


class SpecialityUpdated(UpdateAction):
    table_name: ClassVar[str] = "specialties"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SPEC_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = (
        "code", "title", "tag", "educational_and_professional_program", "id_department",
    )
    code: Optional[FieldChange] = None
    title: Optional[FieldChange] = None
    tag: Optional[FieldChange] = None
    educational_and_professional_program: Optional[FieldChange] = None
    id_department: Optional[FieldChange] = None


class SpecialityDeleted(DeleteAction):
    table_name: ClassVar[str] = "specialties"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _SPEC_LABELS
    code: str
    title: str
