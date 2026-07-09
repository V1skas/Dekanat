"""Журнал дій користувачів (audit log, DK-55).

Декларативний підхід за аналогією з `Dekanat/reports/`:

* `base` — `FieldChange` + `BaseAuditAction`/`CreateAction`/`UpdateAction`/`DeleteAction`;
* `<entity>` — конкретні дії з `TRACKED`+`FIELD_LABELS`;
* `engine.record_action(session, actor_id, record_id, action)` — запис у сесію зміни;
* `registry.parse_changes(log)` — відновлення типізованої дії для UI (`describe()`).

Запис веде сервіс усередині своєї транзакції (атомарно зі зміною), читання —
`Dekanat/services/audit.py`.
"""

from Dekanat.audit.base import (
    FieldChange,
    BaseAuditAction,
    CreateAction,
    UpdateAction,
    DeleteAction,
    format_value,
)
from Dekanat.audit.engine import record_action
from Dekanat.audit.registry import ACTIONS, parse_changes

from Dekanat.audit.dictionaries import (
    KinshipCreated, KinshipUpdated, KinshipDeleted,
    SourceOfFundingCreated, SourceOfFundingUpdated, SourceOfFundingDeleted,
    DepartmentCreated, DepartmentUpdated, DepartmentDeleted,
    EntryBaseCreated, EntryBaseUpdated, EntryBaseDeleted,
    FormOfStudyCreated, FormOfStudyUpdated, FormOfStudyDeleted,
    IdentityDocumentTypeCreated, IdentityDocumentTypeUpdated, IdentityDocumentTypeDeleted,
    SpecialConditionCreated, SpecialConditionUpdated, SpecialConditionDeleted,
    ApplicationStatusCreated, ApplicationStatusUpdated, ApplicationStatusDeleted,
    ItemZnoCreated, ItemZnoUpdated, ItemZnoDeleted,
    SpecialityCreated, SpecialityUpdated, SpecialityDeleted,
)
from Dekanat.audit.worker import WorkerCreated, WorkerUpdated, WorkerDeleted
from Dekanat.audit.role import RoleCreated, RoleUpdated, RoleDeleted
from Dekanat.audit.entrant import EntrantCreated, EntrantUpdated, EntrantDeleted
from Dekanat.audit.entrants_group import (
    GroupCreated, GroupUpdated, GroupDeleted, GroupMembersChanged,
)
from Dekanat.audit.entrant_exam import ExamCreated, ExamUpdated, ExamDeleted
from Dekanat.audit.admission_campaign import (
    AdmissionCampaignCreated, AdmissionCampaignUpdated, AdmissionCampaignDeleted,
)
from Dekanat.audit.app_setting import AppSettingUpdated
from Dekanat.audit.reports import RatingGenerated, AdmissionReportGenerated


__all__ = [
    "FieldChange", "BaseAuditAction", "CreateAction", "UpdateAction", "DeleteAction",
    "format_value", "record_action", "ACTIONS", "parse_changes",
    "KinshipCreated", "KinshipUpdated", "KinshipDeleted",
    "SourceOfFundingCreated", "SourceOfFundingUpdated", "SourceOfFundingDeleted",
    "DepartmentCreated", "DepartmentUpdated", "DepartmentDeleted",
    "EntryBaseCreated", "EntryBaseUpdated", "EntryBaseDeleted",
    "FormOfStudyCreated", "FormOfStudyUpdated", "FormOfStudyDeleted",
    "IdentityDocumentTypeCreated", "IdentityDocumentTypeUpdated", "IdentityDocumentTypeDeleted",
    "SpecialConditionCreated", "SpecialConditionUpdated", "SpecialConditionDeleted",
    "ApplicationStatusCreated", "ApplicationStatusUpdated", "ApplicationStatusDeleted",
    "ItemZnoCreated", "ItemZnoUpdated", "ItemZnoDeleted",
    "SpecialityCreated", "SpecialityUpdated", "SpecialityDeleted",
    "WorkerCreated", "WorkerUpdated", "WorkerDeleted",
    "RoleCreated", "RoleUpdated", "RoleDeleted",
    "EntrantCreated", "EntrantUpdated", "EntrantDeleted",
    "GroupCreated", "GroupUpdated", "GroupDeleted", "GroupMembersChanged",
    "ExamCreated", "ExamUpdated", "ExamDeleted",
    "AdmissionCampaignCreated", "AdmissionCampaignUpdated", "AdmissionCampaignDeleted",
    "AppSettingUpdated",
    "RatingGenerated", "AdmissionReportGenerated",
]
