import reflex as rx

from datetime import datetime
from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import EntrantGroupModel, EntrantModel, EntrantExamModel, AdmissionCampaignModel
from Dekanat.services.entrants_group import EntrantsGroupService
from Dekanat.services.admission_campaign import AdmissionCampaignService


# ---------- List page ----------

class ListEntrantsGroupState(AppState):
    items: Optional[Sequence[EntrantGroupModel]] = None
    in_progress: bool = True

    # Стан панелі фільтрів
    filter_open: bool = False
    filter_title: str = ""
    filter_campaign_id: int = 0  # 0 — без фільтра по кампанії
    campaigns: List[AdmissionCampaignModel] = []

    # Режим вибору груп для друку (DK-24 follow-up).
    select_mode: bool = False
    selected_ids: List[int] = []

    def _campaign_range(self):
        if not self.filter_campaign_id:
            return None
        campaign = next((c for c in self.campaigns if c.id == self.filter_campaign_id), None)
        if campaign is None:
            return None
        try:
            start_dt = datetime.strptime(campaign.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(campaign.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            return (start_dt, end_dt)
        except (ValueError, TypeError):
            return None

    def _reload_items(self):
        service = EntrantsGroupService()
        self.items = service.get_list_items(
            title=self.filter_title.strip() or None,
            created_between=self._campaign_range(),
        )

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True
            campaign_service = AdmissionCampaignService()
            self.campaigns = list(campaign_service.get_list_items())
            active = campaign_service.get_active_campaign()
            self.filter_campaign_id = active.id if active is not None else 0
            self._reload_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.ENTRANTS_GROUP_ADD)

    # --- filter panel ---

    @rx.event
    def toggle_filter(self):
        self.filter_open = not self.filter_open

    @rx.event
    def set_filter_title(self, value: str):
        self.filter_title = value
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.var
    def campaign_options(self) -> List[Dict[str, str]]:
        opts: List[Dict[str, str]] = [{"value": "0", "label": "— Без фільтра —"}]
        opts.extend({"value": str(c.id), "label": c.title} for c in self.campaigns)
        return opts

    @rx.var
    def filter_campaign_id_str(self) -> str:
        return str(self.filter_campaign_id) if self.filter_campaign_id else "0"

    @rx.event
    def set_filter_campaign_id(self, value: str):
        try:
            self.filter_campaign_id = int(value) if value else 0
        except (ValueError, TypeError):
            self.filter_campaign_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    @rx.event
    def clear_filters(self):
        self.filter_title = ""
        self.filter_campaign_id = 0
        self.in_progress = True
        yield
        try:
            self._reload_items()
        finally:
            self.in_progress = False

    # --- режим вибору груп для друку ---

    @rx.event
    def toggle_select_mode(self):
        self.select_mode = not self.select_mode
        if not self.select_mode:
            self.selected_ids = []

    @rx.event
    def select_all(self):
        if self.items is None:
            self.selected_ids = []
            return
        self.selected_ids = [it.id for it in self.items if it.id is not None]

    @rx.event
    def clear_selection(self):
        self.selected_ids = []

    @rx.event
    def toggle_selected(self, group_id: int):
        if group_id in self.selected_ids:
            self.selected_ids = [i for i in self.selected_ids if i != group_id]
        else:
            self.selected_ids = self.selected_ids + [group_id]

    @rx.var
    def selected_set(self) -> List[str]:
        """`contains`-перевірка для рендеру стану чекбокса (Reflex дозволяє
        порівняти лише з типом списку Var; ID конвертуємо в рядки)."""
        return [str(i) for i in self.selected_ids]

    @rx.event
    def on_click_print_confirm(self):
        if not self.selected_ids:
            yield rx.toast.warning("Оберіть принаймні одну групу.")
            return
        ids_str = ",".join(str(i) for i in self.selected_ids)
        self.select_mode = False
        self.selected_ids = []
        yield rx.redirect(f"{routes.ENTRANTS_GROUP_PRINT}?ids={ids_str}")


# ---------- Form state helpers ----------

def _entrant_to_row(e: EntrantModel) -> Dict[str, str]:
    return {
        "value": str(e.id),
        "label": e.person.pib if e.person is not None else f"Абітурієнт #{e.id}",
        "subtitle": e.person.phone_number if (e.person is not None and e.person.phone_number) else "",
    }


def _filter_assignable(entrants: List[EntrantModel], chosen_ids: set, query: str) -> List[Dict[str, str]]:
    """Кандидати на додавання: доступні мінус уже обрані, з пошуком за ПІБ/телефоном."""
    avail = [e for e in entrants if e.id not in chosen_ids]
    q = (query or "").lower().strip()
    if q:
        def _hit(e: EntrantModel) -> bool:
            if e.person is None:
                return False
            pib = (e.person.pib or "").lower()
            phone = (e.person.phone_number or "").lower()
            return q in pib or q in phone
        avail = [e for e in avail if _hit(e)]
    return [_entrant_to_row(e) for e in avail]


# ---------- Add page ----------

class AddEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = False

    # Список абітурієнтів, які належатимуть до групи (поки що тільки в пам'яті форми).
    entrants_in_group: List[EntrantModel] = []
    # Усі абітурієнти, доступні для додавання (вільні від інших груп).
    assignable_entrants: List[EntrantModel] = []

    add_entrant_dialog_open: bool = False
    add_entrant_dialog_search: str = ""

    def _reload_item(self):
        self.item = EntrantGroupModel()
        self.entrants_in_group = []
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""
        service = EntrantsGroupService()
        self.assignable_entrants = list(service.get_assignable_entrants(None))

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    # --- entrants management ---

    @rx.var
    def available_to_add_rows(self) -> List[Dict[str, str]]:
        return _filter_assignable(
            self.assignable_entrants,
            {e.id for e in self.entrants_in_group},
            self.add_entrant_dialog_search,
        )

    @rx.event
    def set_add_entrant_dialog_search(self, value: str):
        self.add_entrant_dialog_search = value

    @rx.event
    def open_add_entrant_dialog(self):
        self.add_entrant_dialog_search = ""
        self.add_entrant_dialog_open = True

    @rx.event
    def close_add_entrant_dialog(self):
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def pick_entrant_to_add(self, entrant_id_str: str):
        try:
            eid = int(entrant_id_str)
        except (ValueError, TypeError):
            return
        match = next((e for e in self.assignable_entrants if e.id == eid), None)
        if match is None:
            return
        if any(e.id == match.id for e in self.entrants_in_group):
            return
        self.entrants_in_group.append(match)
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def remove_entrant_from_group(self, index: int):
        if 0 <= index < len(self.entrants_in_group):
            del self.entrants_in_group[index]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntrantsGroupService()
        try:
            entrant_ids = [e.id for e in self.entrants_in_group]
            self.item = service.add_one(self.item, entrant_ids=entrant_ids)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_LIST)


# ---------- Edit page ----------

class EditEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True

    entrants_in_group: List[EntrantModel] = []
    assignable_entrants: List[EntrantModel] = []

    add_entrant_dialog_open: bool = False
    add_entrant_dialog_search: str = ""

    def _reload_item(self):
        service = EntrantsGroupService()
        group_id = int(self._route_param("id", "-1"))
        loaded = service.get_by_id(group_id)
        if loaded is not None:
            self.item = loaded
            self.entrants_in_group = list(service.get_entrants(loaded.id))
            self.assignable_entrants = list(service.get_assignable_entrants(loaded.id))
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def available_to_add_rows(self) -> List[Dict[str, str]]:
        return _filter_assignable(
            self.assignable_entrants,
            {e.id for e in self.entrants_in_group},
            self.add_entrant_dialog_search,
        )

    @rx.event
    def set_add_entrant_dialog_search(self, value: str):
        self.add_entrant_dialog_search = value

    @rx.event
    def open_add_entrant_dialog(self):
        self.add_entrant_dialog_search = ""
        self.add_entrant_dialog_open = True

    @rx.event
    def close_add_entrant_dialog(self):
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def pick_entrant_to_add(self, entrant_id_str: str):
        try:
            eid = int(entrant_id_str)
        except (ValueError, TypeError):
            return
        match = next((e for e in self.assignable_entrants if e.id == eid), None)
        if match is None:
            return
        if any(e.id == match.id for e in self.entrants_in_group):
            return
        self.entrants_in_group.append(match)
        self.add_entrant_dialog_open = False
        self.add_entrant_dialog_search = ""

    @rx.event
    def remove_entrant_from_group(self, index: int):
        if 0 <= index < len(self.entrants_in_group):
            del self.entrants_in_group[index]

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        service = EntrantsGroupService()
        try:
            entrant_ids = [e.id for e in self.entrants_in_group]
            self.item = service.edit_one(self.item, entrant_ids=entrant_ids)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_VIEW + str(self.item.id))


# ---------- View page ----------

class ViewEntrantsGroupState(AppState):
    item: EntrantGroupModel = EntrantGroupModel()
    in_process: bool = True
    downloading: bool = False

    entrants_in_group: List[EntrantModel] = []
    exams: List[EntrantExamModel] = []
    # Передзібрані рядки для таблиці іспитів: дата відформатована на сервері,
    # бо у Var[datetime] немає зручного локалізованого форматування на фронті.
    exams_display: List[Dict[str, str]] = []

    def _reload_item(self):
        service = EntrantsGroupService()
        group_id = int(self._route_param("id", "-1"))
        loaded = service.get_by_id(group_id)
        if loaded is not None:
            self.item = loaded
            self.entrants_in_group = list(service.get_entrants(loaded.id))
            self.exams = list(service.get_exams(loaded.id))
            self.exams_display = [
                {
                    "subject": (e.item_zno.title if e.item_zno is not None else "—"),
                    "date_time": f"{e.date} {e.time_start}—{e.time_end}" if e.date else "—",
                }
                for e in self.exams
            ]

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.DASHBOARD)
            else:
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(routes.ENTRANTS_GROUP_EDIT + str(self.item.id))

    @rx.event
    def on_click_print(self):
        if self.item is None or self.item.id is None:
            return rx.toast.warning("Запис не завантажено.")
        return rx.redirect(f"{routes.ENTRANTS_GROUP_PRINT}?ids={self.item.id}")

    @rx.event
    def on_click_sheet(self, kind: str):
        """Сформувати екзаменаційну відомість групи у XLSX і віддати на
        завантаження (DK-29). kind: 'vidomist' | 'vykladacham' | 'telefony'.
        Перевірка права — і на сервері (back-end)."""
        if not self.has_permission(Actions.ENTRANTS_GROUP_SHEETS):
            yield rx.toast.error("У Вас немає дозволу на формування відомостей!")
            return
        if self.item is None or self.item.id is None:
            yield rx.toast.warning("Групу не завантажено.")
            return

        self.downloading = True
        yield
        try:
            from datetime import date
            from Dekanat.reports import (
                ExamApplicant,
                VidomistReport,
                VykladachamReport,
                TelefonyReport,
            )

            payload = EntrantsGroupService().get_exam_sheet_payload(self.item.id)
            applicants = [ExamApplicant(**a) for a in payload["applicants"]]
            if not applicants:
                yield rx.toast.warning("У групі немає абітурієнтів.")
                return

            if kind == "vidomist":
                report = VidomistReport(
                    specialty=payload["specialty"],
                    subject=payload["subject"],
                    report_date=date.today(),
                    applicants=applicants,
                )
            elif kind == "vykladacham":
                report = VykladachamReport(applicants=applicants)
            elif kind == "telefony":
                report = TelefonyReport(applicants=applicants)
            else:
                yield rx.toast.error("Невідомий тип відомості.")
                return

            filename = f"{payload['group_title']}_{report.file_basename}.xlsx"
            yield rx.download(data=report.render_bytes(), filename=filename)
        except Exception:
            yield rx.toast.error("Під час формування відомості сталася помилка. Спробуйте ще раз.")
        finally:
            self.downloading = False

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = EntrantsGroupService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""


# ============================================================
# Auto-generate page (DK-24)
# ============================================================

from pydantic import BaseModel, Field


class GeneratedEntrant(BaseModel):
    id: int = 0
    pib: str = ""
    # Приоритетная (priority=1) спеціальність абітурієнта — для відображення
    # у picker'і та діалозі складу групи (DK-24 follow-up).
    spec_label: str = ""


class GeneratedGroup(BaseModel):
    title: str = ""
    spec_code: str = ""
    spec_dept: int = 0
    spec_label: str = ""
    entrants: List[GeneratedEntrant] = Field(default_factory=list)


class AutoGenerateEntrantsGroupState(AppState):
    in_progress: bool = True
    generating: bool = False
    saving: bool = False

    # Параметри генерації
    max_size: int = 25
    # Сформовані групи — тримаємо в памʼяті до натискання «Зберегти».
    generated_groups: List[GeneratedGroup] = []
    # Список «вільних» абітурієнтів кампанії, з якого можна руками додавати у групи.
    # Перерахунок робиться при кожному відкритті picker'а: підмножина = pool − ті, що
    # вже потрапили хоча б в одну сформовану групу.
    _pool: List[GeneratedEntrant] = []

    # Діалог складу групи
    composition_open: bool = False
    composition_index: int = -1

    # Picker додавання у відкриту групу
    picker_open: bool = False
    picker_search: str = ""

    # ---- Lifecycle ----

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_AUTO_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування груп!")
            yield rx.redirect(routes.DASHBOARD)
            return
        # Перевіримо що активна кампанія взагалі є — інакше форма безглузда.
        if AdmissionCampaignService().get_active_campaign() is None:
            yield rx.toast.warning("Немає активної вступної кампанії — спочатку створіть її.")
            yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
            return
        self.in_progress = False

    # ---- Form fields ----

    @rx.event
    def set_max_size(self, value: str):
        try:
            self.max_size = max(1, int(value)) if value else 1
        except (ValueError, TypeError):
            self.max_size = 1

    # ---- Запуск формування ----

    @rx.event
    def on_click_generate(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_AUTO_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування груп!")
            return
        if self.max_size < 1:
            yield rx.toast.warning("Розмір групи має бути не менше 1.")
            return

        self.generating = True
        yield  # тригер реренду перед важкою операцією
        try:
            preview = EntrantsGroupService().preview_auto_groups(self.max_size)
            self.generated_groups = [
                GeneratedGroup(
                    title=g["title"],
                    spec_code=g["spec_code"],
                    spec_dept=g["spec_dept"],
                    spec_label=g["spec_label"],
                    entrants=[
                        GeneratedEntrant(
                            id=e["id"],
                            pib=e["pib"],
                            spec_label=e.get("spec_label", g["spec_label"]),
                        )
                        for e in g["entrants"]
                    ],
                )
                for g in preview
            ]
            self._pool = [
                GeneratedEntrant(id=r["id"], pib=r["pib"], spec_label=r.get("spec_label", ""))
                for r in EntrantsGroupService().get_assignable_for_campaign()
            ]
            if not self.generated_groups:
                yield rx.toast.info("Немає кандидатів для формування груп.")
            else:
                yield rx.toast.success(f"Сформовано груп: {len(self.generated_groups)}.")
        except Exception as ex:
            print(f"[AutoGenerateEntrantsGroupState][on_click_generate][ERROR] {ex}")
            yield rx.toast.error("Під час формування трапилась помилка. Спробуйте ще раз.")
        finally:
            self.generating = False

    # ---- Composition dialog ----

    @rx.event
    def open_composition(self, index: int):
        if index < 0 or index >= len(self.generated_groups):
            return
        self.composition_index = index
        self.composition_open = True

    @rx.event
    def set_composition_open(self, value: bool):
        self.composition_open = value
        if not value:
            self.composition_index = -1

    @rx.event
    def remove_entrant_from_group(self, entrant_id: int):
        if not (0 <= self.composition_index < len(self.generated_groups)):
            return
        group = self.generated_groups[self.composition_index]
        new_group = GeneratedGroup(
            title=group.title,
            spec_code=group.spec_code,
            spec_dept=group.spec_dept,
            spec_label=group.spec_label,
            entrants=[e for e in group.entrants if e.id != entrant_id],
        )
        new_groups = list(self.generated_groups)
        new_groups[self.composition_index] = new_group
        self.generated_groups = new_groups

    # ---- Picker для ручного додавання ----

    @rx.event
    def open_picker(self):
        self.picker_search = ""
        self.picker_open = True

    @rx.event
    def set_picker_open(self, value: bool):
        self.picker_open = value
        if not value:
            self.picker_search = ""

    @rx.event
    def set_picker_search(self, value: str):
        self.picker_search = value

    @rx.event
    def add_entrant_to_group(self, entrant_id: int):
        if not (0 <= self.composition_index < len(self.generated_groups)):
            return
        # Знайдемо абітурієнта у пулі для коректного pib.
        match = next((p for p in self._pool if p.id == entrant_id), None)
        if match is None:
            return
        group = self.generated_groups[self.composition_index]
        if any(e.id == entrant_id for e in group.entrants):
            return  # уже в групі
        new_group = GeneratedGroup(
            title=group.title,
            spec_code=group.spec_code,
            spec_dept=group.spec_dept,
            spec_label=group.spec_label,
            entrants=list(group.entrants) + [
                GeneratedEntrant(id=match.id, pib=match.pib, spec_label=match.spec_label),
            ],
        )
        new_groups = list(self.generated_groups)
        new_groups[self.composition_index] = new_group
        self.generated_groups = new_groups

    # ---- Сomputed для view ----

    @rx.var
    def current_group_title(self) -> str:
        if 0 <= self.composition_index < len(self.generated_groups):
            return self.generated_groups[self.composition_index].title
        return ""

    @rx.var
    def current_group_entrants(self) -> List[GeneratedEntrant]:
        if 0 <= self.composition_index < len(self.generated_groups):
            return self.generated_groups[self.composition_index].entrants
        return []

    @rx.var
    def picker_rows(self) -> List[GeneratedEntrant]:
        """Підмножина пулу: фільтруємо за пошуком та виключаємо тих,
        хто вже доданий хоча б в одну сформовану групу."""
        taken_ids = {e.id for g in self.generated_groups for e in g.entrants}
        q = self.picker_search.strip().lower()
        rows: List[GeneratedEntrant] = []
        for p in self._pool:
            if p.id in taken_ids:
                continue
            if q and q not in p.pib.lower():
                continue
            rows.append(p)
        return rows[:200]  # не валимо UI великим списком

    @rx.var
    def group_rows(self) -> List[Dict[str, str]]:
        """Плоский список для таблиці результатів: назва, спеціальність, кількість."""
        return [
            {
                "index": str(i),
                "title": g.title,
                "spec_label": g.spec_label,
                "count": str(len(g.entrants)),
            }
            for i, g in enumerate(self.generated_groups)
        ]

    # ---- Save / cancel ----

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_AUTO_GENERATE):
            yield rx.toast.error("У Вас немає дозволу на формування груп!")
            return
        if not self.generated_groups:
            yield rx.toast.warning("Немає груп для збереження.")
            return

        # Після ручного редагування деякі групи можуть залишитися без учасників —
        # такі ігноруємо: створювати порожні групи безглуздо.
        non_empty = [g for g in self.generated_groups if g.entrants]
        if not non_empty:
            yield rx.toast.warning("Усі групи порожні — нема чого зберігати.")
            return
        skipped = len(self.generated_groups) - len(non_empty)

        self.saving = True
        yield
        try:
            payload = [
                {
                    "title": g.title,
                    "entrants": [{"id": e.id} for e in g.entrants],
                }
                for g in non_empty
            ]
            count = EntrantsGroupService().bulk_create_with_entrants(payload)
            msg = f"Збережено груп: {count}."
            if skipped:
                msg += f" Пропущено порожніх: {skipped}."
            yield rx.toast.success(msg)
            self.generated_groups = []
            self._pool = []
            yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
        except Exception as ex:
            print(f"[AutoGenerateEntrantsGroupState][on_save][ERROR] {ex}")
            yield rx.toast.error("Під час збереження трапилась помилка. Спробуйте ще раз.")
        finally:
            self.saving = False

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.ENTRANTS_GROUP_LIST)


# ============================================================
# Print page state (DK-24 follow-up)
# ============================================================


class PrintEntrantRow(BaseModel):
    pib: str = ""


class PrintGroup(BaseModel):
    id: int = 0
    title: str = ""
    entrants: List[PrintEntrantRow] = Field(default_factory=list)


class PrintEntrantsGroupState(AppState):
    in_progress: bool = True
    groups: List[PrintGroup] = []

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.ENTRANTS_GROUP_VIEW):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_progress = True
        # Парсимо ids із query (`?ids=1,2,3`). Path-params для цього маршруту нема —
        # один сценарій передає ids зі списку (декілька), інший — з view (один).
        ids_raw = ""
        try:
            ids_raw = self.router.url.query_parameters.get("ids", "") or ""
        except Exception:
            ids_raw = ""
        ids = [int(s) for s in ids_raw.split(",") if s.strip().isdigit()]
        if not ids:
            yield rx.toast.warning("Не передано жодної групи для друку.")
            yield rx.redirect(routes.ENTRANTS_GROUP_LIST)
            return

        try:
            service = EntrantsGroupService()
            collected: List[PrintGroup] = []
            for gid in ids:
                group = service.get_by_id(gid)
                if group is None:
                    continue
                entrants = service.get_entrants(gid)
                rows: List[PrintEntrantRow] = []
                for e in entrants:
                    person = e.person
                    rows.append(PrintEntrantRow(
                        pib=person.pib if person and person.pib else f"#{e.id}",
                    ))
                rows.sort(key=lambda r: r.pib.lower())
                collected.append(PrintGroup(id=group.id, title=group.title or f"#{group.id}", entrants=rows))
            self.groups = collected
            self.in_progress = False
            # Дамо браузеру намалювати таблиці, потім автоматично відкриваємо діалог друку.
            yield rx.call_script("setTimeout(() => window.print(), 300)")
        except Exception as ex:
            print(f"[PrintEntrantsGroupState][on_load][ERROR] {ex}")
            self.in_progress = False
            yield rx.toast.error("Під час завантаження сталася помилка.")

    @rx.event
    def on_click_back(self):
        return rx.redirect(routes.ENTRANTS_GROUP_LIST)

    @rx.event
    def on_click_print(self):
        return rx.call_script("window.print()")
