"""Дії журналу для формування рейтингу та звіту приймальної кампанії (DK-55).

Обидві — action="generate". record_id — id кампанії (щоб історія показувалась на
сторінці, де кампанія обирається селектором).
"""

from typing import ClassVar, Dict

from Dekanat.audit.base import BaseAuditAction


class RatingGenerated(BaseAuditAction):
    action: ClassVar[str] = "generate"
    table_name: ClassVar[str] = "rating_snapshots"
    id_campaign: int
    snapshot_id: int
    entries_count: int

    def describe(self) -> list[str]:
        return [f"Сформовано рейтинговий список (позицій: {self.entries_count})"]


class AdmissionReportGenerated(BaseAuditAction):
    action: ClassVar[str] = "generate"
    table_name: ClassVar[str] = "admission_campaign_reports"
    id_campaign: int

    def describe(self) -> list[str]:
        return ["Сформовано звіт приймальної кампанії"]
