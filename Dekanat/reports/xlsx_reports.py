"""Екзаменаційні відомості у XLSX (DK-29).

Три звіти на групу абітурієнтів:
  * VidomistReport      — відомість обліку вступного випробування (шапка + таблиця);
  * VykladachamReport   — список для викладачів;
  * TelefonyReport      — список з телефонами (абітурієнта та родичів).

Дані в контекст рендеру передаються об'єктами (ExamApplicant), а не словниками —
у шаблоні доступ через `a.name` / `a.phone` / `a.relatives`.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import ClassVar

from pydantic import BaseModel

from Dekanat.reports.engine import render_xlsx


class ExamApplicant(BaseModel):
    name: str                 # ПІБ
    phone: str = ""           # телефон абітурієнта (з картки)
    relatives: str = ""       # телефони родичів з ПІБ (для листа телефонів)


class XlsxReport(BaseModel):
    """Базовий xlsx-звіт: зв'язок Pydantic-схеми з конкретним шаблоном.

    Валідація відбувається при створенні об'єкта (fail-fast). `context()`
    за замовчуванням віддає всі поля, але з applicants як об'єктами."""

    template_name: ClassVar[str]
    file_basename: ClassVar[str] = "report"
    sheet_name: ClassVar[str] = ""  # назва листа у вихідному файлі

    applicants: list[ExamApplicant]

    def context(self) -> dict:
        return {"applicants": self.applicants, "sheet_name": self.sheet_name}

    @property
    def filename(self) -> str:
        return f"{self.file_basename}.xlsx"

    def render(self) -> BytesIO:
        return render_xlsx(self.template_name, self.context())

    def render_bytes(self) -> bytes:
        return self.render().getvalue()


class VidomistReport(XlsxReport):
    template_name: ClassVar[str] = "vidomist_template.xlsx"
    file_basename: ClassVar[str] = "vidomist"
    sheet_name: ClassVar[str] = "Відомість"

    specialty: str            # «D1 Інженерія ...» — тягнеться з групи
    subject: str = ""         # форма контролю / предмет випробування
    report_date: date         # дата формування (Pydantic розпарсить ISO-рядок)
    number: str = ""          # № відомості — лишається порожнім (від руки)

    def context(self) -> dict:
        # Об'єкти, а не дамп: applicants як ExamApplicant; шапка — скалярами.
        return {
            "specialty": self.specialty,
            "subject": self.subject,
            "report_date": self.report_date,
            "number": self.number,
            "applicants": self.applicants,
            "sheet_name": self.sheet_name,
        }


class VykladachamReport(XlsxReport):
    template_name: ClassVar[str] = "spysok_vykladacham_template.xlsx"
    file_basename: ClassVar[str] = "spysok_vykladacham"
    sheet_name: ClassVar[str] = "Список викладачам"


class TelefonyReport(XlsxReport):
    template_name: ClassVar[str] = "spysok_telefony_template.xlsx"
    file_basename: ClassVar[str] = "spysok_telefony"
    sheet_name: ClassVar[str] = "Список телефони"
