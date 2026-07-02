from datetime import datetime
from typing import Dict, Optional, Sequence, Tuple

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from Dekanat.dao.entrant import apply_entrant_filters
from Dekanat.models import (
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialityModel,
)
from Dekanat.utils.db import ua_collate


# Сортування списку заявок (DK-35) завжди композитне з ФІКСОВАНИМ порядком ключів:
# спершу ПІБ, потім пріоритет, потім спеціальність. Клік по заголовку лише перемикає
# напрямок відповідного стовпця (asc⇄desc), не змінюючи пріоритет ключів.
_CANONICAL_ORDER = ["pib", "priority", "speciality"]


def _application_loaders():
    """Eager-load усього, що потрібно для одного рядка-заявки: спеціальність та
    абітурієнт з особою і довідниками. Фото не рендериться у списку — воно
    підвантажиться разом з особою, але на фронт не потрапляє (сервіс віддає лише
    рядки-проекції)."""
    return [
        selectinload(SpecialtieEntrantModel.speciality),
        selectinload(SpecialtieEntrantModel.entrant).selectinload(EntrantModel.application_status),
        selectinload(SpecialtieEntrantModel.entrant).selectinload(EntrantModel.person).selectinload(PersonModel.entry_base),
        selectinload(SpecialtieEntrantModel.entrant).selectinload(EntrantModel.person).selectinload(PersonModel.source_of_funding),
    ]


def _sort_columns(field: str, direction: str) -> list:
    def _dir(col):
        return col.desc() if direction == "desc" else col.asc()

    if field == "pib":
        return [_dir(ua_collate(PersonModel.pib))]
    if field == "priority":
        return [_dir(SpecialtieEntrantModel.priority)]
    if field == "speciality":
        # Спеціальність — за кодом, далі за назвою (кирилиця через ua_collate).
        return [_dir(SpecialityModel.code), _dir(ua_collate(SpecialityModel.title))]
    return []


def _apply_sort(statement, sort_dirs: Optional[Dict[str, str]]):
    """Порядок ключів фіксований (ПІБ → пріоритет → спеціальність); напрямок кожного
    стовпця береться зі `sort_dirs` (дефолт — asc)."""
    dirs = sort_dirs or {}
    cols: list = []
    for field in _CANONICAL_ORDER:
        direction = (dirs.get(field) or "asc").lower()
        if direction not in ("asc", "desc"):
            direction = "asc"
        cols.extend(_sort_columns(field, direction))
    return statement.order_by(*cols)


class EntrantApplicationDao:
    """Читання «заявок» — по одному рядку на кожен пріоритет абітурієнта (запис у
    specialties_entrants). Фільтрація виконується на рівні абітурієнта тими самими
    предикатами, що і список абітурієнтів (apply_entrant_filters), тож обидва списки
    відбирають одні й ті ж картки; кожна відібрана картка розкладається на свої заявки.
    """

    @staticmethod
    def get_all(
        session: Session,
        with_del: bool = False,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        pib_substring: Optional[str] = None,
        phone_substring: Optional[str] = None,
        application_status_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        priority_speciality_id: Optional[int] = None,
        top_priority_speciality_id: Optional[int] = None,
        sort_dirs: Optional[Dict[str, str]] = None,
    ) -> Sequence[SpecialtieEntrantModel]:
        statement = (
            select(SpecialtieEntrantModel)
            .options(*_application_loaders())
            .join(EntrantModel, SpecialtieEntrantModel.id_entrant == EntrantModel.id)
            .join(PersonModel, EntrantModel.id == PersonModel.id)
            .join(SpecialityModel, SpecialtieEntrantModel.id_speciality == SpecialityModel.id)
        )
        if not with_del:
            statement = statement.where(EntrantModel.is_deleted == False)
        statement = apply_entrant_filters(
            statement,
            pib_substring=pib_substring,
            phone_substring=phone_substring,
            application_status_id=application_status_id,
            entry_base_id=entry_base_id,
            created_between=created_between,
            created_date_between=created_date_between,
            priority_speciality_id=priority_speciality_id,
            top_priority_speciality_id=top_priority_speciality_id,
        )
        statement = _apply_sort(statement, sort_dirs)
        return session.exec(statement).all()
