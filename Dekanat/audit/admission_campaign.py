"""Дії журналу для вступних кампаній (admission_campaigns, DK-55/DK-66).

Скалярні поля дифаються автоматично; зміна набору квот по спеціальностях —
окреме поле `quotas` (`CollectionChange` — додано/вилучено/змінено квоту по
спеціальності+базі+формі, з назвою та розбивкою місць по джерелах
фінансування, DK-66), яке виставляє `AdmissionCampaignSpecialityService`.
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange, FieldRow, CollectionChange


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
    quotas: Optional[CollectionChange] = None

    def has_changes(self) -> bool:
        return super().has_changes() or (self.quotas is not None and self.quotas.has_changes())

    def describe(self) -> list[str]:
        lines = super().describe()
        if self.quotas is not None and self.quotas.has_changes():
            lines.append(
                f"Квоти: додано {len(self.quotas.added)}, вилучено {len(self.quotas.removed)}, "
                f"змінено {len(self.quotas.edited)}"
            )
        return lines

    def field_rows(self) -> list[FieldRow]:
        rows = super().field_rows()
        if self.quotas is not None:
            rows.extend(self.quotas.field_rows())
        return rows


class AdmissionCampaignDeleted(DeleteAction):
    table_name: ClassVar[str] = "admission_campaigns"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _CAMPAIGN_LABELS
    title: str
