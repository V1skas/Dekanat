from typing import List, Tuple

import reflex as rx
from pydantic import BaseModel, Field

from Dekanat.states.app import AppState
from Dekanat.services.app_update import AppUpdateService


class UpdateRow(BaseModel):
    """Плоский рядок для рендеру в `rx.foreach` (DK-32). `is_header` — перший
    рядок кожного оновлення (несе version/title/дату); решта — рядки тексту.
    Плоский список замість `List[Update] з вкладеним List[Line]` — Reflex не
    дозволяє вкладений `rx.foreach` над атрибутом елемента зовнішнього
    `rx.foreach` (див. CLAUDE.md, зразок — `SettingDraft.section_header`)."""

    version: str = ""
    title: str = ""
    published_at_str: str = ""
    text: str = ""
    is_bullet: bool = False
    is_header: bool = False


def _split_lines(body: str) -> List[Tuple[str, bool]]:
    """Мінімальний ручний парсер буллет-списку замість `rx.markdown` (DK-32):
    рендер markdown у діалозі, змонтованому через `extra_app_wraps` (шапка),
    падає з `ColorModeContext` є null (перше використання `rx.markdown` у
    проєкті виявило цю несумісність). Тексти оновлень — короткі буллет-списки
    з емодзі, тож ручного розбору достатньо. Повертає (текст, чи буллет)."""
    lines: List[Tuple[str, bool]] = []
    for raw in body.split("\n"):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            lines.append((stripped[2:], True))
        else:
            lines.append((stripped, False))
    return lines


class ChangelogState(AppState):
    """Вікно історії оновлень (DK-32). Доступно будь-якому автентифікованому
    користувачу — окремого права не потребує."""

    changelog_open: bool = False
    in_progress: bool = False
    rows: List[UpdateRow] = Field(default_factory=list)

    @rx.event
    def set_changelog_open(self, value: bool):
        self.changelog_open = value

    @rx.event
    def open_changelog(self):
        if self.worker is None:
            return

        self.in_progress = True
        yield
        try:
            service = AppUpdateService()
            items = service.get_list_items()
            new_rows: List[UpdateRow] = []
            for item in items:
                lines = _split_lines(item.body) or [("", False)]
                for idx, (text, is_bullet) in enumerate(lines):
                    new_rows.append(UpdateRow(
                        version=item.version if idx == 0 else "",
                        title=(item.title or "") if idx == 0 else "",
                        published_at_str=item.published_at.strftime("%Y-%m-%d") if idx == 0 else "",
                        text=text,
                        is_bullet=is_bullet,
                        is_header=(idx == 0),
                    ))
            self.rows = new_rows
            service.mark_seen(self.worker.id, self.latest_update_id_cache)
            # Оновлюємо і в памʼяті — інакше наступний require_auth порівняє з
            # застарілим self.worker.last_seen_update_id і знову покаже маркер.
            self.worker.last_seen_update_id = self.latest_update_id_cache
            self.has_unread_update = False
            self.changelog_open = True
        except Exception:
            yield rx.toast.error("Під час завантаження історії оновлень сталася помилка.")
        finally:
            self.in_progress = False
