from dataclasses import dataclass, field
from typing import Dict, List, Optional

from Dekanat import routes
from Dekanat.actions import Actions


@dataclass
class MenuItem:
    label: str
    icon: str
    url: Optional[str] = None
    children: List["MenuItem"] = field(default_factory=list)
    required_action: Optional[Actions] = None
    # Якщо True — пункт показується лише на dashboard-сторінці свого розділу,
    # але прибраний із бічного меню. Зручно для рідкісних або «сервісних» пунктів.
    dashboard_only: bool = False


MAIN: List[MenuItem] = [
    MenuItem("База знань", "book-marked", routes.DASHBOARD_BASE, children=[
        MenuItem("Типи паспортів", "id-card", routes.IDENTITY_DOCUMENT_TYPE_LIST, required_action=Actions.IDENTITY_DOCUMENT_TYPE_LIST),
        MenuItem("Типи родичів", "users-round", routes.KINSHIP_LIST, required_action=Actions.KINSHIP_LIST),
        MenuItem("Спеціальні умови", "shield-check", routes.SPECIAL_CONDITION_LIST, required_action=Actions.SPECIAL_CONDITION_LIST),
        MenuItem("Джерела фінансування", "wallet", routes.SOURCE_OF_FUNDING_LIST, required_action=Actions.SOURCE_OF_FUNDING_LIST),
        MenuItem("Бази вступу", "book-marked", routes.ENTRY_BASE_LIST, required_action=Actions.ENTRY_BASE_LIST),
        MenuItem("Форми навчання", "book-open-check", routes.FORM_OF_STUDY_LIST, required_action=Actions.FORM_OF_STUDY_LIST),
        MenuItem("Відділення", "building-2", routes.DEPARTMENT_LIST, required_action=Actions.DEPARTMENT_LIST),
        MenuItem("Спеціальності", "graduation-cap", routes.SPECIALITY_LIST, required_action=Actions.SPECIALITY_LIST),
        MenuItem("Статуси заявок", "clipboard-list", routes.APPLICATION_STATUS_LIST, required_action=Actions.APPLICATION_STATUS_LIST),
        MenuItem("Предмети ЗНО", "book-open", routes.ITEM_ZNO_LIST, required_action=Actions.ITEM_ZNO_LIST),
    ]),
    MenuItem("Контингент", "graduation-cap", routes.DASHBOARD_CONTINGENT, children=[
        MenuItem("Абітурієнти", "user-plus", routes.ENTRANT_LIST, required_action=Actions.ENTRANT_LIST),
    ]),
    MenuItem("Приймальна комісія", "clipboard-pen", routes.DASHBOARD_ADMISSION_COMMISSION, children=[
        MenuItem("Вступні кампанії", "calendar-days", routes.ADMISSION_CAMPAIGN_LIST, required_action=Actions.ADMISSION_CAMPAIGN_LIST),
        MenuItem("Екзаменаційні групи", "users", routes.ENTRANTS_GROUP_LIST, required_action=Actions.ENTRANTS_GROUP_LIST),
        MenuItem("Графік іспитів", "calendar-clock", routes.ENTRANT_EXAM_LIST, required_action=Actions.ENTRANT_EXAM_LIST),
        MenuItem("Рейтинговий список", "list-ordered", routes.RATING_LIST, required_action=Actions.RATING_VIEW),
    ]),
    MenuItem("Звітність", "chart-line", routes.DASHBOARD_REPORTING, children=[
        MenuItem("Приймальна кампанія", "chart-pie", routes.REPORT_ADMISSION, required_action=Actions.REPORT_ADMISSION_VIEW),
    ]),
    MenuItem("Адміністрування", "shield-user", routes.DASHBOARD_ADMIN, children=[
        MenuItem("Користувачі", "users", routes.WORKERS_LIST, required_action=Actions.WORKER_LIST),
        MenuItem("Ролі", "key-round", routes.ROLES_LIST, required_action=Actions.ROLE_LIST),
        MenuItem("Налаштування", "settings", routes.SETTINGS, required_action=Actions.SETTINGS_VIEW),
    ]),
]


def find_group_by_url(url: str) -> Optional[MenuItem]:
    """Знайти верхньорівневу групу за її dashboard-маршрутом. Використовується
    рендером section-dashboard-сторінок, щоб не дублювати дерево у view-файлі."""
    for it in MAIN:
        if it.url == url:
            return it
    return None


# URL-prefix → section label. Used by the global header to display the current section.
# Each leaf menu item's URL is normalised to its entity base (e.g. ".../kinship/list" → ".../kinship");
# at request time the current path is matched against the longest base that prefixes it.
SECTION_TITLES: Dict[str, str] = {}


def _collect_section_titles(items: List[MenuItem]) -> None:
    for it in items:
        if it.url:
            base = it.url
            if base.endswith("/list"):
                base = base[: -len("/list")]
            SECTION_TITLES[base] = it.label
        if it.children:
            _collect_section_titles(it.children)


_collect_section_titles(MAIN)
SECTION_TITLES[routes.DASHBOARD] = "Головна"
