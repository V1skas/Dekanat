import reflex as rx

from typing import List
from pydantic import BaseModel, Field

from Dekanat.actions import Actions
from Dekanat.states.app import AppState
from Dekanat.services.audit import AuditService
from Dekanat.audit import parse_changes, FieldRow


# Людські підписи дій для заголовка рядка історії.
_ACTION_LABELS = {
    "create": "Створено",
    "update": "Змінено",
    "delete": "Видалено",
    "generate": "Сформовано",
    "assign": "Склад групи",
}


class AuditRow(BaseModel):
    """Один рядок історії, вже підготовлений до рендеру (DK-56).

    `details` заповнюється лише якщо у користувача є право деталізації —
    сервер не відправляє деталі в payload стану без права (захист на рівні
    даних, а не лише приховування в UI)."""

    id: int = 0
    kind: str = ""            # raw action — для кольору бейджа
    action_label: str = ""
    actor: str = ""
    when: str = ""
    details: List[FieldRow] = Field(default_factory=list)


class AuditHistoryState(AppState):
    """Спільний стан блоку «Історія змін» (DK-55/DK-56). Переиспользується
    всіма сторінками перегляду: на екрані одночасно лише одна, тож конфлікту
    немає. Права — per-view (view_action/detail_action передає викликач),
    повністю незалежні: без view-права блок не показується навіть за
    наявності detail-права."""

    rows: List[AuditRow] = []
    loading: bool = False
    can_view: bool = False
    can_detail: bool = False
    expanded_ids: List[int] = []

    def _load(self, table_name: str, record_id: str, view_action: str, detail_action: str):
        self.can_view = self.has_permission(Actions(view_action))
        self.can_detail = self.has_permission(Actions(detail_action))
        self.expanded_ids = []
        if not self.can_view:
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
                details: List[FieldRow] = []
                if self.can_detail:
                    try:
                        details = parse_changes(log).field_rows()
                    except Exception as e:
                        print(f"[AuditHistoryState][parse][ERROR] {e}")
                        details = []
                rows.append(AuditRow(
                    id=log.id,
                    kind=log.action,
                    action_label=_ACTION_LABELS.get(log.action, log.action),
                    actor=(log.worker.pib if log.worker is not None and log.worker.pib else "—"),
                    when=when,
                    details=details,
                ))
            self.rows = rows
        except Exception as e:
            print(f"[AuditHistoryState][_load][ERROR] {e}")
            self.rows = []
        finally:
            self.loading = False

    @rx.event
    def load(self, table_name: str, view_action: str, detail_action: str, id_param: str = "id"):
        """Завантажити історію запису, чий id береться з path-параметра маршруту."""
        self._load(table_name, self._route_param(id_param, ""), view_action, detail_action)

    @rx.event
    def load_for_key(self, table_name: str, record_id: int, view_action: str, detail_action: str):
        """Завантажити історію за явним record_id (сторінки без [id] — рейтинг/звіт).

        record_id тут — числовий id кампанії; у БД зберігається рядком."""
        self._load(table_name, str(record_id), view_action, detail_action)

    @rx.event
    def toggle_row(self, log_id: int):
        """Розгорнути/згорнути деталізацію рядка. No-op без права деталізації."""
        if not self.can_detail:
            return
        if log_id in self.expanded_ids:
            self.expanded_ids = [i for i in self.expanded_ids if i != log_id]
        else:
            self.expanded_ids = self.expanded_ids + [log_id]
