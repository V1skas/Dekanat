import reflex as rx
import base64

from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from Dekanat.dao.entrant import EntrantDao
from Dekanat.dao.source_of_funding import SourceOfFundingDao
from Dekanat.dao.entry_base import EntryBaseDao
from Dekanat.dao.application_status import ApplicationStatusDao
from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.dao.speciality import SpecialityDao
from Dekanat.dao.form_of_study import FormOfStudyDao
from Dekanat.dao.item_zno import ItemZnoDao
from Dekanat.dao.identity_document_type import IdentityDocumentTypeDao
from Dekanat.dao.kinship import KinshipDao
from Dekanat.dao.special_condition import SpecialConditionDao
from Dekanat.utils.clock import now_local
from Dekanat.utils.display import format_grade
from Dekanat.models import (
    EntrantModel,
    EntrantGroupModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialtieEntrantSourceOfFundingModel,
    IdentityDocumentModel,
    DocumentAboutEducationModel,
    MilitaryAccountingModel,
    MedicalReferenceModel,
    InformationAboutRelativesModel,
    SpecialConditionPersonModel,
    ResultZnoModel,
)
from Dekanat.audit import (
    record_action,
    diff_collection,
    CollectionChange,
    EntrantCreated,
    EntrantUpdated,
    EntrantDeleted,
    GroupCreated,
    GroupMembersChanged,
)


def _label_maps(session) -> Dict[str, Dict]:
    """Мапи id/код → назва для резолву FK-полів і дочірніх колекцій у журналі
    (DK-66) — замість сирих id показуємо назви. `with_del=True`: не втратити
    назву посилання на вже видалений довідниковий запис (стара історія має
    лишатись читомою)."""
    return {
        "source_of_funding": {r.id: r.title for r in SourceOfFundingDao.get_all(session, with_del=True)},
        "entry_base": {r.id: r.title for r in EntryBaseDao.get_all(session, with_del=True)},
        "application_status": {r.id: r.title for r in ApplicationStatusDao.get_all(session, with_del=True)},
        "entrant_group": {r.id: r.title for r in EntrantsGroupDao.get_all(session, with_del=True)},
        "speciality": {r.id: f"{r.code} {r.title}" for r in SpecialityDao.get_all(session, with_del=True)},
        "form_of_study": {r.id: r.title for r in FormOfStudyDao.get_all(session, with_del=True)},
        "item_zno": {r.id: r.title for r in ItemZnoDao.get_all(session, with_del=True)},
        "identity_document_type": {r.id: r.title for r in IdentityDocumentTypeDao.get_all(session, with_del=True)},
        "kinship": {r.id: r.title for r in KinshipDao.get_all(session, with_del=True)},
        "special_condition": {r.subcategory_code: r.title for r in SpecialConditionDao.get_all(session, with_del=True)},
    }


def _name(mapping: Dict, key: Any) -> Optional[str]:
    """Назва довідникового запису за id/кодом. `None`-ключ → `None`; невідомий
    (видалений і не знайдений) — `#ключ`, щоб не показувати порожнечу мовчки."""
    if key is None:
        return None
    return mapping.get(key, f"#{key}")


def _entrant_snapshot(person: PersonModel, entrant: EntrantModel, maps: Dict) -> SimpleNamespace:
    """Зведений знімок скалярних полів особи + абітурієнта для diff журналу.
    FK-поля вже резолвлені у назви (DK-66) — `FieldChange` показує назву, а не id."""
    return SimpleNamespace(
        pib=person.pib, edbo=person.edbo, citizenship=person.citizenship, sex=person.sex,
        date_of_birth=person.date_of_birth,
        place_of_registration_city=person.place_of_registration_city,
        place_of_registration=person.place_of_registration, mokpp=person.mokpp,
        email=person.email, phone_number=person.phone_number,
        the_need_for_a_dormitory=person.the_need_for_a_dormitory,
        id_source_of_funding=_name(maps["source_of_funding"], person.id_source_of_funding),
        id_entry_base=_name(maps["entry_base"], person.id_entry_base),
        id_application_status=_name(maps["application_status"], entrant.id_application_status),
        comment=entrant.comment,
        submitted_electronically=entrant.submitted_electronically,
        id_entrant_group=_name(maps["entrant_group"], entrant.id_entrant_group),
    )


# --- Дочірні колекції: поштучний diff (added/removed/edited, DK-66) ---------
#
# Для кожної колекції: людський підпис, поля рядка (для читання з ORM/вхідних
# моделей), поля ідентичності (без значення, що диффиться — інакше ідентичність
# рядка "плаває" разом зі зміною) та функції identity()/value() з резолвом назв.
# `value_fn is None` — немає стабільного «значення» для порівняння (не FK-based
# природний ключ), diff зводиться до add+remove при будь-якій зміні рядка.

def _specialty_identity(row: Dict, maps: Dict) -> str:
    spec = _name(maps["speciality"], row["id_speciality"]) or f"#{row['id_speciality']}"
    form = _name(maps["form_of_study"], row["id_form_of_study"]) or f"#{row['id_form_of_study']}"
    return f"{spec} ({form})"


def _specialty_value(row: Dict, maps: Dict) -> str:
    return f"пріоритет {row['priority']}"


def _result_zno_identity(row: Dict, maps: Dict) -> str:
    return _name(maps["item_zno"], row["id_items_zno"]) or f"#{row['id_items_zno']}"


def _result_zno_value(row: Dict, maps: Dict) -> str:
    return format_grade(row["points"])


def _identity_document_identity(row: Dict, maps: Dict) -> str:
    doc_type = _name(maps["identity_document_type"], row["id_type"]) or f"#{row['id_type']}"
    return f"{doc_type} № {row['number']}"


def _identity_document_value(row: Dict, maps: Dict) -> str:
    return row.get("series") or ""


def _education_document_identity(row: Dict, maps: Dict) -> str:
    number = row.get("number")
    return f"{row['title']} № {number}" if number else (row.get("title") or "")


def _military_accounting_identity(row: Dict, maps: Dict) -> str:
    return f"№ {row['number']} {row['series']}".strip()


def _military_accounting_value(row: Dict, maps: Dict) -> str:
    return row.get("date_of_issue") or ""


def _medical_reference_identity(row: Dict, maps: Dict) -> str:
    return row.get("number") or ""


def _medical_reference_value(row: Dict, maps: Dict) -> str:
    return row.get("date_of_issue") or ""


def _relative_identity(row: Dict, maps: Dict) -> str:
    kin = _name(maps["kinship"], row["id_kinship"]) or f"#{row['id_kinship']}"
    return f"{kin}: {row['pib']}"


def _relative_value(row: Dict, maps: Dict) -> str:
    return row.get("phone_number") or ""


def _special_condition_identity(row: Dict, maps: Dict) -> str:
    title = _name(maps["special_condition"], row["id_special_condition"]) or f"#{row['id_special_condition']}"
    number = row.get("number")
    return f"{title} № {number}" if number else title


def _special_condition_value(row: Dict, maps: Dict) -> str:
    return row.get("date_of_issue") or ""


# (label, item_fields, id_key_fields, identity_fn, value_fn)
_ENTRANT_COLLECTIONS = [
    ("Спеціальності", ("id_speciality", "id_form_of_study", "priority"),
     ("id_speciality", "id_form_of_study"), _specialty_identity, _specialty_value),
    ("Результати ЗНО", ("id_items_zno", "points_raw", "points"),
     ("id_items_zno",), _result_zno_identity, _result_zno_value),
    ("Документи, що посвідчують особу", ("number", "series", "id_type"),
     ("number", "id_type"), _identity_document_identity, _identity_document_value),
    ("Документи про освіту", ("title", "number", "series", "date_of_issue"),
     ("title", "number", "series", "date_of_issue"), _education_document_identity, None),
    ("Військовий облік", ("number", "series", "date_of_issue"),
     ("number", "series"), _military_accounting_identity, _military_accounting_value),
    ("Медичні довідки", ("number", "date_of_issue"),
     ("number",), _medical_reference_identity, _medical_reference_value),
    ("Відомості про родичів", ("id_kinship", "pib", "phone_number"),
     ("id_kinship", "pib"), _relative_identity, _relative_value),
    ("Спеціальні умови", ("id_special_condition", "number", "date_of_issue"),
     ("id_special_condition", "number"), _special_condition_identity, _special_condition_value),
]


def _prepare_rows(items, fields: Tuple[str, ...], id_fields: Tuple[str, ...], maps: Dict,
                   identity_fn, value_fn) -> List[Dict]:
    """Читає скалярні поля рядків колекції (ORM/вхідні моделі) і резолвить їх у
    `{"id_key", "identity", "value"}` для `diff_collection` (DK-66)."""
    prepared: List[Dict] = []
    for item in (items or []):
        row = {f: getattr(item, f, None) for f in fields}
        prepared.append({
            "id_key": tuple(row[f] for f in id_fields),
            "identity": identity_fn(row, maps),
            "value": value_fn(row, maps) if value_fn is not None else None,
        })
    return prepared


def _build_collection_changes(old_rows_list: List[List[Dict]], new_items_list, new_maps: Dict) -> List[CollectionChange]:
    """Diff усіх дочірніх колекцій картки (DK-66). `old_rows_list` — уже
    підготовлені (у read-сесії, з тодішніми назвами) рядки; `new_items_list` —
    сирі вхідні моделі, резолвляться тут через `new_maps` (пишуча сесія).
    Повертає лише колекції, що реально змінились (`has_changes()`), у порядку
    `_ENTRANT_COLLECTIONS`."""
    changes: List[CollectionChange] = []
    for (label, fields, id_fields, identity_fn, value_fn), old_rows, new_items in zip(
        _ENTRANT_COLLECTIONS, old_rows_list, new_items_list
    ):
        new_rows = _prepare_rows(new_items, fields, id_fields, new_maps, identity_fn, value_fn)
        change = diff_collection(label, old_rows, new_rows)
        if change.has_changes():
            changes.append(change)
    return changes


def photo_to_data_url(photo_bytes: Optional[bytes], mime: Optional[str]) -> str:
    """Convert stored photo bytes + mime into an inline data URL for rx.image src."""
    if not photo_bytes:
        return ""
    effective_mime = mime if mime else "image/png"
    encoded = base64.b64encode(photo_bytes).decode("ascii")
    return f"data:{effective_mime};base64,{encoded}"


class EntrantService:
    def get_list_items(
        self,
        pib: Optional[str] = None,
        phone: Optional[str] = None,
        mokpp: Optional[str] = None,
        status_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
        priority_speciality_id: Optional[int] = None,
        top_priority_speciality_id: Optional[int] = None,
        special_condition_code: Optional[str] = None,
        submitted_electronically: Optional[bool] = None,
        sort_field: Optional[str] = None,
        sort_dir: str = "asc",
    ) -> Sequence[EntrantModel]:
        """Повертає абітурієнтів із серверною фільтрацією та сортуванням."""
        try:
            with rx.session() as session:
                return EntrantDao.get_all(
                    session,
                    pib_substring=pib,
                    phone_substring=phone,
                    mokpp_substring=mokpp,
                    application_status_id=status_id,
                    entry_base_id=entry_base_id,
                    created_between=created_between,
                    created_date_between=created_date_between,
                    priority_speciality_id=priority_speciality_id,
                    top_priority_speciality_id=top_priority_speciality_id,
                    special_condition_code=special_condition_code,
                    submitted_electronically=submitted_electronically,
                    sort_field=sort_field,
                    sort_dir=sort_dir,
                )
        except Exception as e:
            print(f"[EntrantService][get_list_items][ERROR] {e}")
            raise

    def get_priority_items(
        self,
        top_priority_speciality_id: Optional[int] = None,
        entry_base_id: Optional[int] = None,
        created_between: Optional[Tuple[datetime, datetime]] = None,
        created_date_between: Optional[Tuple[datetime, datetime]] = None,
    ) -> Sequence[EntrantModel]:
        """Полегшена вибірка для представлення «Пріоритетні спеціальності» (DK-49):
        абітурієнти з підвантаженими лише ПІБ та пріоритетним списком спеціальностей.
        Фільтри — пріоритетна спеціальність (№1) та база вступу (DK-51)."""
        try:
            with rx.session() as session:
                return EntrantDao.get_priority_view(
                    session,
                    top_priority_speciality_id=top_priority_speciality_id,
                    entry_base_id=entry_base_id,
                    created_between=created_between,
                    created_date_between=created_date_between,
                )
        except Exception as e:
            print(f"[EntrantService][get_priority_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantService][get_by_id][ERROR] {e}")
            raise

    def find_duplicates(
        self,
        pib: Optional[str] = None,
        phone: Optional[str] = None,
        mokpp: Optional[str] = None,
        edbo: Optional[str] = None,
        exclude_id: Optional[int] = None,
    ) -> Sequence[EntrantModel]:
        """Попередній пошук можливих дублікатів картки за ПІБ/телефоном/ІПН/ЄДБО
        перед збереженням (DK-60). Не блокує збереження — лише інформує."""
        try:
            with rx.session() as session:
                return EntrantDao.find_duplicates(
                    session, pib=pib, phone=phone, mokpp=mokpp, edbo=edbo, exclude_id=exclude_id,
                )
        except Exception as e:
            print(f"[EntrantService][find_duplicates][ERROR] {e}")
            raise

    @staticmethod
    def _validate_mokpp(person: PersonModel) -> None:
        """ІПН — необов'язковий (DK-38), але якщо вказаний, має бути рівно 10 цифр.
        Дублюємо клієнтську перевірку на сервері, бо клієнт може надіслати будь-що."""
        mokpp = (person.mokpp or "").strip()
        if mokpp and not (mokpp.isdigit() and len(mokpp) == 10):
            raise ValueError("ІПН має містити рівно 10 цифр")

    def _validate_specialties(
        self, person: PersonModel, specialties: list[SpecialtieEntrantModel]
    ) -> None:
        """Перевіряє, що кожна обрана абітурієнтом спеціальність доступна для його бази
        вступу та обраної форми навчання в активній кампанії (DK-26). Викликається до
        відкриття пишучої сесії, щоб не плодити вкладені сесії на hot path."""
        if not specialties:
            return
        from Dekanat.services.admission_campaign import AdmissionCampaignService
        from Dekanat.services.admission_campaign_speciality import (
            AdmissionCampaignSpecialityService,
        )

        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None or campaign.id is None:
            return  # немає активної кампанії — немає з чим звіряти
        quotas = AdmissionCampaignSpecialityService().get_by_campaign(campaign.id)
        valid = {
            (q.id_speciality, q.id_entry_base, q.id_form_of_study)
            for q in quotas
        }
        base = person.id_entry_base
        for sp in specialties:
            key = (sp.id_speciality, base, sp.id_form_of_study)
            if key not in valid:
                raise ValueError(
                    "Обрана спеціальність недоступна для цієї бази вступу та форми "
                    "навчання в активній кампанії."
                )

    @staticmethod
    def _apply_new_group(entrant: EntrantModel, new_group_title: Optional[str], session) -> None:
        """Створює нову екзаменаційну групу з переданою назвою у поточній транзакції
        і привʼязує до неї абітурієнта (DK-48). Викликається лише коли автопідбір у
        картці запропонував НОВУ групу; наявну групу картка передає через
        `entrant.id_entrant_group`, тож тут нічого не робимо."""
        title = (new_group_title or "").strip()
        if not title:
            return
        group = EntrantGroupModel(title=title)
        session.add(group)
        session.flush()
        entrant.id_entrant_group = group.id

    @staticmethod
    def _log_group_assignment(
        session,
        actor_id: Optional[int],
        new_group_id: Optional[int],
        old_group_id: Optional[int],
        pib: str,
        new_group_title: Optional[str],
    ) -> None:
        """Окремий запис журналу про призначення абітурієнту екзам. групи з картки
        (DK-55). Якщо група щойно створена автопідбором — спершу GroupCreated."""
        if new_group_id is None or new_group_id == old_group_id:
            return
        title = (new_group_title or "").strip()
        if title:
            record_action(session, actor_id, new_group_id, GroupCreated(title=title))
        record_action(session, actor_id, new_group_id, GroupMembersChanged(added=[pib]))

    @staticmethod
    def _collection_items(old_full) -> list:
        """Дочірні колекції завантаженого абітурієнта (ORM-списки) у порядку
        `_ENTRANT_COLLECTIONS` (DK-66)."""
        if old_full is None:
            return [[] for _ in _ENTRANT_COLLECTIONS]
        person = old_full.person
        return [
            old_full.specialties,
            person.results_zno if person else [],
            person.identity_document if person else [],
            person.document_about_education if person else [],
            person.military_accounting if person else [],
            person.medical_reference if person else [],
            person.information_about_relatives if person else [],
            person.special_conditions if person else [],
        ]

    def _read_old_snapshot(self, person_id: int):
        """Знімок старого стану картки в ОКРЕМІЙ read-only сесії (DK-55/DK-66).

        Повертає `(old_snap, old_group_id, old_collection_rows)`: `old_snap` —
        `SimpleNamespace` скалярів (FK-поля вже резолвлені у назви), а рядки
        дочірніх колекцій підготовлені (`id_key`/`identity`/`value`, теж із
        резолвленими назвами — довідники читаються тут же, в read-сесії) для
        diff'а в `_build_collection_changes`. Жоден ORM-обʼєкт (напр. `item_zno`)
        не потрапляє у пишучу сесію `edit_one` — інакше буде identity-map
        конфлікт із `item_zno`, які несуть вхідні результати ЗНО. Сесія повністю
        закривається до відкриття пишучої, тож блокування SQLite не виникає
        (сесії не одночасні)."""
        with rx.session() as session:
            old_full = EntrantDao.get_by_id(person_id, session)
            if old_full is None:
                return None, None, [[] for _ in _ENTRANT_COLLECTIONS]
            old_maps = _label_maps(session)
            old_group_id = old_full.id_entrant_group
            old_snap = (
                _entrant_snapshot(old_full.person, old_full, old_maps)
                if old_full.person is not None else None
            )
            old_items_list = self._collection_items(old_full)
            old_rows = [
                _prepare_rows(items, fields, id_fields, old_maps, identity_fn, value_fn)
                for (label, fields, id_fields, identity_fn, value_fn), items in zip(
                    _ENTRANT_COLLECTIONS, old_items_list
                )
            ]
            return old_snap, old_group_id, old_rows

    def add_one(
        self,
        person: PersonModel,
        entrant: EntrantModel,
        identity_documents: list[IdentityDocumentModel],
        documents_about_education: list[DocumentAboutEducationModel],
        military_accountings: list[MilitaryAccountingModel],
        medical_references: list[MedicalReferenceModel],
        information_about_relatives: list[InformationAboutRelativesModel],
        special_conditions: list[SpecialConditionPersonModel],
        specialties: list[SpecialtieEntrantModel],
        results_zno: list[ResultZnoModel],
        specialty_sources: Optional[list[SpecialtieEntrantSourceOfFundingModel]] = None,
        new_group_title: Optional[str] = None,
        actor_id: Optional[int] = None,
    ) -> EntrantModel:
        try:
            self._validate_mokpp(person)
            self._validate_specialties(person, specialties)
            with rx.session() as session:
                # Перевірка дублікатів по ІПН (mokpp): двох абітурієнтів з одним ІПН бути
                # не може. По ПІБ не перевіряємо — можливі повні тезки (DK-36).
                if person.mokpp and EntrantDao.get_person_by_mokpp(person.mokpp, session) is not None:
                    raise ValueError(f"Абітурієнт з ІПН {person.mokpp} вже існує.")
                person.id = None  # type: ignore[assignment]
                saved_person = EntrantDao.add_person(person, session)
                person_id = saved_person.id

                # Автопідбір групи (DK-48): нова група створюється лише зараз, при
                # збереженні картки, і одразу привʼязується до абітурієнта.
                self._apply_new_group(entrant, new_group_title, session)

                entrant.id = person_id  # type: ignore[assignment]
                saved_entrant = EntrantDao.add_entrant(entrant, session)

                EntrantDao.replace_identity_documents(person_id, identity_documents, session)
                EntrantDao.replace_documents_about_education(person_id, documents_about_education, session)
                EntrantDao.replace_military_accountings(person_id, military_accountings, session)
                EntrantDao.replace_medical_references(person_id, medical_references, session)
                EntrantDao.replace_information_about_relatives(person_id, information_about_relatives, session)
                EntrantDao.replace_special_conditions(person_id, special_conditions, session)
                EntrantDao.replace_results_zno(person_id, results_zno, session)
                EntrantDao.replace_specialties(person_id, specialties, session)
                # Прийнятні ресурси фінансування по кожному пріоритету (DK-59): нова
                # картка — старих рядків немає, тож достатньо вставити.
                EntrantDao.insert_specialty_sources(person_id, specialty_sources or [], session)

                maps = _label_maps(session)
                record_action(session, actor_id, person_id, EntrantCreated(
                    pib=person.pib, edbo=person.edbo,
                    id_application_status=_name(maps["application_status"], entrant.id_application_status) or "",
                ))
                self._log_group_assignment(
                    session, actor_id, entrant.id_entrant_group, None, person.pib, new_group_title,
                )

                session.commit()
                session.refresh(saved_entrant)
                return saved_entrant
        except Exception as e:
            print(f"[EntrantService][add_one][ERROR] {e}")
            raise

    def edit_one(
        self,
        person: PersonModel,
        entrant: EntrantModel,
        identity_documents: list[IdentityDocumentModel],
        documents_about_education: list[DocumentAboutEducationModel],
        military_accountings: list[MilitaryAccountingModel],
        medical_references: list[MedicalReferenceModel],
        information_about_relatives: list[InformationAboutRelativesModel],
        special_conditions: list[SpecialConditionPersonModel],
        specialties: list[SpecialtieEntrantModel],
        results_zno: list[ResultZnoModel],
        specialty_sources: Optional[list[SpecialtieEntrantSourceOfFundingModel]] = None,
        new_group_title: Optional[str] = None,
        actor_id: Optional[int] = None,
    ) -> EntrantModel:
        try:
            self._validate_mokpp(person)
            self._validate_specialties(person, specialties)

            # Знімок старого стану — в ОКРЕМІЙ read-only сесії (примітиви, назви
            # вже резолвлені), щоб ORM-обʼєкти (item_zno тощо) не потрапили у
            # пишучу сесію (DK-55/DK-66).
            old_snap, old_group_id, old_collection_rows = self._read_old_snapshot(person.id)

            with rx.session() as session:
                # Дублікат по ІПН (виключаючи саму картку, що редагується) — DK-36.
                if person.mokpp and EntrantDao.get_person_by_mokpp(person.mokpp, session, exclude_id=person.id) is not None:
                    raise ValueError(f"Абітурієнт з ІПН {person.mokpp} вже існує.")

                # Автопідбір групи (DK-48): нову групу створюємо лише зараз.
                self._apply_new_group(entrant, new_group_title, session)
                # Preserve timestamps from existing rows and bump status_changed_at only if status really changed.
                existing_person = session.get(PersonModel, person.id)
                if existing_person is not None:
                    person.created_at = existing_person.created_at
                existing_entrant = session.get(EntrantModel, entrant.id)
                if existing_entrant is not None:
                    entrant.created_at = existing_entrant.created_at
                    if existing_entrant.id_application_status != entrant.id_application_status:
                        entrant.application_status_changed_at = now_local()
                    else:
                        entrant.application_status_changed_at = existing_entrant.application_status_changed_at

                EntrantDao.edit_person(person, session)
                merged_entrant = EntrantDao.edit_entrant(entrant, session)
                session.flush()

                person_id = person.id

                EntrantDao.replace_identity_documents(person_id, identity_documents, session)
                EntrantDao.replace_documents_about_education(person_id, documents_about_education, session)
                EntrantDao.replace_military_accountings(person_id, military_accountings, session)
                EntrantDao.replace_medical_references(person_id, medical_references, session)
                EntrantDao.replace_information_about_relatives(person_id, information_about_relatives, session)
                EntrantDao.replace_special_conditions(person_id, special_conditions, session)
                EntrantDao.replace_results_zno(person_id, results_zno, session)
                # Старі позначки прийнятних ресурсів видаляємо ДО заміни спеціальностей
                # (FK-constraint на specialties_entrants — DK-59), нові вставляємо ПІСЛЯ.
                EntrantDao.delete_specialty_sources(entrant.id, session)
                EntrantDao.replace_specialties(entrant.id, specialties, session)
                EntrantDao.insert_specialty_sources(entrant.id, specialty_sources or [], session)

                # Журнал: один запис на збереження. Деталізацію (diff скалярів +
                # поштучний diff дочірніх колекцій) пишемо у `changes`; логуємо
                # лише якщо щось реально змінилось (DK-55/DK-66).
                if old_snap is not None:
                    new_maps = _label_maps(session)
                    new_collections = [specialties, results_zno, identity_documents,
                                       documents_about_education, military_accountings,
                                       medical_references, information_about_relatives, special_conditions]
                    action = EntrantUpdated.from_diff(old_snap, _entrant_snapshot(person, entrant, new_maps))
                    action.collection_changes = _build_collection_changes(
                        old_collection_rows, new_collections, new_maps,
                    ) or None
                    record_action(session, actor_id, person_id, action)
                self._log_group_assignment(
                    session, actor_id, entrant.id_entrant_group, old_group_id, person.pib, new_group_title,
                )

                session.commit()
                session.refresh(merged_entrant)
                return merged_entrant
        except Exception as e:
            print(f"[EntrantService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, entrant: EntrantModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                entrant.is_deleted = True
                EntrantDao.edit_entrant(entrant, session)
                pib = entrant.person.pib if entrant.person is not None else ""
                edbo = entrant.person.edbo if entrant.person is not None else None
                if entrant.person is not None:
                    entrant.person.is_deleted = True
                    EntrantDao.edit_person(entrant.person, session)
                record_action(session, actor_id, entrant.id, EntrantDeleted(pib=pib, edbo=edbo))
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantService][delete_one][ERROR] {e}")
            return False
