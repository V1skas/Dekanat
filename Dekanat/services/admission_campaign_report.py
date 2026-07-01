import json
import reflex as rx

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Tuple

from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.dao.admission_campaign_report import AdmissionCampaignReportDao
from Dekanat.models import (
    AdmissionCampaignModel,
    AdmissionCampaignReportModel,
    EntrantModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialityModel,
)


def _spec_label(s: Optional[SpecialityModel]) -> str:
    if s is None:
        return "—"
    return f"{s.code} {s.title} ({s.tag})"


class AdmissionCampaignReportService:
    """Звіт по приймальній кампанії: числа за день/тиждень/період, серії
    по дням, розподіл по специальностях. Знімок зберігається у БД як JSON,
    щоб не дублювати обчислення при кожному відкритті сторінки (DK-25)."""

    # ---- read ----

    def get_latest(self, id_campaign: int) -> Optional[AdmissionCampaignReportModel]:
        try:
            with rx.session() as session:
                return AdmissionCampaignReportDao.get_latest_for_campaign(id_campaign, session)
        except Exception as e:
            print(f"[AdmissionCampaignReportService][get_latest][ERROR] {e}")
            return None

    def get_payload(self, id_campaign: int) -> Tuple[Optional[Dict], Optional[datetime]]:
        snap = self.get_latest(id_campaign)
        if snap is None:
            return None, None
        try:
            return json.loads(snap.payload), snap.generated_at
        except Exception as e:
            print(f"[AdmissionCampaignReportService][get_payload][ERROR] {e}")
            return None, snap.generated_at

    # ---- generate ----

    def generate(self, id_campaign: int) -> Tuple[Dict, datetime]:
        try:
            with rx.session() as session:
                campaign = session.get(AdmissionCampaignModel, id_campaign)
                if campaign is None:
                    raise ValueError(f"Кампанію #{id_campaign} не знайдено")

                # Діапазон кампанії
                try:
                    start_d = date.fromisoformat(campaign.start_date)
                    end_d = date.fromisoformat(campaign.end_date)
                except (ValueError, TypeError):
                    today = date.today()
                    start_d, end_d = today, today
                start_dt = datetime.combine(start_d, datetime.min.time())
                end_dt = datetime.combine(end_d, datetime.max.time())

                entrants = session.exec(
                    select(EntrantModel)
                    .options(
                        selectinload(EntrantModel.person).selectinload(PersonModel.entry_base),
                        selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality).selectinload(SpecialityModel.department),
                        selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.form_of_study),
                    )
                    .join(PersonModel, EntrantModel.id == PersonModel.id)
                    .where(EntrantModel.is_deleted == False)
                    .where(EntrantModel.created_at >= start_dt)
                    .where(EntrantModel.created_at <= end_dt)
                ).all()

                today = date.today()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())
                week_start = today - timedelta(days=6)  # вкл. сьогодні — 7 днів
                week_start_dt = datetime.combine(week_start, datetime.min.time())

                # ---- лічильники ----
                total_today = 0
                total_week = 0
                total_period = len(entrants)

                # Серія по днях усього періоду — мапа date.iso → count.
                period_counts: Dict[str, int] = {}
                cur = start_d
                while cur <= end_d:
                    period_counts[cur.isoformat()] = 0
                    cur += timedelta(days=1)

                # Серія по днях тижня (від week_start до today включно).
                week_counts: Dict[str, int] = {}
                cur = week_start
                while cur <= today:
                    week_counts[cur.isoformat()] = 0
                    cur += timedelta(days=1)

                # Розподіл специальностей рахуємо окремо для трьох періодів —
                # day/week/period, щоб toggle на сторінці перемикався без перегенерації.
                spec_top: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}
                spec_any: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}

                # Нові зрізи (DK-26): по базах вступу, формах навчання, а також загальні
                # підсумки по специальностях (з розрізненням бази/форми) та по відділеннях.
                by_base: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}
                by_form: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}
                totals_by_spec: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}
                totals_by_dept: Dict[str, Dict[str, int]] = {"day": {}, "week": {}, "period": {}}

                def _bump(bucket: Dict[str, Dict[str, int]], name: str, in_today: bool, in_week: bool):
                    bucket["period"][name] = bucket["period"].get(name, 0) + 1
                    if in_week:
                        bucket["week"][name] = bucket["week"].get(name, 0) + 1
                    if in_today:
                        bucket["day"][name] = bucket["day"].get(name, 0) + 1

                for e in entrants:
                    if e.created_at is None:
                        continue
                    d_iso = e.created_at.date().isoformat()
                    in_today = today_start <= e.created_at <= today_end
                    in_week = week_start_dt <= e.created_at <= today_end
                    # «в період» — усі сюди потрапили за фільтром запиту.

                    if d_iso in period_counts:
                        period_counts[d_iso] += 1
                    if in_today:
                        total_today += 1
                    if in_week:
                        total_week += 1
                        if d_iso in week_counts:
                            week_counts[d_iso] += 1

                    seen_specs: set = set()
                    for s in (e.specialties or []):
                        label = _spec_label(s.speciality)
                        if s.priority == 1:
                            spec_top["period"][label] = spec_top["period"].get(label, 0) + 1
                            if in_week:
                                spec_top["week"][label] = spec_top["week"].get(label, 0) + 1
                            if in_today:
                                spec_top["day"][label] = spec_top["day"].get(label, 0) + 1
                        if label not in seen_specs:
                            spec_any["period"][label] = spec_any["period"].get(label, 0) + 1
                            if in_week:
                                spec_any["week"][label] = spec_any["week"].get(label, 0) + 1
                            if in_today:
                                spec_any["day"][label] = spec_any["day"].get(label, 0) + 1
                            seen_specs.add(label)

                    # Розподіл по базі вступу — по особі (одна база на абітурієнта).
                    base_name = (
                        e.person.entry_base.title
                        if e.person is not None and e.person.entry_base is not None
                        else "—"
                    )
                    _bump(by_base, base_name, in_today, in_week)

                    # Форма навчання, підсумок по специальності (з базою/формою) та по
                    # відділенню — рахуємо за пріоритетною (priority=1) специальністю.
                    top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                    if top is not None:
                        form_name = top.form_of_study.title if top.form_of_study is not None else "—"
                        _bump(by_form, form_name, in_today, in_week)
                        spec_lbl = _spec_label(top.speciality)
                        _bump(totals_by_spec, f"{spec_lbl} · {base_name} · {form_name}", in_today, in_week)
                        dept_name = (
                            top.speciality.department.title
                            if top.speciality is not None and top.speciality.department is not None
                            else "—"
                        )
                        _bump(totals_by_dept, dept_name, in_today, in_week)

                def _bucket_to_list(d: Dict[str, int]) -> List[Dict]:
                    return sorted(
                        [{"spec": k, "count": v} for k, v in d.items()],
                        key=lambda r: r["count"],
                        reverse=True,
                    )

                payload = {
                    "campaign_id": id_campaign,
                    "campaign_title": campaign.title,
                    "campaign_start": campaign.start_date,
                    "campaign_end": campaign.end_date,
                    "today_iso": today.isoformat(),
                    "totals": {
                        "today": total_today,
                        "week": total_week,
                        "period": total_period,
                    },
                    "week_series": [
                        {"date": d, "count": c} for d, c in week_counts.items()
                    ],
                    "period_series": [
                        {"date": d, "count": c} for d, c in period_counts.items()
                    ],
                    "by_spec_top": {
                        "day": _bucket_to_list(spec_top["day"]),
                        "week": _bucket_to_list(spec_top["week"]),
                        "period": _bucket_to_list(spec_top["period"]),
                    },
                    "by_spec_any": {
                        "day": _bucket_to_list(spec_any["day"]),
                        "week": _bucket_to_list(spec_any["week"]),
                        "period": _bucket_to_list(spec_any["period"]),
                    },
                    "by_entry_base": {
                        "day": _bucket_to_list(by_base["day"]),
                        "week": _bucket_to_list(by_base["week"]),
                        "period": _bucket_to_list(by_base["period"]),
                    },
                    "by_form": {
                        "day": _bucket_to_list(by_form["day"]),
                        "week": _bucket_to_list(by_form["week"]),
                        "period": _bucket_to_list(by_form["period"]),
                    },
                    "totals_by_spec": {
                        "day": _bucket_to_list(totals_by_spec["day"]),
                        "week": _bucket_to_list(totals_by_spec["week"]),
                        "period": _bucket_to_list(totals_by_spec["period"]),
                    },
                    "totals_by_department": {
                        "day": _bucket_to_list(totals_by_dept["day"]),
                        "week": _bucket_to_list(totals_by_dept["week"]),
                        "period": _bucket_to_list(totals_by_dept["period"]),
                    },
                }

                # Перезаписуємо останній знімок кампанії — історія не зберігається.
                AdmissionCampaignReportDao.delete_for_campaign(id_campaign, session)
                snap = AdmissionCampaignReportModel(
                    id_campaign=id_campaign,
                    payload=json.dumps(payload, ensure_ascii=False),
                )
                AdmissionCampaignReportDao.add_one(snap, session)
                session.commit()
                session.refresh(snap)
                return payload, snap.generated_at
        except Exception as e:
            print(f"[AdmissionCampaignReportService][generate][ERROR] {e}")
            raise
