import reflex as rx

from typing import List, Dict, Optional

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import AppSettingModel
from Dekanat.services.app_setting import AppSettingService


# Підписи розділів — порядок задає порядок виводу на сторінці.
CATEGORY_TITLES: Dict[str, str] = {
    "auth": "Авторизація",
    "users": "Користувачі",
}


class SettingDraft(rx.Base):
    key: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    value: str = ""
    value_type: str = "str"
    # Заголовок розділу для першого елемента в категорії; "" для решти.
    # Дозволяє рендерити секції одним flat rx.foreach без вкладеного циклу
    # (Reflex не дає прямо вкласти foreach по атрибуту rx.Base моделі).
    section_header: str = ""


class ListAppSettingState(AppState):
    in_progress: bool = True

    # Усі чернетки настройок (буфер для редагування на формі).
    # Відсортовані за категоріями; перший елемент кожної категорії несе section_header.
    drafts: List[SettingDraft] = []

    def _sort_and_mark_headers(self, items: List[SettingDraft]) -> List[SettingDraft]:
        by_cat: Dict[str, List[SettingDraft]] = {}
        for d in items:
            by_cat.setdefault(d.category, []).append(d)
        ordered_cats: List[str] = []
        for cat in CATEGORY_TITLES:
            if cat in by_cat:
                ordered_cats.append(cat)
        for cat in by_cat:
            if cat not in ordered_cats:
                ordered_cats.append(cat)
        result: List[SettingDraft] = []
        for cat in ordered_cats:
            for idx, d in enumerate(by_cat[cat]):
                d.section_header = CATEGORY_TITLES.get(cat, cat) if idx == 0 else ""
                result.append(d)
        return result

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SETTINGS_VIEW):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_progress = True
        try:
            service = AppSettingService()
            service.ensure_defaults()
            items = service.get_list_items()
            raw = [
                SettingDraft(
                    key=i.key,
                    category=i.category,
                    title=i.title,
                    description=i.description or "",
                    value=i.value or "",
                    value_type=i.value_type,
                )
                for i in items
            ]
            self.drafts = self._sort_and_mark_headers(raw)
            self.in_progress = False
        except Exception:
            self.in_progress = False
            yield rx.toast.error("Під час завантаження налаштувань сталася помилка.")

    @rx.event
    def set_value(self, key: str, value: str):
        # Створюємо нові обʼєкти, щоб Reflex побачив зміну (mutable in-place правки
        # rx.Base всередині списку state не завжди тригерять реренд).
        new_drafts: List[SettingDraft] = []
        for d in self.drafts:
            if d.key == key:
                new_drafts.append(SettingDraft(
                    key=d.key,
                    category=d.category,
                    title=d.title,
                    description=d.description,
                    value=value,
                    value_type=d.value_type,
                    section_header=d.section_header,
                ))
            else:
                new_drafts.append(d)
        self.drafts = new_drafts

    def _validate(self) -> Optional[str]:
        for d in self.drafts:
            if d.value_type == "int":
                try:
                    n = int(d.value)
                except (ValueError, TypeError):
                    return f"«{d.title}»: очікується ціле число."
                if d.key == "session_timeout_minutes" and n < 1:
                    return "«Час сесії, хв»: значення має бути ≥ 1."
            elif d.value_type == "bool":
                if d.value not in ("true", "false"):
                    return f"«{d.title}»: очікується true/false."
        return None

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SETTINGS_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        err = self._validate()
        if err:
            yield rx.toast.warning(err)
            return

        try:
            items = [
                AppSettingModel(
                    key=d.key,
                    category=d.category,
                    title=d.title,
                    description=d.description or None,  # type: ignore[arg-type]
                    value=d.value,
                    value_type=d.value_type,
                )
                for d in self.drafts
            ]
            AppSettingService().save_all(items)
            yield rx.toast.success("Налаштування збережено!")
        except Exception:
            yield rx.toast.error("Під час збереження сталася помилка. Спробуйте ще раз.")
