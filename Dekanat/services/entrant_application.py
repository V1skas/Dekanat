import reflex as rx

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from Dekanat.dao.entrant_application import EntrantApplicationDao


class EntrantApplicationRow(BaseModel):
    """Плоский рядок списку заявок (DK-35): одна заявка = абітурієнт + одна
    спеціальність з його пріоритетного списку. Усі поля вже підготовлені до показу
    (рядки), щоб не тягнути на фронт повні моделі з фото."""

    entrant_id: int
    pib: str
    created_at: str
    phone_number: str
    email: str
    entry_base: str
    source_of_funding: str
    priority: int
    speciality: str
    application_status: str


class EntrantApplicationService:
    def get_list_items(
        self,
        pib: Optional[str] = None,
        phone: Optional[str] = None,
        status_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        priority_speciality_id: Optional[int] = None,
        top_priority_speciality_id: Optional[int] = None,
        sort_dirs: Optional[Dict[str, str]] = None,
    ) -> List[EntrantApplicationRow]:
        """Повертає заявки абітурієнтів із серверною фільтрацією та сортуванням."""
        try:
            with rx.session() as session:
                rows = EntrantApplicationDao.get_all(
                    session,
                    pib_substring=pib,
                    phone_substring=phone,
                    application_status_id=status_id,
                    entry_base_id=entry_base_id,
                    created_between=created_between,
                    created_date_between=created_date_between,
                    priority_speciality_id=priority_speciality_id,
                    top_priority_speciality_id=top_priority_speciality_id,
                    sort_dirs=sort_dirs,
                )
                # Мапимо ORM-моделі у плоскі рядки всередині сесії (поки relationship'и
                # доступні), щоб на фронт пішли лише потрібні рядки, без фото та зайвих полів.
                return [self._to_row(sp) for sp in rows]
        except Exception as e:
            print(f"[EntrantApplicationService][get_list_items][ERROR] {e}")
            raise

    @staticmethod
    def _to_row(sp) -> EntrantApplicationRow:
        entrant = sp.entrant
        person = entrant.person if entrant is not None else None
        speciality = sp.speciality

        created_str = ""
        if entrant is not None and entrant.created_at is not None:
            try:
                created_str = entrant.created_at.strftime("%Y-%m-%d")
            except AttributeError:
                created_str = str(entrant.created_at)[:10]

        entry_base = ""
        source_of_funding = ""
        pib = ""
        phone_number = ""
        email = ""
        if person is not None:
            pib = person.pib or ""
            phone_number = person.phone_number or ""
            email = person.email or ""
            if person.entry_base is not None:
                entry_base = person.entry_base.title or ""
            if person.source_of_funding is not None:
                source_of_funding = person.source_of_funding.title or ""

        application_status = ""
        if entrant is not None and entrant.application_status is not None:
            application_status = entrant.application_status.title or ""

        speciality_label = ""
        if speciality is not None:
            speciality_label = f"{speciality.code} {speciality.title} ({speciality.tag})"

        return EntrantApplicationRow(
            entrant_id=sp.id_entrant,
            pib=pib,
            created_at=created_str,
            phone_number=phone_number,
            email=email,
            entry_base=entry_base,
            source_of_funding=source_of_funding,
            priority=sp.priority,
            speciality=speciality_label,
            application_status=application_status,
        )
