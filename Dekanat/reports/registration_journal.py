"""Журнал реєстрації заяв вступників у DOCX (DK-30).

Офіційна форма МОН: хронологічний перелік поданих заяв з 10 колонками. Уся форматна
логіка (дати, стать, склеювання документів/пріоритетів/результатів ЗНО) живе у
`services/registration_journal.py` — сюди приходять уже готові рядки-стрічки, а шаблон
лишається «тупим». Порядок рядків = порядок реєстрації (за датою прийому документів).
"""

from __future__ import annotations

from typing import ClassVar, List

from pydantic import BaseModel, Field

from Dekanat.reports.base import BaseReport


class RegistrationJournalRow(BaseModel):
    """Один рядок журналу = один абітурієнт. Усі поля — вже відформатовані рядки
    (колонки 9–10 приходять порожніми: у системі цих даних немає, заповнюються від
    руки в готовому документі)."""

    edbo: str = ""            # 1. Номер заяви з ЄДЕБО
    accepted_at: str = ""     # 2. Дата прийому документів (dd.mm.yyyy hh:mm:ss)
    pib: str = ""             # 3. Прізвище, власне ім'я, по батькові
    sex: str = ""             # 4. Стать (Чол./Жін.)
    birth_date: str = ""      # 5. Дата народження (dd.mm.yyyy)
    education: str = ""       # 6. Документ про освіту (номер, серія, дата, тип)
    priority: str = ""        # 7. Пріоритетність заяви (не заповнюється)
    zno: str = ""             # 8. Подані результати ЗНО (предмет — бал, що беруть участь у рейтингу)
    refusal: str = ""         # 9. Причини відмови (порожньо)
    signature: str = ""       # 10. Підпис про одержання повернених документів (порожньо)


class RegistrationJournalReport(BaseReport):
    template_name: ClassVar[str] = "registration_journal.docx"

    # Заголовок і підзаголовок-період документа.
    title: str = "Журнал реєстрації заяв вступників"
    period_label: str = ""
    # Базове ім'я файлу для віддачі користувачу (без розширення) — формує state.
    file_stem: str = "Журнал реєстрації"

    rows: List[RegistrationJournalRow] = Field(default_factory=list)

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
