from dataclasses import dataclass, field
from typing import List, Optional

from Dekanat import routes
from Dekanat.actions import Actions


@dataclass
class MenuItem:
    label: str
    icon: str
    url: Optional[str] = None
    children: List["MenuItem"] = field(default_factory=list)
    required_action: Optional[Actions] = None


MAIN: List[MenuItem] = [
    MenuItem("База знань", "book-marked", children=[
        MenuItem("Типи паспортів", "id-card", routes.IDENTITY_DOCUMENT_TYPE_LIST, required_action=Actions.IDENTITY_DOCUMENT_TYPE_LIST),
        MenuItem("Типи родичів", "users-round", routes.KINSHIP_LIST, required_action=Actions.KINSHIP_LIST),
        MenuItem("Спеціальні умови", "shield-check", routes.SPECIAL_CONDITION_LIST, required_action=Actions.SPECIAL_CONDITION_LIST),
        MenuItem("Джерела фінансування", "wallet", routes.SOURCE_OF_FUNDING_LIST, required_action=Actions.SOURCE_OF_FUNDING_LIST),
        MenuItem("Відділення", "building-2", routes.DEPARTMENT_LIST, required_action=Actions.DEPARTMENT_LIST),
        MenuItem("Спеціальності", "graduation-cap", routes.SPECIALITY_LIST, required_action=Actions.SPECIALITY_LIST),
        MenuItem("Статуси заявок", "clipboard-list", routes.APPLICATION_STATUS_LIST, required_action=Actions.APPLICATION_STATUS_LIST),
    ]),
    MenuItem("Контингент", "graduation-cap", children=[
        MenuItem("Абітурієнти", "user-plus", routes.APPLICANTS),
    ]),
    MenuItem("Адміністрування", "shield-user", children=[
        MenuItem("Користувачі", "users", routes.WORKERS_LIST, required_action=Actions.WORKER_LIST),
        MenuItem("Ролі", "key-round", routes.ROLES_LIST, required_action=Actions.ROLE_LIST),
    ]),
]
