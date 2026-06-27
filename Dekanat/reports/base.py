"""Базовий клас звіту (DK-27).

Кожен звіт = Pydantic-схема, що знає свій шаблон. Валідація відбувається при
створенні обʼєкта — fail-fast, поруч із викликаючим кодом. Імʼя шаблону і форма
даних склеєні на рівні класу: жодних магічних рядків, рассинхрон між шаблоном і
даними неможливий, працює автодоповнення в IDE.

Конкретні звіти живуть у `reports/<entity>.py` і реєструються у `reports/__init__.py`.
"""

from io import BytesIO
from typing import ClassVar

from pydantic import BaseModel

from Dekanat.reports.engine import render_docx


class BaseReport(BaseModel):
    """Спадкоємці зобовʼязані задати `template_name` (файл у `reports/templates/`).

    За потреби перевизначайте `context()` — щоб підготувати дані під шаблон
    (плоскі ключі, похідні поля). Дефолт віддає весь `model_dump()`.
    """

    # Імʼя файлу-шаблону у `reports/templates/`. ClassVar — не поле моделі.
    template_name: ClassVar[str]

    # Базове імʼя файлу для віддачі користувачу (без розширення). Спадкоємці
    # можуть зробити його обчислюваним через @property.
    file_basename: ClassVar[str] = "report"

    def context(self) -> dict:
        """Дані для Jinja-рендеру. Дефолт — повний дамп моделі."""
        return self.model_dump()

    @property
    def filename(self) -> str:
        """Імʼя файлу, що віддається користувачу."""
        return f"{self.file_basename}.docx"

    def render(self) -> BytesIO:
        """Відрендерити звіт у `BytesIO` (.docx)."""
        return render_docx(self.template_name, self.context())

    def render_bytes(self) -> bytes:
        """Те саме, але одразу `bytes` — зручно для `rx.download(data=...)`."""
        return self.render().getvalue()
