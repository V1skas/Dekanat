import math
import reflex as rx

from datetime import datetime
from typing import Optional, Sequence, Tuple, List, Dict

from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.models import (
    EntrantGroupModel,
    EntrantModel,
    EntrantExamModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialityModel,
    InformationAboutRelativesModel,
)
from Dekanat.services.admission_campaign import AdmissionCampaignService


class EntrantsGroupService:
    def get_list_items(
        self,
        title: Optional[str] = None,
        created_between: Optional[Tuple[datetime, datetime]] = None,
    ) -> Sequence[EntrantGroupModel]:
        """Повертає групи із серверною фільтрацією по переданих параметрах."""
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_all(
                    session,
                    title_substring=title,
                    created_between=created_between,
                )
        except Exception as e:
            print(f"[EntrantsGroupService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[EntrantGroupModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_by_id(id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                managed = EntrantsGroupDao.add_one(item, session)
                session.flush()
                if entrant_ids:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                managed = EntrantsGroupDao.edit_one(item, session)
                if entrant_ids is not None:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantGroupModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantsGroupDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[EntrantsGroupService][delete_one][ERROR] {e}")
            return False

    def get_entrants(self, group_id: int) -> Sequence[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_entrants_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_entrants][ERROR] {e}")
            raise

    def get_assignable_entrants(self, group_id: Optional[int]) -> Sequence[EntrantModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_assignable_entrants(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_assignable_entrants][ERROR] {e}")
            raise

    # ---------- Автоформування груп ----------

    def preview_auto_groups(self, max_size: int) -> List[Dict]:
        """Розрахувати склад нових екзаменаційних груп без збереження.

        Правила (DK-24):
        * Беремо абітурієнтів активної кампанії (за `created_at`).
        * Лише ті, хто ще не у групі (`id_entrant_group IS NULL` або стара група soft-deleted).
        * У абітурієнта має бути приоритетна (priority=1) спеціальність — інакше до групи
          поставити неможливо, він пропускається.
        * Розбиваємо за приоритетной специальностью; всередині — нарізаємо на групи по
          `max_size` (останній блок може бути меншим).
        * Імʼя: `<TAG>-<YY>-<N>`, де YY — дві останні цифри року старту кампанії,
          N — порядковий номер для цієї спеціальності у цьому році (з урахуванням
          уже існуючих груп з таким префіксом у БД, щоб не плодити дублів).

        Повертає список словників:
        ``{"title": str, "spec_code": str, "spec_dept": int, "spec_label": str,
           "entrants": List[{"id": int, "pib": str}]}``.
        """
        if max_size < 1:
            raise ValueError("Максимальний розмір групи має бути не менше 1")

        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None:
            raise RuntimeError("Немає активної вступної кампанії")
        try:
            year_full = int(campaign.start_date[:4])
        except (ValueError, TypeError):
            year_full = datetime.now().year
        yy = f"{year_full % 100:02d}"
        active_range = AdmissionCampaignService().get_active_range()

        with rx.session() as session:
            # Кандидати: абітурієнти кампанії, не в групі, з priority=1 спеціальністю.
            stmt = (
                select(EntrantModel)
                .options(
                    selectinload(EntrantModel.person).selectinload(PersonModel.entry_base),
                    selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality),
                    selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.form_of_study),
                    selectinload(EntrantModel.entrant_group),
                )
                .join(PersonModel, EntrantModel.id == PersonModel.id)
                .where(EntrantModel.is_deleted == False)
            )
            if active_range is not None:
                start_dt, end_dt = active_range
                stmt = stmt.where(EntrantModel.created_at >= start_dt).where(EntrantModel.created_at <= end_dt)
            entrants = session.exec(stmt).all()

            # Фільтр «не в активній групі» — soft-deleted допустимо.
            def _is_free(e: EntrantModel) -> bool:
                if e.id_entrant_group is None:
                    return True
                return bool(e.entrant_group and e.entrant_group.is_deleted)

            candidates = [e for e in entrants if _is_free(e)]

            # Згрупуємо за кортежем (приоритетная специальность, база вступу, форма
            # навчання) — назва групи тепер враховує префікси бази та форми (DK-26).
            by_spec: Dict[Tuple[str, int, int, int], Dict] = {}
            for e in candidates:
                top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                if top is None or top.speciality is None or top.form_of_study is None:
                    continue
                if e.person is None or e.person.entry_base is None:
                    continue
                base = e.person.entry_base
                form = top.form_of_study
                key = (top.id_speciality_code, top.id_speciality_department, base.id, form.id)
                bucket = by_spec.setdefault(key, {
                    "spec": top.speciality,
                    "base": base,
                    "form": form,
                    "entrants": [],
                })
                bucket["entrants"].append(e)

            # Перерахуємо існуючі групи з префіксом TAG-YY-, щоб продовжити нумерацію.
            existing_titles = {
                row.title
                for row in session.exec(select(EntrantGroupModel).where(EntrantGroupModel.is_deleted == False)).all()
            }

            def _next_number(prefix: str) -> int:
                # Найбільший вже наявний номер з таким префіксом + 1.
                max_n = 0
                for t in existing_titles:
                    if not t.startswith(prefix):
                        continue
                    suffix = t[len(prefix):]
                    if suffix.isdigit():
                        max_n = max(max_n, int(suffix))
                return max_n + 1

            result: List[Dict] = []
            for (code, dept, base_id, form_id), bucket in by_spec.items():
                spec: SpecialityModel = bucket["spec"]
                base = bucket["base"]
                form = bucket["form"]
                ents: List[EntrantModel] = bucket["entrants"]
                # Стабільний порядок: за ПІБ.
                ents.sort(key=lambda e: (e.person.pib if e.person and e.person.pib else "").lower())
                base_prefix = base.prefix or ""
                form_prefix = form.prefix or ""
                spec_label = f"{spec.code} {spec.title} · {base.title} · {form.title}"
                # Шаблон назви: (тег)-(рік)(префікс бази)(префікс форми)-(номер) (DK-26).
                prefix = f"{spec.tag}-{yy}{base_prefix}{form_prefix}-"
                n = _next_number(prefix)
                # Рівномірний розподіл: якщо груп більше однієї, ділимо людей
                # навпіл/натретіх якомога рівніше. Перші `extras` груп отримують
                # на одну людину більше, решта — порівну. Так уникаємо ситуації
                # 30/30/13 при max=30 для 73 кандидатів — буде 25/24/24.
                total = len(ents)
                groups_n = math.ceil(total / max_size) if total else 0
                chunks: List[List[EntrantModel]] = []
                if groups_n <= 1:
                    if ents:
                        chunks = [ents]
                else:
                    base = total // groups_n
                    extras = total % groups_n
                    start = 0
                    for i in range(groups_n):
                        size = base + (1 if i < extras else 0)
                        chunks.append(ents[start:start + size])
                        start += size

                for chunk in chunks:
                    title = f"{prefix}{n}"
                    n += 1
                    # Реєструємо ім'я, щоб подальші виклики не повторили його.
                    existing_titles.add(title)
                    result.append({
                        "title": title,
                        "spec_code": code,
                        "spec_dept": dept,
                        "spec_label": spec_label,
                        "entrants": [
                            {
                                "id": e.id,
                                "pib": (e.person.pib if e.person and e.person.pib else f"#{e.id}"),
                                "spec_label": spec_label,
                            }
                            for e in chunk
                        ],
                    })

            # Стабільне сортування результату — за назвою.
            result.sort(key=lambda g: g["title"])
            return result

    def get_assignable_for_campaign(self) -> List[Dict]:
        """Список «вільних» абітурієнтів активної кампанії — для пікера ручного
        додавання у попередньо сформовану групу.
        Повертає словники ``{"id": int, "pib": str, "spec_label": str}``."""
        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None:
            return []
        active_range = AdmissionCampaignService().get_active_range()
        with rx.session() as session:
            stmt = (
                select(EntrantModel)
                .options(
                    selectinload(EntrantModel.person),
                    selectinload(EntrantModel.entrant_group),
                    selectinload(EntrantModel.specialties).selectinload(SpecialtieEntrantModel.speciality),
                )
                .where(EntrantModel.is_deleted == False)
            )
            if active_range is not None:
                start_dt, end_dt = active_range
                stmt = stmt.where(EntrantModel.created_at >= start_dt).where(EntrantModel.created_at <= end_dt)
            entrants = session.exec(stmt).all()
            result: List[Dict] = []
            for e in entrants:
                in_active_group = (
                    e.id_entrant_group is not None
                    and e.entrant_group is not None
                    and not e.entrant_group.is_deleted
                )
                if in_active_group:
                    continue
                pib = e.person.pib if e.person and e.person.pib else f"#{e.id}"
                top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                spec_label = (
                    f"{top.speciality.code} {top.speciality.title}"
                    if top is not None and top.speciality is not None
                    else "—"
                )
                result.append({"id": e.id, "pib": pib, "spec_label": spec_label})
            result.sort(key=lambda r: r["pib"].lower())
            return result

    def bulk_create_with_entrants(self, groups: List[Dict]) -> int:
        """Зберігає підготовлені групи з їх складом в одній транзакції.

        Очікує `groups` у форматі `preview_auto_groups`. Повертає кількість
        створених груп. Перевірок ліміту розміру тут немає — користувач уже
        міг руками додати/видалити учасників.
        """
        try:
            with rx.session() as session:
                created = 0
                for g in groups:
                    group = EntrantGroupModel(title=g["title"])
                    session.add(group)
                    session.flush()
                    ids = [e["id"] for e in g.get("entrants", [])]
                    if ids:
                        EntrantsGroupDao.replace_entrants(group.id, ids, session)
                    created += 1
                session.commit()
                return created
        except Exception as e:
            print(f"[EntrantsGroupService][bulk_create_with_entrants][ERROR] {e}")
            raise

    def get_exams(self, group_id: int) -> Sequence[EntrantExamModel]:
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_exams_by_group(group_id, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_exams][ERROR] {e}")
            raise

    def get_exam_sheet_payload(self, group_id: int) -> Dict:
        """Збирає дані для екзаменаційних відомостей по групі (DK-29).

        Повертає `{group_title, specialty, subject, applicants}`, де applicants —
        список `{name, phone, relatives}`. specialty береться з пріоритетної
        специальності абітурієнтів групи (вони з однієї специальності), subject —
        з предметів запланованих іспитів групи. Один запит за абітурієнтами
        (з особою, родичами, специальностями) і один — за іспитами.
        """
        try:
            with rx.session() as session:
                group = session.get(EntrantGroupModel, group_id)
                if group is None:
                    raise ValueError(f"Групу #{group_id} не знайдено")

                entrants = list(session.exec(
                    select(EntrantModel)
                    .options(
                        selectinload(EntrantModel.person)
                        .selectinload(PersonModel.information_about_relatives)
                        .selectinload(InformationAboutRelativesModel.kinship),
                        selectinload(EntrantModel.specialties)
                        .selectinload(SpecialtieEntrantModel.speciality),
                    )
                    .where(EntrantModel.id_entrant_group == group_id)
                    .where(EntrantModel.is_deleted == False)
                ).all())

                # Предмети (форма контролю) — з запланованих іспитів групи.
                exams = session.exec(
                    select(EntrantExamModel)
                    .options(selectinload(EntrantExamModel.item_zno))
                    .where(EntrantExamModel.id_group == group_id)
                    .where(EntrantExamModel.is_deleted == False)
                ).all()
                subjects: List[str] = []
                for ex in exams:
                    t = ex.item_zno.title if ex.item_zno is not None else None
                    if t and t not in subjects:
                        subjects.append(t)
                subject = ", ".join(subjects)

                specialty = ""
                applicants: List[Dict] = []
                for e in entrants:
                    p = e.person
                    pib = p.pib if p is not None and p.pib else f"#{e.id}"
                    phone = p.phone_number if p is not None and p.phone_number else ""
                    rel_parts: List[str] = []
                    for r in (p.information_about_relatives or []) if p is not None else []:
                        label = r.pib or ""
                        kin = r.kinship.title if r.kinship is not None else ""
                        if kin:
                            label = f"{label} ({kin})"
                        if r.phone_number:
                            label = f"{label} — {r.phone_number}"
                        if label.strip():
                            rel_parts.append(label)
                    applicants.append({
                        "name": pib,
                        "phone": phone,
                        "relatives": "\n".join(rel_parts),
                    })
                    if not specialty:
                        top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                        if top is None and e.specialties:
                            top = e.specialties[0]
                        if top is not None and top.speciality is not None:
                            specialty = f"{top.speciality.code} {top.speciality.title}"

                applicants.sort(key=lambda a: a["name"].lower())
                return {
                    "group_title": group.title or f"#{group_id}",
                    "specialty": specialty,
                    "subject": subject,
                    "applicants": applicants,
                }
        except Exception as e:
            print(f"[EntrantsGroupService][get_exam_sheet_payload][ERROR] {e}")
            raise
