"""Рейтинговий список абітурієнтів у DOCX (DK-28).

Оптимізація по пам'яті:
  * `total`          — сума балів рахується на льоту (computed_field), не зберігається;
  * `recommendation` — виводиться з budget/contract на льоту, не зберігається;
  * `budget` / `contract` — два незалежні булеві поля; якщо обидва False,
    абітурієнт автоматично «Не рекомендовано до зарахування».

Ім'я директора та секретаря у звіт не передаються — вони жорстко прописані
у самому шаблоні.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, computed_field

from Dekanat.reports.base import BaseReport


class RatingApplicant(BaseModel):
    pib: str                    # ПІБ
    grades: list[Decimal]       # оцінки; порядок відповідає RatingReport.exams
    budget: bool = False        # проходить на бюджет (вкл. квоту)
    contract: bool = False      # проходить на контракт

    @computed_field
    @property
    def total(self) -> Decimal:
        # Сума на льоту — не займає місце в даних.
        return sum(self.grades, Decimal(0))

    @computed_field
    @property
    def recommendation(self) -> str:
        # Рекомендація на льоту з budget/contract.
        if self.budget or self.contract:
            return "Рекомендовано до зарахування"
        return "Не рекомендовано до зарахування"


class RatingReport(BaseReport):
    template_name: ClassVar[str] = "rating_list.docx"

    # Ім'я файлу без розширення — назва потоку без номера групи
    # (напр. «ПЗ-25дн»): tag спеціальності + рік + префікси бази/форми.
    file_stem: str

    specialty: str              # «F2 Інженерія програмного забезпечення»
    admission_base: str         # «9 класів (БЗСО)»
    budget_places: int          # Державне замовлення (бюджетні місця)
    total_places: int           # Ліцензійний обсяг (бюджет + контракт)
    report_date: date           # Pydantic сам розпарсить «2025-07-23» у date
    exams: list[str]            # назви іспитів (колонки таблиці)
    applicants: list[RatingApplicant]

    @property
    def filename(self) -> str:
        return f"{self.file_stem}.docx"

    def context(self) -> dict:
        # Передаємо самі об'єкти (а не model_dump): у шаблоні `report.*` та
        # `a.total` / `a.recommendation` звертаються до полів/property напряму,
        # а Decimal форматується фільтром `grade` (не руками).
        return {
            "report": self,
            "applicants": self.applicants,
        }
