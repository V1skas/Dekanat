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

from openpyxl.styles import PatternFill
from openpyxl.workbook import Workbook
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

    def post_process(self, wb: Workbook) -> None:
        """Хук пост-обробки готової книги (DK-66) — за замовчуванням no-op."""
        return None

    @property
    def filename(self) -> str:
        return f"{self.file_basename}.xlsx"

    def render(self) -> BytesIO:
        return render_xlsx(self.template_name, self.context(), post_process=self.post_process)

    def render_bytes(self) -> bytes:
        return self.render().getvalue()


_UNKNOWN_SPECIALTY_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")


class VidomistReport(XlsxReport):
    template_name: ClassVar[str] = "vidomist_template.xlsx"
    file_basename: ClassVar[str] = "vidomist"
    sheet_name: ClassVar[str] = "Відомість"

    specialty: str            # «D1 Інженерія ...» — визначається за тегом групи (DK-66)
    opp: str = ""             # освітньо-професійна програма спеціальності (DK-44)
    specialty_unknown: bool = False  # тег групи не дав однозначної спеціальності (DK-66)
    subject: str = ""         # форма контролю / предмет випробування
    report_date: date         # дата формування (Pydantic розпарсить ISO-рядок)
    number: str = ""          # № відомості — лишається порожнім (від руки)

    def context(self) -> dict:
        # Об'єкти, а не дамп: applicants як ExamApplicant; шапка — скалярами.
        return {
            "specialty": self.specialty,
            "opp": self.opp,
            "subject": self.subject,
            "report_date": self.report_date,
            "number": self.number,
            "applicants": self.applicants,
            "sheet_name": self.sheet_name,
        }

    def post_process(self, wb: Workbook) -> None:
        """Якщо спеціальність за тегом групи визначити не вдалось (DK-66) —
        підсвічуємо порожні клітинки спеціальності/ОПП жовтим, щоб оператор
        помітив і заповнив вручну."""
        if not self.specialty_unknown:
            return
        ws = wb[self.sheet_name] if self.sheet_name in wb.sheetnames else wb.active
        if ws is None:
            return
        ws["D3"].fill = _UNKNOWN_SPECIALTY_FILL
        ws["D4"].fill = _UNKNOWN_SPECIALTY_FILL


class VykladachamReport(XlsxReport):
    template_name: ClassVar[str] = "spysok_vykladacham_template.xlsx"
    file_basename: ClassVar[str] = "spysok_vykladacham"
    sheet_name: ClassVar[str] = "Список викладачам"


class TelefonyReport(XlsxReport):
    template_name: ClassVar[str] = "spysok_telefony_template.xlsx"
    file_basename: ClassVar[str] = "spysok_telefony"
    sheet_name: ClassVar[str] = "Список телефони"
