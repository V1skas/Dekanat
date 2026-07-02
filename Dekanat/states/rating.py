import reflex as rx

from typing import List, Dict
from pydantic import BaseModel, Field

from Dekanat.actions import Actions


class RatingGroup(BaseModel):
    spec_key: str = ""
    spec_label: str = ""
    rows: List[Dict[str, str]] = Field(default_factory=list)

from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AdmissionCampaignModel
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.services.rating import RatingService
from Dekanat.utils.display import disambiguate_pib


class ListRatingState(AppState):
    in_progress: bool = True
    generating: bool = False
    downloading: bool = False

    campaigns: List[AdmissionCampaignModel] = []
    selected_campaign_id: int = 0

    # Згорнутий стан картки фільтрів: показуються лише маркери, дата та кнопка розгортання.
    filter_collapsed: bool = False

    # "__all__" — без фільтра
    selected_spec_key: str = "__all__"
    selected_base_key: str = "__all__"
    selected_form_key: str = "__all__"

    # Кеш доступних опцій фільтрів з квот вибраної кампанії
    speciality_options: List[Dict[str, str]] = []
    base_filter_options: List[Dict[str, str]] = []
    form_filter_options: List[Dict[str, str]] = []

    # Лейбли довідників бази вступу та форми навчання (для підписів груп) — DK-26
    entry_base_labels: Dict[str, str] = {}
    form_labels: Dict[str, str] = {}

    # Згруповано за спеціальністю: окрема таблиця для кожної.
    groups: List[RatingGroup] = []

    generated_at_display: str = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.RATING_VIEW):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_progress = True
        try:
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            active = campaign_service.get_active_campaign()
            if active is not None and active.id is not None:
                self.selected_campaign_id = active.id
            elif self.campaigns:
                self.selected_campaign_id = self.campaigns[0].id or 0
            else:
                self.selected_campaign_id = 0

            self._load_reference_labels()
            self._reload_speciality_options()
            self._load_latest_snapshot()
            self.in_progress = False
        except Exception:
            self.in_progress = False
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")

    def _load_reference_labels(self):
        from Dekanat.services.entry_base import EntryBaseService
        from Dekanat.services.form_of_study import FormOfStudyService

        self.entry_base_labels = {
            str(b.id): b.title for b in EntryBaseService().get_list_items()
        }
        self.form_labels = {
            str(f.id): f.title for f in FormOfStudyService().get_list_items()
        }

    def _reload_speciality_options(self):
        from Dekanat.services.admission_campaign_speciality import (
            AdmissionCampaignSpecialityService,
        )
        # Кожна спеціальність — лише раз (квоти повторюють її для різних база/форма).
        spec_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі спеціальності"}]
        base_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі бази вступу"}]
        form_opts: List[Dict[str, str]] = [{"value": "__all__", "label": "Усі форми навчання"}]
        seen_spec: set = set()
        seen_base: set = set()
        seen_form: set = set()
        if self.selected_campaign_id:
            quotas = AdmissionCampaignSpecialityService().get_by_campaign(self.selected_campaign_id)
            for q in quotas:
                sk = str(q.id_speciality)
                if sk not in seen_spec:
                    seen_spec.add(sk)
                    label = (
                        f"{q.speciality.code} {q.speciality.title} ({q.speciality.tag})"
                        if q.speciality is not None
                        else sk
                    )
                    spec_opts.append({"value": sk, "label": label})
                bk = str(q.id_entry_base)
                if bk not in seen_base:
                    seen_base.add(bk)
                    base_opts.append({"value": bk, "label": self.entry_base_labels.get(bk, bk)})
                fk = str(q.id_form_of_study)
                if fk not in seen_form:
                    seen_form.add(fk)
                    form_opts.append({"value": fk, "label": self.form_labels.get(fk, fk)})
        self.speciality_options = spec_opts
        self.base_filter_options = base_opts
        self.form_filter_options = form_opts
        if not any(o["value"] == self.selected_spec_key for o in spec_opts):
            self.selected_spec_key = "__all__"
        if not any(o["value"] == self.selected_base_key for o in base_opts):
            self.selected_base_key = "__all__"
        if not any(o["value"] == self.selected_form_key for o in form_opts):
            self.selected_form_key = "__all__"

    def _load_latest_snapshot(self):
        self.groups = []
        self.generated_at_display = ""
        if not self.selected_campaign_id:
            return

        snapshot, entries = RatingService().get_latest_for_campaign(self.selected_campaign_id)
        if snapshot is None:
            return
        try:
            self.generated_at_display = snapshot.generated_at.strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            self.generated_at_display = str(snapshot.generated_at)

        self._fill_from_entries(entries)

    def _fill_from_entries(self, entries):
        groups_by_key: Dict[str, RatingGroup] = {}
        order: List[str] = []

        for e in entries:
            spec_only = str(e.id_speciality)
            if self.selected_spec_key != "__all__" and spec_only != self.selected_spec_key:
                continue
            if self.selected_base_key != "__all__" and str(e.id_entry_base) != self.selected_base_key:
                continue
            if self.selected_form_key != "__all__" and str(e.id_form_of_study) != self.selected_form_key:
                continue
            # Групуємо за кортежем спеціальність+база+форма — однакові спеціальності
            # з різною базою/формою показуються окремими таблицями (DK-26).
            group_key = f"{spec_only}|{e.id_entry_base}|{e.id_form_of_study}"
            spec_name = (
                f"{e.speciality.code} {e.speciality.title} ({e.speciality.tag})"
                if e.speciality is not None
                else str(e.id_speciality)
            )
            base_name = self.entry_base_labels.get(str(e.id_entry_base), "—")
            form_name = self.form_labels.get(str(e.id_form_of_study), "—")
            spec_label = f"{spec_name} · {base_name} · {form_name}"
            pib = (
                e.entrant.person.pib
                if e.entrant is not None and e.entrant.person is not None and e.entrant.person.pib
                else f"#{e.id_entrant}"
            )
            phone = (
                e.entrant.person.phone_number
                if e.entrant is not None and e.entrant.person is not None and e.entrant.person.phone_number
                else ""
            )
            if group_key not in groups_by_key:
                groups_by_key[group_key] = RatingGroup(spec_key=group_key, spec_label=spec_label, rows=[])
                order.append(group_key)
            groups_by_key[group_key].rows.append(
                {
                    "id": str(e.id_entrant),
                    "position": str(e.position),
                    "pib": pib,
                    "phone": phone,
                    "total": str(e.total_points),
                    "status": e.status,
                }
            )

        # Тезки в межах однієї таблиці (спеціальність+база+форма) розрізняємо телефоном (DK-36).
        for group in groups_by_key.values():
            display = disambiguate_pib((r["pib"], r["phone"]) for r in group.rows)
            for row, shown in zip(group.rows, display):
                row["pib"] = shown

        self.groups = [groups_by_key[k] for k in order]

    @rx.var
    def selected_campaign_id_str(self) -> str:
        return str(self.selected_campaign_id) if self.selected_campaign_id else ""

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        return [{"value": str(c.id), "label": c.title} for c in self.campaigns]

    @rx.event
    def set_selected_campaign_id(self, value: str):
        try:
            self.selected_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.selected_campaign_id = 0
        self.selected_spec_key = "__all__"
        self.selected_base_key = "__all__"
        self.selected_form_key = "__all__"
        self._reload_speciality_options()
        self._load_latest_snapshot()

    @rx.event
    def toggle_filter_collapsed(self):
        self.filter_collapsed = not self.filter_collapsed

    @rx.event
    def on_click_row(self, entrant_id: str):
        """Клік по рядку рейтингу веде на картку абітурієнта (DK-43)."""
        if not entrant_id:
            return
        return rx.redirect(routes.ENTRANT_VIEW + entrant_id)

    def _refill_from_latest(self):
        """Перерахунок груп з кешованого знімка під поточні фільтри."""
        if self.selected_campaign_id:
            _, entries = RatingService().get_latest_for_campaign(self.selected_campaign_id)
            self._fill_from_entries(entries)

    @rx.event
    def set_selected_spec_key(self, value: str):
        self.selected_spec_key = value or "__all__"
        self._refill_from_latest()

    @rx.event
    def set_selected_base_key(self, value: str):
        self.selected_base_key = value or "__all__"
        self._refill_from_latest()

    @rx.event
    def set_selected_form_key(self, value: str):
        self.selected_form_key = value or "__all__"
        self._refill_from_latest()

    @rx.event
    def on_click_generate(self):
        if not self.has_permission(Actions.RATING_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування рейтингу!")
            return
        if not self.selected_campaign_id:
            yield rx.toast.warning("Оберіть вступну кампанію!")
            return

        self.generating = True
        yield
        try:
            snapshot, entries = RatingService().generate(self.selected_campaign_id)
            try:
                self.generated_at_display = snapshot.generated_at.strftime("%Y-%m-%d %H:%M:%S")
            except AttributeError:
                self.generated_at_display = str(snapshot.generated_at)
            self._fill_from_entries(entries)
            yield rx.toast.success("Рейтинг сформовано!")
        except Exception:
            yield rx.toast.error("Під час формування рейтингу сталася помилка. Спробуйте ще раз.")
        finally:
            self.generating = False

    @rx.event
    def on_click_download_group(self, group_key: str):
        """Завантажити DOCX одного потоку (спеціальність+база+форма)."""
        if not self.has_permission(Actions.RATING_DOCX):
            yield rx.toast.error("У Вас немає дозволу на завантаження рейтингу!")
            return
        parts = group_key.split("|")
        if len(parts) != 3 or not self.selected_campaign_id:
            yield rx.toast.error("Не вдалося визначити потік для завантаження.")
            return
        spec_key = parts[0]
        base_key, form_key = parts[1], parts[2]

        self.downloading = True
        yield
        try:
            from Dekanat.reports import RatingReport

            payloads, _ = RatingService().get_documents_payload(
                self.selected_campaign_id, spec_key, base_key, form_key
            )
            if not payloads:
                yield rx.toast.warning("Немає даних для формування документа.")
                return
            report = RatingReport(**payloads[0])
            yield rx.download(data=report.render_bytes(), filename=report.filename)
        except Exception:
            yield rx.toast.error("Під час формування документа сталася помилка. Спробуйте ще раз.")
        finally:
            self.downloading = False

    def _build_current_download(self):
        """Формує DOCX по всіх потоках поточної вибірки (з урахуванням фільтрів).
        Один потік → окремий .docx, декілька → zip (по файлу на потік).
        Повертає event `rx.download` або None, якщо даних немає."""
        from Dekanat.reports import RatingReport

        payloads, _ = RatingService().get_documents_payload(
            self.selected_campaign_id,
            self.selected_spec_key,
            self.selected_base_key,
            self.selected_form_key,
        )
        if not payloads:
            return None
        if len(payloads) == 1:
            report = RatingReport(**payloads[0])
            return rx.download(data=report.render_bytes(), filename=report.filename)

        import io
        import zipfile

        buf = io.BytesIO()
        counts: Dict[str, int] = {}
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in payloads:
                report = RatingReport(**p)
                base_name = report.filename
                n = counts.get(base_name, 0)
                counts[base_name] = n + 1
                # Захист від однакових імен потоків у межах архіву.
                name = base_name if n == 0 else f"{report.file_stem} ({n + 1}).docx"
                zf.writestr(name, report.render_bytes())
        buf.seek(0)
        return rx.download(data=buf.getvalue(), filename="rating_list.zip")

    @rx.event
    def on_click_download_all(self):
        """Масове завантаження: по файлу на кожен потік поточної вибірки.
        Один потік — окремий .docx, декілька — zip-архів."""
        if not self.has_permission(Actions.RATING_DOCX):
            yield rx.toast.error("У Вас немає дозволу на завантаження рейтингу!")
            return
        if not self.selected_campaign_id:
            yield rx.toast.warning("Оберіть вступну кампанію!")
            return

        self.downloading = True
        yield
        try:
            event = self._build_current_download()
            if event is None:
                yield rx.toast.warning("Немає сформованого рейтингу для завантаження.")
                return
            yield event
        except Exception:
            yield rx.toast.error("Під час формування документів сталася помилка. Спробуйте ще раз.")
        finally:
            self.downloading = False

