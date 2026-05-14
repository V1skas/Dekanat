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
    ]),
    MenuItem("Контингент", "graduation-cap", children=[
        MenuItem("Абітурієнти", "user-plus", routes.APPLICANTS),
    ]),
    MenuItem("Адміністрування", "shield-user", children=[
        MenuItem("Користувачі", "users", routes.WORKERS_LIST, required_action=Actions.WORKER_LIST),
        MenuItem("Ролі", "key-round", routes.ROLES_LIST, required_action=Actions.ROLE_LIST),
    ]),
]
