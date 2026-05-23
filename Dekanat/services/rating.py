import reflex as rx

from typing import Optional, Dict, List, Tuple
from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.dao.rating import RatingDao
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
)


# Status constants for entries
STATUS_BUDGET = "budget"
STATUS_CONTRACT = "contract"
STATUS_KVOTA = "kvota"
STATUS_REJECTED = "rejected"


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
        """Розраховує рейтинг для всіх спеціальностей кампанії, зберігає та повертає його."""
        try:
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

                # Які спец. умови вважаються квотою
                kvota_codes = {
                    sc.subcategory_code
                    for sc in session.exec(
                        select(SpecialConditionModel).where(SpecialConditionModel.is_kvota == True)
                    ).all()
                }

                # Підготовка даних по кожному абітурієнту
                entrant_info: Dict[int, Dict] = {}
                for ent in entrants:
                    if ent.person is None:
                        continue
                    total = sum((r.points or 0) for r in (ent.person.results_zno or []))
                    has_kvota = any(
                        sc.id_special_condition in kvota_codes
                        for sc in (ent.person.special_conditions or [])
                    )
                    spec_keys = [
                        (s.id_speciality_code, s.id_speciality_department)
                        for s in (ent.specialties or [])
                    ]
                    entrant_info[ent.id] = {
                        "id": ent.id,
                        "total": total,
                        "kvota": has_kvota,
                        "specs": spec_keys,
                    }

                # Будуємо рейтинг для кожної спеціальності з квот кампанії
                entries: List[RatingEntryModel] = []
                for q in quotas:
                    key = (q.id_speciality_code, q.id_speciality_department)
                    applicants = [
                        info for info in entrant_info.values() if key in info["specs"]
                    ]
                    # Кандидати з квотою — нагору; в межах груп сортування за балом desc
                    kvotas = sorted(
                        [a for a in applicants if a["kvota"]],
                        key=lambda a: a["total"],
                        reverse=True,
                    )
                    others = sorted(
                        [a for a in applicants if not a["kvota"]],
                        key=lambda a: a["total"],
                        reverse=True,
                    )
                    ordered = kvotas + others

                    budget_seats = q.budget_places or 0
                    contract_seats = q.contract_places or 0
                    budget_filled = 0

                    for pos, info in enumerate(ordered, start=1):
                        if info["kvota"]:
                            status = STATUS_KVOTA
                            budget_filled += 1
                        elif budget_filled < budget_seats:
                            status = STATUS_BUDGET
                            budget_filled += 1
                        elif (
                            budget_filled - budget_seats < contract_seats
                            if budget_filled >= budget_seats
                            else False
                        ):
                            # not used branch; рівноцінно простішому лічильнику нижче
                            status = STATUS_CONTRACT
                        else:
                            status = ""  # вирішимо нижче

                        entries.append(
                            RatingEntryModel(
                                id_snapshot=0,  # set later
                                id_speciality_code=q.id_speciality_code,
                                id_speciality_department=q.id_speciality_department,
                                id_entrant=info["id"],
                                position=pos,
                                total_points=info["total"],
                                status=status,
                            )
                        )

                # Простіше визначити статус не-квота-абітурієнтів за лічильниками
                # (перепишемо statuses, що ще не виставлені)
                # Для цього групуємо вже сформовані entries за спеціальністю
                by_spec: Dict[Tuple[str, int], List[RatingEntryModel]] = {}
                for e in entries:
                    by_spec.setdefault((e.id_speciality_code, e.id_speciality_department), []).append(e)
                for q in quotas:
                    key = (q.id_speciality_code, q.id_speciality_department)
                    spec_entries = by_spec.get(key, [])
                    budget_left = q.budget_places or 0
                    contract_left = q.contract_places or 0
                    # Перший прохід: квоти вже мають статус STATUS_KVOTA та з'їдають бюджет
                    for e in spec_entries:
                        if e.status == STATUS_KVOTA:
                            budget_left = max(0, budget_left - 1)
                    # Другий прохід: виставляємо статуси не-квота-абітурієнтам у порядку position
                    for e in sorted(spec_entries, key=lambda x: x.position):
                        if e.status == STATUS_KVOTA:
                            continue
                        if budget_left > 0:
                            e.status = STATUS_BUDGET
                            budget_left -= 1
                        elif contract_left > 0:
                            e.status = STATUS_CONTRACT
                            contract_left -= 1
                        else:
                            e.status = STATUS_REJECTED

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
            print(f"[RatingService][generate][ERROR] {e}")
            raise
