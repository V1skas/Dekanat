"""Дії журналу для вступних кампаній (admission_campaigns, DK-55).

Скалярні поля дифаються автоматично; зміна набору квот по спеціальностях —
окреме поле `quotas`, яке сервіс виставляє вручну (кількість квот до-після).
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange


_CAMPAIGN_LABELS: Dict[str, str] = {
    "title": "Назва",
    "start_date": "Початок",
    "end_date": "Завершення",
    "quotas": "Квоти (шт.)",
}


class AdmissionCampaignCreated(CreateAction):
    table_name: ClassVar[str] = "admission_campaigns"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _CAMPAIGN_LABELS
    title: str
    start_date: str
    end_date: str


class AdmissionCampaignUpdated(UpdateAction):
    table_name: ClassVar[str] = "admission_campaigns"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _CAMPAIGN_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("title", "start_date", "end_date")
    title: Optional[FieldChange] = None
    start_date: Optional[FieldChange] = None
    end_date: Optional[FieldChange] = None
    quotas: Optional[FieldChange] = None


class AdmissionCampaignDeleted(DeleteAction):
    table_name: ClassVar[str] = "admission_campaigns"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _CAMPAIGN_LABELS
    title: str
