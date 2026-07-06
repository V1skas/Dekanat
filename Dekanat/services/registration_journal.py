from datetime import datetime
from typing import Dict, List, Optional, Tuple

from Dekanat.models import EntrantModel
from Dekanat.services.entrant import EntrantService


# Ключі рядка журналу = поля `RegistrationJournalRow` (і колонки таблиці на сторінці).
# Порожні "refusal"/"signature" — у системі цих даних немає (заповнюються від руки).


def _fmt_date(value: Optional[str]) -> str:
    """'2010-08-26' → '26.08.2010'. Порожнє/невідоме → як є (або '')."""
    if not value:
        return ""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return value


def _fmt_dt(value: Optional[datetime]) -> str:
    """datetime → '01.07.2026 13:41:08' (із секундами, як у прикладі МОН)."""
    if value is None:
        return ""
    try:
        return value.strftime("%d.%m.%Y %H:%M:%S")
    except (ValueError, AttributeError):
        return str(value)


def _map_sex(value: Optional[str]) -> str:
    """Повна форма статі → скорочення форми МОН."""
    mapping = {"Чоловіча": "Чол.", "Жіноча": "Жін."}
    return mapping.get(value or "", value or "")


class RegistrationJournalService:
    """Журнал реєстрації заяв (DK-30) — пряма проекція абітурієнтів у рядки журналу.
    Власного DAO не має: переиспользує `EntrantService.get_list_items` (він фільтрує за
    датою прийому і eager-load'ить документи про освіту, результати ЗНО та пріоритети).
    Один рядок = один абітурієнт; порядок — за датою прийому (created_at asc)."""

    def _build_rows(
        self,
        created_between: Optional[Tuple[datetime, datetime]],
        created_date_between: Optional[Tuple[datetime, datetime]],
    ) -> List[Dict[str, str]]:
        try:
            entrants = EntrantService().get_list_items(
                created_between=created_between,
                created_date_between=created_date_between,
                sort_field="created_at",
                sort_dir="asc",
            )
            return [self._row_from_entrant(e) for e in entrants]
        except Exception as e:
            print(f"[RegistrationJournalService][_build_rows][ERROR] {e}")
            raise

    @staticmethod
    def _row_from_entrant(e: EntrantModel) -> Dict[str, str]:
        person = e.person

        # 6. Документи про освіту: "номер, серія, дата, тип" (кілька — через '; ').
        education_parts: List[str] = []
        for d in (person.document_about_education or []) if person is not None else []:
            head = [p for p in (d.number, d.series, _fmt_date(d.date_of_issue)) if p]
            head.append(d.title or "")
            education_parts.append(", ".join(p for p in head if p))
        education = "; ".join(p for p in education_parts if p)

        # 7. Пріоритетність заяви — не заповнюється (лишається порожньою, DK-30 follow-up).
        priority = ""

        # 8. Подані результати ЗНО: "предмет — бал". Показуємо саме ті бали, що беруть
        # участь у рейтингу — `points` (уже домножений на коефіцієнт предмета), а не
        # сирий введений бал `points_raw` (DK-30 follow-up).
        zno_parts: List[str] = []
        for r in (person.results_zno or []) if person is not None else []:
            title = r.item_zno.title if r.item_zno is not None else ""
            score = r.points
            if title or score is not None:
                zno_parts.append(f"{title} — {score}".strip(" —"))
        zno = "; ".join(zno_parts)

        return {
            "edbo": (person.edbo or "") if person is not None else "",
            "accepted_at": _fmt_dt(e.created_at),
            "pib": (person.pib or "") if person is not None else "",
            "sex": _map_sex(person.sex if person is not None else ""),
            "birth_date": _fmt_date(person.date_of_birth if person is not None else ""),
            "education": education,
            "priority": priority,
            "zno": zno,
            "refusal": "",
            "signature": "",
        }

    def get_rows(
        self,
        created_between: Optional[Tuple[datetime, datetime]],
        created_date_between: Optional[Tuple[datetime, datetime]],
    ) -> List[Dict[str, str]]:
        """Рядки журналу для таблиці на сторінці."""
        return self._build_rows(created_between, created_date_between)

    def get_document_payload(
        self,
        created_between: Optional[Tuple[datetime, datetime]],
        created_date_between: Optional[Tuple[datetime, datetime]],
        period_label: str,
        file_stem: str,
    ) -> Dict:
        """Payload для `RegistrationJournalReport(**payload)`. Читає ті самі рядки,
        що й таблиця — сторінка й документ завжди узгоджені."""
        try:
            rows = self._build_rows(created_between, created_date_between)
            return {
                "period_label": period_label,
                "file_stem": file_stem,
                "rows": rows,
            }
        except Exception as e:
            print(f"[RegistrationJournalService][get_document_payload][ERROR] {e}")
            raise
