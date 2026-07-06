"""Розклад проведення іспитів (співбесід) груп у DOCX (DK-46).

Офіційна форма коледжу: шапка (заголовок + гриф «ЗАТВЕРДЖУЮ»), таблиця «ГРУПА /
День тижня / ДАТА / ЧАС / АУДИТОРІЯ» та підпис відповідального секретаря. Уся
форматна логіка (дати, день тижня, аудиторія з опису) живе у
`services/entrant_exam.py` — сюди приходять уже готові рядки, а шаблон лишається
«тупим». Порядок рядків = порядок у графіку (за датою та часом початку).

Заголовок і підписи зашиті у самому шаблоні `exam_schedule.docx`; динамічний лише
підзаголовок-відділення (`subtitle`), що визначається за формою навчання
пріоритетної спеціальності абітурієнтів обраних груп.
"""

from __future__ import annotations

from typing import ClassVar, List

from pydantic import BaseModel, Field

from Dekanat.reports.base import BaseReport


class ExamScheduleRow(BaseModel):
    """Один рядок розкладу = один іспит групи. Усі поля — вже відформатовані рядки."""

    group: str = ""        # ГРУПА — назва групи
    weekday: str = ""      # День тижня (Понеділок … Неділя)
    date: str = ""         # ДАТА (dd.mm.yyyy)
    time: str = ""         # ЧАС (час початку, hh:mm)
    auditorium: str = ""   # АУДИТОРІЯ (беремо з поля «Опис» іспиту)


class ExamScheduleReport(BaseReport):
    template_name: ClassVar[str] = "exam_schedule.docx"

    # Підзаголовок-відділення, напр. «(заочне відділення)». Порожній рядок — коли
    # форму навчання визначити не вдалося або групи різних відділень.
    subtitle: str = ""
    # Базове ім'я файлу для віддачі користувачу (без розширення) — формує state.
    file_stem: str = "Розклад іспитів"

    rows: List[ExamScheduleRow] = Field(default_factory=list)

    @property
    def filename(self) -> str:
        return f"{self.file_stem}.docx"

    def context(self) -> dict:
        # Передаємо самі об'єкти: у шаблоні `report.*` та `r.*` звертаються до полів
        # напряму (усі вже рядки, жодних фільтрів не треба).
        return {
            "report": self,
            "rows": self.rows,
        }
