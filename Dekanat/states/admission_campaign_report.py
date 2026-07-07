import reflex as rx

from typing import Dict, List, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.admission_campaign_report import AdmissionCampaignReportService
from Dekanat.utils.background import run_blocking
from Dekanat.utils.clock import now_local


_COMPARE_NONE = "__none__"


_PERIOD_DAY = "day"
_PERIOD_WEEK = "week"
_PERIOD_PERIOD = "period"


def _empty_payload() -> Dict:
    empty_spec = {"day": [], "week": [], "period": []}
    return {
        "totals": {"today": 0, "week": 0, "period": 0},
        "week_series": [],
        "period_series": [],
        "by_spec_top": dict(empty_spec),
        "by_spec_any": dict(empty_spec),
    }


class ListAdmissionReportState(AppState):
    in_progress: bool = True
    generating: bool = False

    campaigns: List[AdmissionCampaignModel] = []
    selected_campaign_id: int = 0
    compare_campaign_id: int = 0  # 0 — без сравнения

    # Готові payload'и; ключі: "primary" / "compare".
    primary_payload: Dict = _empty_payload()
    compare_payload: Dict = _empty_payload()

    primary_generated_at: str = ""
    compare_generated_at: str = ""

    # Глобальний перемикач періоду — впливає на всі графіки/діаграми (DK-25 follow-up).
    selected_period: str = _PERIOD_PERIOD

    @rx.event
    def set_selected_period(self, value: str):
        if value in (_PERIOD_DAY, _PERIOD_WEEK, _PERIOD_PERIOD):
            self.selected_period = value

    @rx.var
    def is_period_day(self) -> bool:
        return self.selected_period == _PERIOD_DAY

    @rx.var
    def is_period_week(self) -> bool:
        return self.selected_period == _PERIOD_WEEK

    @rx.var
    def is_period_period(self) -> bool:
        return self.selected_period == _PERIOD_PERIOD

    # ---- Lifecycle ----

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.REPORT_ADMISSION_VIEW):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_progress = True
        try:
            svc = AdmissionCampaignService()
            self.campaigns = list(svc.get_list_items())
            active = svc.get_active_campaign()
            if active is not None and active.id is not None:
                self.selected_campaign_id = active.id
            elif self.campaigns:
                self.selected_campaign_id = self.campaigns[0].id or 0
            else:
                self.selected_campaign_id = 0
            self.compare_campaign_id = 0
            self._reload_primary()
            self._reload_compare()
        except Exception as ex:
            print(f"[ListAdmissionReportState][on_load][ERROR] {ex}")
            yield rx.toast.error("Під час завантаження сталася помилка.")
        finally:
            self.in_progress = False

    def _reload_primary(self):
        if not self.selected_campaign_id:
            self.primary_payload = _empty_payload()
            self.primary_generated_at = ""
            return
        payload, generated_at = AdmissionCampaignReportService().get_payload(self.selected_campaign_id)
        if payload is None:
            self.primary_payload = _empty_payload()
            self.primary_generated_at = ""
            return
        self.primary_payload = payload
        self.primary_generated_at = (
            generated_at.strftime("%Y-%m-%d %H:%M:%S") if generated_at is not None else ""
        )

    def _reload_compare(self):
        if not self.compare_campaign_id:
            self.compare_payload = _empty_payload()
            self.compare_generated_at = ""
            return
        payload, generated_at = AdmissionCampaignReportService().get_payload(self.compare_campaign_id)
        if payload is None:
            self.compare_payload = _empty_payload()
            self.compare_generated_at = ""
            return
        self.compare_payload = payload
        self.compare_generated_at = (
            generated_at.strftime("%Y-%m-%d %H:%M:%S") if generated_at is not None else ""
        )

    # ---- selects ----

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        return [{"value": str(c.id), "label": c.title} for c in self.campaigns]

    @rx.var
    def compare_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": _COMPARE_NONE, "label": "— Без порівняння —"}]
        opts.extend(
            {"value": str(c.id), "label": c.title}
            for c in self.campaigns
            if c.id != self.selected_campaign_id
        )
        return opts

    @rx.var
    def selected_campaign_id_str(self) -> str:
        return str(self.selected_campaign_id) if self.selected_campaign_id else ""

    @rx.var
    def compare_campaign_id_str(self) -> str:
        return str(self.compare_campaign_id) if self.compare_campaign_id else _COMPARE_NONE

    @rx.event
    def set_selected_campaign_id(self, value: str):
        try:
            self.selected_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.selected_campaign_id = 0
        # Якщо в compare випадково обрана та сама — скидаємо.
        if self.compare_campaign_id == self.selected_campaign_id:
            self.compare_campaign_id = 0
        self._reload_primary()
        self._reload_compare()

    @rx.event
    def set_compare_campaign_id(self, value: str):
        if not value or value == _COMPARE_NONE:
            self.compare_campaign_id = 0
        else:
            try:
                self.compare_campaign_id = int(value)
            except (ValueError, TypeError):
                self.compare_campaign_id = 0
        self._reload_compare()

    # ---- generate ----

    @rx.event
    async def on_click_generate(self):
        """Формування звіту. Важкий read-only розрахунок payload винесено у фоновий
        потік (`run_blocking`), щоб не блокувати event loop іншим користувачам
        (DK-44). Запис знімка робимо на event loop — INSERT у потік не виносимо
        (SQLite `database is locked`)."""
        if not self.has_permission(Actions.REPORT_ADMISSION_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування звіту!")
            return
        if not self.selected_campaign_id:
            yield rx.toast.warning("Оберіть кампанію.")
            return
        if self.selected_campaign_ended:
            yield rx.toast.error("Кампанія вже завершена — формування звіту недоступне.")
            return
        self.generating = True
        yield
        try:
            campaign_id = self.selected_campaign_id
            service = AdmissionCampaignReportService()
            payload = await run_blocking(service.compute_payload, campaign_id)
            service.persist_payload(campaign_id, payload)
            self._reload_primary()
            yield rx.toast.success("Звіт сформовано.")
        except Exception as ex:
            print(f"[ListAdmissionReportState][on_click_generate][ERROR] {ex}")
            yield rx.toast.error("Під час формування звіту сталася помилка.")
        finally:
            self.generating = False

    # ---- View-ready computed vars ----
    # Reflex погано працює з вкладеним dict як `Var` — рендеримо через
    # плоскі computed vars, які беруть з payload'у потрібні зрізи.

    # totals
    @rx.var
    def total_today_primary(self) -> int:
        return int(self.primary_payload.get("totals", {}).get("today", 0))

    @rx.var
    def total_week_primary(self) -> int:
        return int(self.primary_payload.get("totals", {}).get("week", 0))

    @rx.var
    def total_period_primary(self) -> int:
        return int(self.primary_payload.get("totals", {}).get("period", 0))

    @rx.var
    def total_today_compare(self) -> int:
        return int(self.compare_payload.get("totals", {}).get("today", 0))

    @rx.var
    def total_week_compare(self) -> int:
        return int(self.compare_payload.get("totals", {}).get("week", 0))

    @rx.var
    def total_period_compare(self) -> int:
        return int(self.compare_payload.get("totals", {}).get("period", 0))

    @rx.var
    def selected_campaign_ended(self) -> bool:
        """Чи завершилася обрана кампанія (end_date у минулому) — DK-51.
        Для таких кампаній формування звіту заборонене."""
        campaign = next((c for c in self.campaigns if c.id == self.selected_campaign_id), None)
        if campaign is None or not campaign.end_date:
            return False
        return campaign.end_date < now_local().date().isoformat()

    @rx.var
    def has_report(self) -> bool:
        return self.primary_generated_at != ""

    @rx.var
    def has_compare(self) -> bool:
        return self.compare_campaign_id > 0

    @rx.var
    def compare_has_report(self) -> bool:
        return self.compare_generated_at != ""

    # --- day bar ---
    @rx.var
    def day_bar_data(self) -> List[Dict]:
        """Дані для стовпчикової діаграми «за сьогодні». Один запис «Сьогодні»
        з полями для основної та (опційно) порівняльної кампанії."""
        row: Dict = {
            "label": "Сьогодні",
            "primary": self.total_today_primary,
        }
        if self.compare_campaign_id > 0:
            row["compare"] = self.total_today_compare
        return [row]

    # --- series (week / period) ---
    @rx.var
    def week_series_data(self) -> List[Dict]:
        return self._merge_series(
            self.primary_payload.get("week_series", []),
            self.compare_payload.get("week_series", []) if self.has_compare else [],
        )

    @rx.var
    def period_series_data(self) -> List[Dict]:
        return self._merge_series(
            self.primary_payload.get("period_series", []),
            self.compare_payload.get("period_series", []) if self.has_compare else [],
        )

    def _merge_series(self, primary: List[Dict], compare: List[Dict]) -> List[Dict]:
        """Зливаємо дві серії за полем `date`. Якщо порівняння не задано —
        просто рендеримо primary. Дати, відсутні в одній зі сторін, отримають 0."""
        if not compare:
            return [{"date": r["date"], "primary": r["count"]} for r in primary]
        p_map = {r["date"]: r["count"] for r in primary}
        c_map = {r["date"]: r["count"] for r in compare}
        # Якщо у компарованій кампанії інші дати (інший період) — показуємо обидві
        # серії «вирівняними по порядку», а не по конкретних датах. Це чесніше для
        # порівняння двох кампаній різних років.
        max_n = max(len(primary), len(compare))
        out: List[Dict] = []
        for i in range(max_n):
            p = primary[i] if i < len(primary) else None
            c = compare[i] if i < len(compare) else None
            label = p["date"] if p is not None else (c["date"] if c is not None else f"#{i}")
            out.append({
                "date": label,
                "primary": p["count"] if p is not None else 0,
                "compare": c["count"] if c is not None else 0,
            })
        # допоможемо unused warnings; референси про всяк випадок
        _ = (p_map, c_map)
        return out

    # --- pies (по обраному періоду) ---

    def _spec_bucket(self, payload: Dict, key: str) -> List[Dict]:
        """Зворотна сумісність: payload може бути або словником {day/week/period},
        або старим плоским списком (для старих знімків, де ще не було розбиття)."""
        raw = payload.get(key, {})
        if isinstance(raw, dict):
            rows = raw.get(self.selected_period, [])
        else:
            rows = raw  # legacy
        return [{"name": r["spec"], "value": int(r["count"])} for r in rows]

    @rx.var
    def spec_top_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "by_spec_top")

    @rx.var
    def spec_any_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "by_spec_any")

    @rx.var
    def spec_top_compare(self) -> List[Dict]:
        return self._spec_bucket(self.compare_payload, "by_spec_top")

    @rx.var
    def spec_any_compare(self) -> List[Dict]:
        return self._spec_bucket(self.compare_payload, "by_spec_any")

    # --- нові зрізи DK-26 (по обраному періоду) ---

    @rx.var
    def by_entry_base_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "by_entry_base")

    @rx.var
    def by_entry_base_compare(self) -> List[Dict]:
        return self._spec_bucket(self.compare_payload, "by_entry_base")

    @rx.var
    def by_form_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "by_form")

    @rx.var
    def by_form_compare(self) -> List[Dict]:
        return self._spec_bucket(self.compare_payload, "by_form")

    @rx.var
    def totals_by_spec_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "totals_by_spec")

    @rx.var
    def totals_by_department_primary(self) -> List[Dict]:
        return self._spec_bucket(self.primary_payload, "totals_by_department")
