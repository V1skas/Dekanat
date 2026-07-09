"""Дії журналу для користувачів системи (workers, DK-55).

Поля пароля/солі навмисно не логуються. Набір ролей — окреме поле `roles`, яке
сервіс виставляє вручну (з `from_diff` для скалярних полів воно не рахується).
"""

from typing import ClassVar, Dict, Optional, Tuple

from Dekanat.audit.base import CreateAction, UpdateAction, DeleteAction, FieldChange


_WORKER_LABELS: Dict[str, str] = {
    "pib": "ПІБ",
    "login": "Логін",
    "email": "Email",
    "phone_number": "Телефон",
    "roles": "Ролі",
}


class WorkerCreated(CreateAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    pib: str
    login: str
    email: Optional[str] = None
    phone_number: Optional[str] = None


class WorkerUpdated(UpdateAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    TRACKED: ClassVar[Tuple[str, ...]] = ("pib", "login", "email", "phone_number")
    pib: Optional[FieldChange] = None
    login: Optional[FieldChange] = None
    email: Optional[FieldChange] = None
    phone_number: Optional[FieldChange] = None
    # Набір ролей — виставляється сервісом вручну (список назв ролей до/після).
    roles: Optional[FieldChange] = None


class WorkerDeleted(DeleteAction):
    table_name: ClassVar[str] = "workers"
    FIELD_LABELS: ClassVar[Dict[str, str]] = _WORKER_LABELS
    pib: str
    login: str
