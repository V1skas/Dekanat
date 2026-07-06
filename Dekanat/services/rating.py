import reflex as rx

from typing import Optional, Dict, List, Tuple
from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.dao.rating import RatingDao
from Dekanat.services.app_setting import AppSettingService
from Dekanat.utils.display import disambiguate_pib
from Dekanat.models import (
    RatingSnapshotModel,
    RatingEntryModel,
    AdmissionCampaignModel,
    AdmissionCampaignSpecialityModel,
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    ResultZnoModel,
    SpecialConditionPersonModel,
    SpecialConditionModel,
    ApplicationStatusModel,
    ItemZnoModel,
)


# Status constants for entries
STATUS_BUDGET = "budget"
STATUS_CONTRACT = "contract"
STATUS_KVOTA = "kvota"
STATUS_REJECTED = "rejected"
# DK-43: картка, чий статус заявки не допускає до рейтингу — рядок унизу, сірий.
STATUS_EXCLUDED = "excluded"


class RatingService:
    def get_latest_for_campaign(
        self, id_campaign: int
    ) -> Tuple[Optional[RatingSnapshotModel], List[RatingEntryModel]]:
        try:
            with rx.session() as session:
                snapshot = RatingDao.get_latest_for_campaign(id_campaign, session)
                if snapshot is None:
                    return None, []
                entries = list(RatingDao.get_entries(snapshot.id, session))
                return snapshot, entries
        except Exception as e:
            print(f"[RatingService][get_latest_for_campaign][ERROR] {e}")
            raise

    def generate(self, id_campaign: int) -> Tuple[RatingSnapshotModel, List[RatingEntryModel]]:
        """Розраховує рейтинг для всіх спеціальностей кампанії, зберігає та повертає його.

        Обчислення (важка read-only частина) і збереження розділені: `compute_entries`
        рахує рядки без запису (state виносить його у фоновий потік, DK-44),
        `persist_entries` пише знімок. Виносити у потік ще й запис не можна — на
        SQLite конкурентний INSERT із hot-path авторизації дає `database is locked`."""
        entries = self.compute_entries(id_campaign)
        return self.persist_entries(id_campaign, entries)

    def compute_entries(self, id_campaign: int) -> List[RatingEntryModel]:
        """Читає дані й рахує рейтингові рядки БЕЗ запису в БД. Повертає ще не
        привʼязані до сесії `RatingEntryModel` (id_snapshot не заданий). Повністю
        read-only — безпечно викликати у фоновому потоці через `run_blocking` (DK-44)."""
        try:
            # Верхня межа суми балів (DK-40) — читаємо до відкриття основної сесії,
            # щоб не тримати дві сесії SQLite одночасно.
            max_total = AppSettingService().get_max_total_points()
            with rx.session() as session:
                campaign = session.get(AdmissionCampaignModel, id_campaign)
                if campaign is None:
                    raise ValueError(f"Кампанію #{id_campaign} не знайдено")

                quotas = session.exec(
                    select(AdmissionCampaignSpecialityModel)
                    .options(selectinload(AdmissionCampaignSpecialityModel.speciality))
                    .where(AdmissionCampaignSpecialityModel.id_admission_campaign == id_campaign)
                ).all()

                # Усі абітурієнти, створені у межах активної кампанії
                from datetime import datetime
                try:
                    start_dt = datetime.strptime(campaign.start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(campaign.end_date, "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59
                    )
                except (ValueError, TypeError):
                    start_dt = None
                    end_dt = None

                entrants_stmt = (
                    select(EntrantModel)
                    .options(
                        selectinload(EntrantModel.person).selectinload(PersonModel.results_zno),
                        selectinload(EntrantModel.person).selectinload(PersonModel.special_conditions),
                        selectinload(EntrantModel.specialties),
                    )
                    .where(EntrantModel.is_deleted == False)
                )
                if start_dt is not None and end_dt is not None:
                    entrants_stmt = entrants_stmt.where(
                        EntrantModel.created_at >= start_dt
                    ).where(EntrantModel.created_at <= end_dt)
                entrants = list(session.exec(entrants_stmt).all())

                # Предмети ЗНО, що враховуються у рейтингу (DK-47). Лише їхні оцінки
                # входять до суми балів; решта (напр. компоненти НМТ) — ігноруються.
                rated_item_ids = {
                    i.id
                    for i in session.exec(
                        select(ItemZnoModel)
                        .where(ItemZnoModel.is_counted_in_rating == True)
                        .where(ItemZnoModel.is_deleted == False)
                    ).all()
                }

                # Які спец. умови вважаються квотою
                kvota_codes = {
                    sc.subcategory_code
                    for sc in session.exec(
                        select(SpecialConditionModel).where(SpecialConditionModel.is_kvota == True)
                    ).all()
                }

                # Статуси заявки, що допускають абітурієнта до рейтингу (DK-43).
                # Картки з рештою статусів у рейтингу не беруть участі — див. нижче.
                allowed_status_ids = {
                    s.id
                    for s in session.exec(
                        select(ApplicationStatusModel).where(
                            ApplicationStatusModel.is_allowed_in_rating == True
                        )
                    ).all()
                }

                # Підготовка даних по кожному абітурієнту. Квота визначається кортежем
                # (спеціальність, база вступу, форма навчання): база береться з особи,
                # форма — з конкретного запису пріоритету (DK-26).
                entrant_info: Dict[int, Dict] = {}
                for ent in entrants:
                    if ent.person is None:
                        continue
                    total = sum(
                        (r.points or 0)
                        for r in (ent.person.results_zno or [])
                        if r.id_items_zno in rated_item_ids
                    )
                    total = min(total, max_total)
                    has_kvota = any(
                        sc.id_special_condition in kvota_codes
                        for sc in (ent.person.special_conditions or [])
                    )
                    spec_keys = [
                        (s.id_speciality, s.id_form_of_study)
                        for s in (ent.specialties or [])
                    ]
                    entrant_info[ent.id] = {
                        "id": ent.id,
                        "total": total,
                        "kvota": has_kvota,
                        "allowed": ent.id_application_status in allowed_status_ids,
                        "base": ent.person.id_entry_base,
                        "specs": spec_keys,
                    }

                # Будуємо рейтинг для кожної квоти кампанії (спеціальність+база+форма)
                entries: List[RatingEntryModel] = []
                for q in quotas:
                    applicants = [
                        info
                        for info in entrant_info.values()
                        if info["base"] == q.id_entry_base
                        and (q.id_speciality, q.id_form_of_study)
                        in info["specs"]
                    ]
                    # Не допущені за статусом заявки (DK-43) — не ранжуються нарівні
                    # з рештою, а йдуть у самий низ зі статусом STATUS_EXCLUDED.
                    allowed = [a for a in applicants if a["allowed"]]
                    excluded = sorted(
                        [a for a in applicants if not a["allowed"]],
                        key=lambda a: a["total"],
                        reverse=True,
                    )
                    # Кандидати з квотою — нагору; в межах груп сортування за балом desc
                    kvotas = sorted(
                        [a for a in allowed if a["kvota"]],
                        key=lambda a: a["total"],
                        reverse=True,
                    )
                    others = sorted(
                        [a for a in allowed if not a["kvota"]],
                        key=lambda a: a["total"],
                        reverse=True,
                    )
                    ordered = kvotas + others + excluded

                    for pos, info in enumerate(ordered, start=1):
                        if not info["allowed"]:
                            status = STATUS_EXCLUDED
                        elif info["kvota"]:
                            status = STATUS_KVOTA
                        else:
                            status = ""
                        entries.append(
                            RatingEntryModel(
                                id_snapshot=0,  # set later
                                id_speciality=q.id_speciality,
                                id_entry_base=q.id_entry_base,
                                id_form_of_study=q.id_form_of_study,
                                id_entrant=info["id"],
                                position=pos,
                                total_points=info["total"],
                                status=status,
                            )
                        )

                # Виставляємо статуси не-квота-абітурієнтам за лічильниками місць.
                # Групуємо вже сформовані entries за кортежем квоти (спеціальність+база+форма).
                by_spec: Dict[Tuple[int, int, int], List[RatingEntryModel]] = {}
                for e in entries:
                    by_spec.setdefault(
                        (e.id_speciality, e.id_entry_base, e.id_form_of_study),
                        [],
                    ).append(e)
                for q in quotas:
                    key = (q.id_speciality, q.id_entry_base, q.id_form_of_study)
                    spec_entries = by_spec.get(key, [])
                    budget_left = q.budget_places or 0
                    contract_left = q.contract_places or 0
                    # Перший прохід: квоти вже мають статус STATUS_KVOTA та з'їдають бюджет
                    for e in spec_entries:
                        if e.status == STATUS_KVOTA:
                            budget_left = max(0, budget_left - 1)
                    # Другий прохід: виставляємо статуси не-квота-абітурієнтам у порядку position.
                    # Не допущені (STATUS_EXCLUDED, DK-43) місць не займають і статус зберігають.
                    for e in sorted(spec_entries, key=lambda x: x.position):
                        if e.status in (STATUS_KVOTA, STATUS_EXCLUDED):
                            continue
                        if budget_left > 0:
                            e.status = STATUS_BUDGET
                            budget_left -= 1
                        elif contract_left > 0:
                            e.status = STATUS_CONTRACT
                            contract_left -= 1
                        else:
                            e.status = STATUS_REJECTED

                # Обчислені рядки повертаємо — запис робить persist_entries.
                return entries
        except Exception as e:
            print(f"[RatingService][compute_entries][ERROR] {e}")
            raise

    def persist_entries(
        self, id_campaign: int, entries: List[RatingEntryModel]
    ) -> Tuple[RatingSnapshotModel, List[RatingEntryModel]]:
        """Зберігає обчислені рядки: видаляє попередній знімок кампанії, створює
        новий і записує рядки, потім перечитує з relationships. Виконується на
        event loop (швидкий запис), а не в потоці — див. `compute_entries` (DK-44)."""
        try:
            with rx.session() as session:
                # Видаляємо попередній рейтинг кампанії і зберігаємо новий
                RatingDao.delete_for_campaign(id_campaign, session)

                snapshot = RatingSnapshotModel(id_campaign=id_campaign)
                RatingDao.add_snapshot(snapshot, entries, session)
                session.commit()
                session.refresh(snapshot)

                # Перечитуємо з повними relationships для відображення
                snapshot_loaded = RatingDao.get_latest_for_campaign(id_campaign, session)
                fresh_entries = list(RatingDao.get_entries(snapshot_loaded.id, session)) if snapshot_loaded else []
                return snapshot_loaded if snapshot_loaded is not None else snapshot, fresh_entries
        except Exception as e:
            print(f"[RatingService][persist_entries][ERROR] {e}")
            raise

    def get_documents_payload(
        self,
        id_campaign: int,
        spec_key: str = "__all__",
        base_key: str = "__all__",
        form_key: str = "__all__",
    ) -> Tuple[List[Dict], Optional[str]]:
        """Збирає дані для DOCX-рейтингу по кожному потоку (спеціальність+база+форма)
        з останнього знімка кампанії. Один елемент списку = один потік = один файл.

        Фільтри `spec_key`/`base_key`/`form_key` ("__all__" — без фільтра) дозволяють
        обмежити вибірку (наприклад, для завантаження одного потоку). Повертає
        `(payloads, generated_at_iso)`; кожен payload готовий до `RatingReport(**p)`.
        """
        try:
            with rx.session() as session:
                campaign = session.get(AdmissionCampaignModel, id_campaign)
                if campaign is None:
                    raise ValueError(f"Кампанію #{id_campaign} не знайдено")

                snapshot = RatingDao.get_latest_for_campaign(id_campaign, session)
                if snapshot is None:
                    return [], None
                entries = list(RatingDao.get_entries(snapshot.id, session))
                if not entries:
                    return [], snapshot.generated_at.isoformat()

                # Рік кампанії у вигляді двох цифр — як у назві групи (DK-24).
                try:
                    yy = f"{int(campaign.start_date[:4]) % 100:02d}"
                except (ValueError, TypeError):
                    yy = ""

                # Квоти кампанії: місця + довідники (tag спеціальності, префікси).
                quotas = session.exec(
                    select(AdmissionCampaignSpecialityModel)
                    .options(
                        selectinload(AdmissionCampaignSpecialityModel.speciality),
                        selectinload(AdmissionCampaignSpecialityModel.entry_base),
                        selectinload(AdmissionCampaignSpecialityModel.form_of_study),
                    )
                    .where(AdmissionCampaignSpecialityModel.id_admission_campaign == id_campaign)
                ).all()
                quota_map = {
                    (q.id_speciality, q.id_entry_base, q.id_form_of_study): q
                    for q in quotas
                }

                # Предмети ЗНО, що враховуються у рейтингу (DK-47): у документ ідуть
                # лише їхні колонки оцінок.
                rated_item_ids = {
                    i.id
                    for i in session.exec(
                        select(ItemZnoModel)
                        .where(ItemZnoModel.is_counted_in_rating == True)
                        .where(ItemZnoModel.is_deleted == False)
                    ).all()
                }

                # Оцінки по іспитах: results_zno для всіх осіб знімка (person.id == entrant.id).
                entrant_ids = [e.id_entrant for e in entries]
                grades_by_person: Dict[int, Dict[int, float]] = {}
                item_titles: Dict[int, str] = {}
                if entrant_ids:
                    results = session.exec(
                        select(ResultZnoModel)
                        .options(selectinload(ResultZnoModel.item_zno))
                        .where(ResultZnoModel.id_person.in_(entrant_ids))  # type: ignore[attr-defined]
                    ).all()
                    for r in results:
                        if r.id_items_zno not in rated_item_ids:
                            continue
                        grades_by_person.setdefault(r.id_person, {})[r.id_items_zno] = r.points
                        if r.item_zno is not None:
                            item_titles[r.id_items_zno] = r.item_zno.title

                # Групуємо записи знімка за потоком (спеціальність+база+форма),
                # зберігаючи порядок появи.
                groups: Dict[Tuple[int, int, int], List[RatingEntryModel]] = {}
                order: List[Tuple[int, int, int]] = []
                for e in entries:
                    key = (e.id_speciality, e.id_entry_base, e.id_form_of_study)
                    if key not in groups:
                        groups[key] = []
                        order.append(key)
                    groups[key].append(e)

                payloads: List[Dict] = []
                for key in order:
                    speciality_id, base_id, form_id = key
                    spec_only = str(speciality_id)
                    if spec_key != "__all__" and spec_only != spec_key:
                        continue
                    if base_key != "__all__" and str(base_id) != base_key:
                        continue
                    if form_key != "__all__" and str(form_id) != form_key:
                        continue

                    group_entries = groups[key]
                    q = quota_map.get(key)
                    spec = q.speciality if q is not None else group_entries[0].speciality
                    base = q.entry_base if q is not None else None
                    form = q.form_of_study if q is not None else None

                    # Не допущені за статусом (DK-43) до офіційного документа не потрапляють.
                    ranked_entries = [e for e in group_entries if e.status != STATUS_EXCLUDED]

                    # Колонки іспитів — об'єднання предметів, за якими є оцінки у цьому
                    # потоці, впорядковане за id предмета (стабільний порядок колонок).
                    item_ids = set()
                    for e in ranked_entries:
                        item_ids.update(grades_by_person.get(e.id_entrant, {}).keys())
                    ordered_items = sorted(item_ids)
                    exams = [item_titles.get(i, f"#{i}") for i in ordered_items]

                    budget_places = q.budget_places if q is not None else 0
                    contract_places = q.contract_places if q is not None else 0

                    applicants: List[Dict] = []
                    for e in sorted(ranked_entries, key=lambda x: x.position):
                        pgrades = grades_by_person.get(e.id_entrant, {})
                        grades = [pgrades.get(i, 0) for i in ordered_items]
                        pib = (
                            e.entrant.person.pib
                            if e.entrant is not None and e.entrant.person is not None and e.entrant.person.pib
                            else f"#{e.id_entrant}"
                        )
                        phone = (
                            e.entrant.person.phone_number
                            if e.entrant is not None and e.entrant.person is not None and e.entrant.person.phone_number
                            else ""
                        )
                        applicants.append(
                            {
                                "pib": pib,
                                "phone": phone,
                                "grades": grades,
                                # Квота проходить на бюджет → budget=True; контракт окремо.
                                "budget": e.status in (STATUS_BUDGET, STATUS_KVOTA),
                                "contract": e.status == STATUS_CONTRACT,
                            }
                        )

                    # Повні тезки в межах потоку — розрізняємо телефоном (DK-36).
                    disp = disambiguate_pib((a["pib"], a["phone"]) for a in applicants)
                    for a, shown in zip(applicants, disp):
                        a["pib"] = shown

                    base_prefix = base.prefix if base is not None else ""
                    form_prefix = form.prefix if form is not None else ""
                    tag = spec.tag if spec is not None else str(speciality_id)
                    file_stem = f"{tag}-{yy}{base_prefix}{form_prefix}"

                    spec_title = f"{spec.code} {spec.title} ({spec.tag})" if spec is not None else str(speciality_id)
                    base_title = base.title if base is not None else "—"

                    payloads.append(
                        {
                            "file_stem": file_stem,
                            "specialty": spec_title,
                            "admission_base": base_title,
                            "budget_places": budget_places,
                            "total_places": budget_places + contract_places,
                            "report_date": snapshot.generated_at.date(),
                            "exams": exams,
                            "applicants": applicants,
                        }
                    )

                return payloads, snapshot.generated_at.isoformat()
        except Exception as e:
            print(f"[RatingService][get_documents_payload][ERROR] {e}")
            raise
