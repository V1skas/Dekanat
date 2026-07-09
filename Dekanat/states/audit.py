import reflex as rx

from typing import List
from pydantic import BaseModel

from Dekanat.actions import Actions
from Dekanat.states.app import AppState
from Dekanat.services.audit import AuditService


# Людські підписи дій для заголовка рядка історії.
_ACTION_LABELS = {
    "create": "Створено",
    "update": "Змінено",
    "delete": "Видалено",
    "generate": "Сформовано",
    "assign": "Склад групи",
}


class AuditRow(BaseModel):
    """Один рядок історії, вже підготовлений до рендеру.

    Наразі показуємо лише сам факт дії (Створено/Змінено/Видалено/…), без
    деталізації змінених полів. Деталі зберігаються у БД (`audit_log.changes`) —
    щоб увімкнути їх у UI, поверніть `parse_changes(log).describe()` у `_load`
    і рендер `lines` у `views/templates/audit.py` (DK-55).
    """

    kind: str = ""            # raw action — для кольору бейджа
    action_label: str = ""
    actor: str = ""
    when: str = ""


class AuditHistoryState(AppState):
    """Спільний стан блоку «Історія змін» (DK-55). Переиспользується всіма
    сторінками перегляду: на екрані одночасно лише одна, тож конфлікту немає."""

    rows: List[AuditRow] = []
    loading: bool = False

    def _load(self, table_name: str, record_id: str):
        if not self.has_permission(Actions.AUDIT_VIEW):
            self.rows = []
            return
        record_id = (record_id or "").strip()
        if not record_id or record_id in ("-1", "0"):
            self.rows = []
            return
        self.loading = True
        try:
            logs = AuditService().get_history(table_name, record_id)
            rows: List[AuditRow] = []
            for log in logs:
                try:
                    when = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    when = str(log.created_at)
                rows.append(AuditRow(
                    kind=log.action,
                    action_label=_ACTION_LABELS.get(log.action, log.action),
                    actor=(log.worker.pib if log.worker is not None and log.worker.pib else "—"),
                    when=when,
                ))
            self.rows = rows
        except Exception as e:
            print(f"[AuditHistoryState][_load][ERROR] {e}")
            self.rows = []
        finally:
            self.loading = False

    @rx.event
    def load(self, table_name: str, id_param: str = "id"):
        """Завантажити історію запису, чий id береться з path-параметра маршруту."""
        self._load(table_name, self._route_param(id_param, ""))

    @rx.event
    def load_for_key(self, table_name: str, record_id: int):
        """Завантажити історію за явним record_id (сторінки без [id] — рейтинг/звіт/налаштування).

        record_id тут — числовий id кампанії (рейтинг/звіт); у БД зберігається рядком."""
        self._load(table_name, str(record_id))
