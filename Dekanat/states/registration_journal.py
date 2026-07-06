import reflex as rx

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.registration_journal import RegistrationJournalService
from Dekanat.utils.background import run_blocking


def _fmt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y")


class ListRegistrationJournalState(AppState):
    """Журнал реєстрації заяв (DK-30): живий перегляд + вивантаження DOCX за шаблоном.
    Без моделі/знімка — рядки читаються з даних абітурієнтів за вибраною кампанією та
    фільтром дати прийому. Дефолт — весь період активної кампанії."""

    in_progress: bool = True
    downloading: bool = False

    campaigns: List[AdmissionCampaignModel] = []
    selected_campaign_id: int = 0

    # Фільтр дати прийому (DK-34-подібний): "day" — конкретний день; "period" — діапазон.
    # Порожні поля → без звуження, тобто весь період кампанії.
    filter_date_mode: str = "day"  # "day" | "period"
    filter_date_day: str = ""
    filter_date_from: str = ""
    filter_date_to: str = ""

    rows: List[Dict[str, str]] = []
    period_label: str = ""

    # ---------- lifecycle ----------

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.REPORT_JOURNAL_VIEW):
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
            # Скидаємо фільтр дати — дефолт показує весь період кампанії.
            self.filter_date_mode = "day"
            self.filter_date_day = ""
            self.filter_date_from = ""
            self.filter_date_to = ""
            self._reload_rows()
        except Exception as ex:
            print(f"[ListRegistrationJournalState][on_load][ERROR] {ex}")
            yield rx.toast.error("Під час завантаження сталася помилка.")
        finally:
            self.in_progress = False

    # ---------- ranges / labels ----------

    def _selected_campaign(self) -> Optional[AdmissionCampaignModel]:
        return next((c for c in self.campaigns if c.id == self.selected_campaign_id), None)

    def _campaign_range(self) -> Optional[Tuple[datetime, datetime]]:
        campaign = self._selected_campaign()
        if campaign is None:
            return None
        try:
            start_dt = datetime.strptime(campaign.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(campaign.end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            return (start_dt, end_dt)
        except (ValueError, TypeError):
            return None

    def _date_range(self) -> Optional[Tuple[datetime, datetime]]:
        if self.filter_date_mode == "day":
            if not self.filter_date_day:
                return None
            try:
                day = datetime.strptime(self.filter_date_day, "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
            return (
                day.replace(hour=0, minute=0, second=0),
                day.replace(hour=23, minute=59, second=59),
            )
        if not self.filter_date_from and not self.filter_date_to:
            return None
        start_dt = datetime.min
        end_dt = datetime.max
        if self.filter_date_from:
            try:
                start_dt = datetime.strptime(self.filter_date_from, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0
                )
            except (ValueError, TypeError):
                pass
        if self.filter_date_to:
            try:
                end_dt = datetime.strptime(self.filter_date_to, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
            except (ValueError, TypeError):
                pass
        return (start_dt, end_dt)

    def _date_portion(self) -> str:
        """Людський опис обраного діапазону дат (для підзаголовка та імені файлу)."""
        dr = self._date_range()
        if dr is not None:
            if self.filter_date_mode == "day" and self.filter_date_day:
                return f"за {_fmt(dr[0])}"
            start = _fmt(dr[0]) if dr[0] != datetime.min else "початок"
            end = _fmt(dr[1]) if dr[1] != datetime.max else "тепер"
            return f"за період {start} – {end}"
        cr = self._campaign_range()
        if cr is not None:
            return f"за період {_fmt(cr[0])} – {_fmt(cr[1])}"
        return "усі заяви"

    def _build_period_label(self) -> str:
        campaign = self._selected_campaign()
        portion = self._date_portion()
        if campaign is not None:
            return f"{campaign.title} · {portion}"
        return portion

    def _file_stem(self) -> str:
        # Крапки/дефіси у датах безпечні для імені файлу; слешів немає.
        return f"Журнал реєстрації {self._date_portion()}".replace("/", "-")

    def _reload_rows(self):
        self.period_label = self._build_period_label()
        self.rows = RegistrationJournalService().get_rows(
            self._campaign_range(), self._date_range()
        )

    # ---------- computed ----------

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        return [{"value": str(c.id), "label": c.title} for c in self.campaigns]

    @rx.var
    def selected_campaign_id_str(self) -> str:
        return str(self.selected_campaign_id) if self.selected_campaign_id else ""

    @rx.var
    def is_date_mode_period(self) -> bool:
        return self.filter_date_mode == "period"

    @rx.var
    def has_rows(self) -> bool:
        return len(self.rows) > 0

    @rx.var
    def rows_count(self) -> int:
        return len(self.rows)

    # ---------- setters ----------

    def _reload_with_spinner(self):
        self.in_progress = True
        yield
        try:
            self._reload_rows()
        finally:
            self.in_progress = False

    @rx.event
    def set_selected_campaign_id(self, value: str):
        try:
            self.selected_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.selected_campaign_id = 0
        yield from self._reload_with_spinner()

    @rx.event
    def set_filter_date_mode(self, value: str):
        self.filter_date_mode = "period" if value in ("period", "Період") else "day"
        self.filter_date_day = ""
        self.filter_date_from = ""
        self.filter_date_to = ""
        yield from self._reload_with_spinner()

    @rx.event
    def set_filter_date_day(self, value: str):
        self.filter_date_day = value or ""
        yield from self._reload_with_spinner()

    @rx.event
    def set_filter_date_from(self, value: str):
        self.filter_date_from = value or ""
        yield from self._reload_with_spinner()

    @rx.event
    def set_filter_date_to(self, value: str):
        self.filter_date_to = value or ""
        yield from self._reload_with_spinner()

    # ---------- download ----------

    @rx.event
    async def on_click_download(self):
        """Формування DOCX за шаблоном. Важкий рендер винесено у фоновий потік
        (`run_blocking`) — event loop лишається вільним для інших користувачів;
        робота у потоці read-only по БД (DK-41/44). Стан знімаємо на event loop до
        виклику: діапазони й підписи рахуємо тут, у потік ідуть готові примітиви."""
        if not self.has_permission(Actions.REPORT_JOURNAL_DOCX):
            yield rx.toast.error("У Вас немає дозволу на завантаження журналу!")
            return

        created_between = self._campaign_range()
        created_date_between = self._date_range()
        period_label = self._build_period_label()
        file_stem = self._file_stem()

        self.downloading = True
        yield
        try:
            result = await run_blocking(
                self._render_document,
                created_between,
                created_date_between,
                period_label,
                file_stem,
            )
            if result is None:
                yield rx.toast.warning("Немає заяв для формування журналу.")
                return
            data, filename = result
            yield rx.download(data=data, filename=filename)
        except Exception as ex:
            print(f"[ListRegistrationJournalState][on_click_download][ERROR] {ex}")
            yield rx.toast.error("Під час формування документа сталася помилка. Спробуйте ще раз.")
        finally:
            self.downloading = False

    @staticmethod
    def _render_document(
        created_between: Optional[Tuple[datetime, datetime]],
        created_date_between: Optional[Tuple[datetime, datetime]],
        period_label: str,
        file_stem: str,
    ):
        """Блокуюча частина: читання рядків + рендер DOCX. Виконується у фоновому
        потоці — жодних мутацій стану / `yield`. Повертає `(bytes, filename)` або
        None, якщо заяв немає."""
        from Dekanat.reports import RegistrationJournalReport

        payload = RegistrationJournalService().get_document_payload(
            created_between, created_date_between, period_label, file_stem
        )
        if not payload.get("rows"):
            return None
        report = RegistrationJournalReport(**payload)
        return report.render_bytes(), report.filename
