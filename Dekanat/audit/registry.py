"""Реєстр дій для зворотного читання журналу (DK-55).

`parse_changes(log)` за парою (table_name, action) відновлює типізований обʼєкт
дії з рядка `changes` — щоб UI викликав `describe()`, а не показував сирий JSON.
Невідомі пари (напр. записи старого формату) не ламають сторінку: повертається
`GenericAudit`, що просто перелічує пари ключ/значення.
"""

import json
from typing import Dict, List, Tuple, Type

from Dekanat.models import AuditLogModel
from Dekanat.audit.base import BaseAuditAction, format_value
from Dekanat.audit import dictionaries as _dic
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


class GenericAudit(BaseAuditAction):
    """Fallback для невідомих (table_name, action): показує сирі пари."""

    model_config = {"extra": "allow"}

    def describe(self) -> list[str]:
        lines: list[str] = []
        for key, value in self.__dict__.items():
            lines.append(f"{key}: {format_value(value)}")
        return lines or ["—"]


_ALL: List[Type[BaseAuditAction]] = [
    _dic.KinshipCreated, _dic.KinshipUpdated, _dic.KinshipDeleted,
    _dic.SourceOfFundingCreated, _dic.SourceOfFundingUpdated, _dic.SourceOfFundingDeleted,
    _dic.DepartmentCreated, _dic.DepartmentUpdated, _dic.DepartmentDeleted,
    _dic.EntryBaseCreated, _dic.EntryBaseUpdated, _dic.EntryBaseDeleted,
    _dic.FormOfStudyCreated, _dic.FormOfStudyUpdated, _dic.FormOfStudyDeleted,
    _dic.IdentityDocumentTypeCreated, _dic.IdentityDocumentTypeUpdated, _dic.IdentityDocumentTypeDeleted,
    _dic.SpecialConditionCreated, _dic.SpecialConditionUpdated, _dic.SpecialConditionDeleted,
    _dic.ApplicationStatusCreated, _dic.ApplicationStatusUpdated, _dic.ApplicationStatusDeleted,
    _dic.ItemZnoCreated, _dic.ItemZnoUpdated, _dic.ItemZnoDeleted,
    _dic.SpecialityCreated, _dic.SpecialityUpdated, _dic.SpecialityDeleted,
    WorkerCreated, WorkerUpdated, WorkerDeleted,
    RoleCreated, RoleUpdated, RoleDeleted,
    EntrantCreated, EntrantUpdated, EntrantDeleted,
    GroupCreated, GroupUpdated, GroupDeleted, GroupMembersChanged,
    ExamCreated, ExamUpdated, ExamDeleted,
    AdmissionCampaignCreated, AdmissionCampaignUpdated, AdmissionCampaignDeleted,
    AppSettingUpdated,
    RatingGenerated, AdmissionReportGenerated,
]

# (table_name, action) → клас дії. Пари унікальні (перевіряється нижче).
ACTIONS: Dict[Tuple[str, str], Type[BaseAuditAction]] = {}
for _cls in _ALL:
    _key = (_cls.table_name, _cls.action)
    assert _key not in ACTIONS, f"Дублікат дії журналу: {_key}"
    ACTIONS[_key] = _cls


def parse_changes(log: AuditLogModel) -> BaseAuditAction:
    action_cls = ACTIONS.get((log.table_name, log.action))
    if action_cls is None:
        try:
            data = json.loads(log.changes or "{}")
        except (ValueError, TypeError):
            data = {}
        return GenericAudit(**data)
    return action_cls.model_validate_json(log.changes)
