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

    def get_entrant_counts(self, group_ids: Sequence[int]) -> Dict[int, int]:
        """Мапа `{group_id: кількість активних абітурієнтів}` (DK-42)."""
        try:
            with rx.session() as session:
                return EntrantsGroupDao.get_entrant_counts(group_ids, session)
        except Exception as e:
            print(f"[EntrantsGroupService][get_entrant_counts][ERROR] {e}")
            raise

    # ---------- Автоформування груп ----------

    def preview_auto_groups(self, max_size: int, use_existing: bool = False) -> List[Dict]:
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

        Якщо `use_existing=True` (DK-42): перш ніж створювати нові групи, доповнюємо
        вже наявні (не видалені) групи тієї самої специальності/бази/форми до `max_size`,
        і лише тих, хто не вмістився, розкидаємо по нових групах. Наявні групи у
        результаті мають ненульовий `id` та `existing_count` (скільки вже в них є).

        Повертає список словників:
        ``{"id": int, "title": str, "spec_code": str, "spec_dept": int, "spec_label": str,
           "existing_count": int, "entrants": List[{"id": int, "pib": str, "spec_label": str}]}``.
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

            # Згрупуємо кандидатів за кортежем (приоритетная специальность, база
            # вступу, форма навчання) — назва групи враховує префікси бази та форми
            # (DK-26). Робимо це першим: префікси цих бакетів потрібні, щоб визначити
            # базу/форму порожньої, вручну створеної групи за її назвою (DK-42).
            by_spec: Dict[Tuple[int, int, int], Dict] = {}
            for e in candidates:
                top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                if top is None or top.speciality is None or top.form_of_study is None:
                    continue
                if e.person is None or e.person.entry_base is None:
                    continue
                base = e.person.entry_base
                form = top.form_of_study
                key = (top.id_speciality, base.id, form.id)
                bucket = by_spec.setdefault(key, {
                    "spec": top.speciality,
                    "base": base,
                    "form": form,
                    "entrants": [],
                })
                bucket["entrants"].append(e)

            # Префікс назви групи для бакета: (тег)-(рік)(префікс бази)(префікс форми)-.
            def _bucket_prefix(bucket: Dict) -> str:
                spec: SpecialityModel = bucket["spec"]
                base = bucket["base"]
                form = bucket["form"]
                return f"{spec.tag}-{yy}{base.prefix or ''}{form.prefix or ''}-"

            prefix_by_key: Dict[Tuple[int, int, int], str] = {
                key: _bucket_prefix(b) for key, b in by_spec.items()
            }

            def _bucket_from_title(title: Optional[str]) -> Optional[Tuple[int, int, int]]:
                """Визначає бакет (спеціальність, база, форма) за назвою групи.

                Потрібно для порожньої, вручну створеної групи, у якої немає членів,
                за якими можна було б визначити базу/форму. Назва має відповідати
                шаблону автоформування `<TAG>-<YY><база><форма>-<N>`; тоді збіг із
                префіксом одного з бакетів кандидатів однозначно дає його ключ."""
                if not title:
                    return None
                for key, prefix in prefix_by_key.items():
                    if title.startswith(prefix) and title[len(prefix):].isdigit():
                        return key
                return None

            # Усі не видалені групи — потрібні і для продовження нумерації, і для
            # режиму дозаповнення (визначення бакета наявних/порожніх груп).
            all_groups = list(
                session.exec(select(EntrantGroupModel).where(EntrantGroupModel.is_deleted == False)).all()
            )
            existing_titles = {g.title for g in all_groups if g.title}

            # Наявні (не видалені) групи — для режиму дозаповнення (DK-42).
            # Бакет групи з абітурієнтами визначаємо за її поточними членами
            # (пріоритетна спеціальність + база + форма). Для порожньої, вручну
            # створеної групи членів немає — тоді визначаємо бакет за назвою
            # (`_bucket_from_title`), щоб теж дозаповнити її; точну кількість беремо
            # окремим запитом (члени поза діапазоном кампанії теж рахуються).
            existing_by_bucket: Dict[Tuple[int, int, int], List[Tuple[int, str, int]]] = {}
            if use_existing:
                counts = EntrantsGroupDao.get_entrant_counts([g.id for g in all_groups], session)
                member_bucket: Dict[int, Tuple[int, int, int]] = {}
                for e in entrants:
                    if _is_free(e):
                        continue
                    g = e.entrant_group
                    if g is None or g.is_deleted or g.id in member_bucket:
                        continue
                    top = next((s for s in (e.specialties or []) if s.priority == 1), None)
                    if (
                        top is not None and top.speciality is not None and top.form_of_study is not None
                        and e.person is not None and e.person.entry_base is not None
                    ):
                        member_bucket[g.id] = (top.id_speciality, e.person.entry_base.id, top.form_of_study.id)
                for g in all_groups:
                    cnt = counts.get(g.id, 0)
                    bucket_key = member_bucket.get(g.id)
                    if bucket_key is None and cnt == 0:
                        bucket_key = _bucket_from_title(g.title)
                    if bucket_key is None:
                        continue
                    existing_by_bucket.setdefault(bucket_key, []).append(
                        (g.id, g.title or f"#{g.id}", cnt)
                    )
                for lst in existing_by_bucket.values():
                    lst.sort(key=lambda t: t[1])  # стабільний порядок за назвою

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

            def _entrant_dict(e: EntrantModel, spec_label: str) -> Dict:
                return {
                    "id": e.id,
                    "pib": (e.person.pib if e.person and e.person.pib else f"#{e.id}"),
                    "spec_label": spec_label,
                }

            result: List[Dict] = []
            for bucket_key, bucket in by_spec.items():
                spec: SpecialityModel = bucket["spec"]
                base = bucket["base"]
                form = bucket["form"]
                ents: List[EntrantModel] = bucket["entrants"]
                # Стабільний порядок: за ПІБ.
                ents.sort(key=lambda e: (e.person.pib if e.person and e.person.pib else "").lower())
                spec_label = f"{spec.code} {spec.title} ({spec.tag}) · {base.title} · {form.title}"
                # Шаблон назви: (тег)-(рік)(префікс бази)(префікс форми)-(номер) (DK-26).
                prefix = prefix_by_key[bucket_key]

                remaining = list(ents)

                # Крок 1 (DK-42): дозаповнюємо наявні групи цієї специальності до max_size.
                if use_existing:
                    for gid, gtitle, gcount in existing_by_bucket.get(bucket_key, []):
                        free = max_size - gcount
                        if free <= 0 or not remaining:
                            continue
                        take = remaining[:free]
                        remaining = remaining[free:]
                        result.append({
                            "id": gid,
                            "title": gtitle,
                            "spec_code": spec.code,
                            "spec_dept": spec.id_department,
                            "spec_label": spec_label,
                            "existing_count": gcount,
                            "entrants": [_entrant_dict(e, spec_label) for e in take],
                        })

                # Крок 2: тих, хто лишився, розкидаємо по нових групах.
                # Рівномірний розподіл: якщо груп більше однієї, ділимо людей
                # навпіл/натретіх якомога рівніше. Перші `extras` груп отримують
                # на одну людину більше, решта — порівну. Так уникаємо ситуації
                # 30/30/13 при max=30 для 73 кандидатів — буде 25/24/24.
                total = len(remaining)
                groups_n = math.ceil(total / max_size) if total else 0
                chunks: List[List[EntrantModel]] = []
                if groups_n <= 1:
                    if remaining:
                        chunks = [remaining]
                else:
                    per = total // groups_n
                    extras = total % groups_n
                    start = 0
                    for i in range(groups_n):
                        size = per + (1 if i < extras else 0)
                        chunks.append(remaining[start:start + size])
                        start += size

                n = _next_number(prefix)
                for chunk in chunks:
                    title = f"{prefix}{n}"
                    n += 1
                    # Реєструємо ім'я, щоб подальші виклики не повторили його.
                    existing_titles.add(title)
                    result.append({
                        "id": 0,
                        "title": title,
                        "spec_code": spec.code,
                        "spec_dept": spec.id_department,
                        "spec_label": spec_label,
                        "existing_count": 0,
                        "entrants": [_entrant_dict(e, spec_label) for e in chunk],
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
                    f"{top.speciality.code} {top.speciality.title} ({top.speciality.tag})"
                    if top is not None and top.speciality is not None
                    else "—"
                )
                result.append({"id": e.id, "pib": pib, "spec_label": spec_label})
            result.sort(key=lambda r: r["pib"].lower())
            return result

    def bulk_create_with_entrants(self, groups: List[Dict]) -> int:
        """Зберігає підготовлені групи з їх складом в одній транзакції.

        Очікує `groups` у форматі `preview_auto_groups`. Групи з ненульовим `id`
        (DK-42) — це наявні групи в режимі дозаповнення: до них абітурієнти
        **дописуються** без чіпання поточного складу. Решта створюються заново.
        Повертає кількість опрацьованих груп. Перевірок ліміту розміру тут немає —
        користувач уже міг руками додати/видалити учасників.
        """
        try:
            with rx.session() as session:
                processed = 0
                for g in groups:
                    ids = [e["id"] for e in g.get("entrants", [])]
                    existing_id = g.get("id") or 0
                    if existing_id:
                        # Дозаповнення наявної групи — тільки дописуємо нових.
                        if ids:
                            EntrantsGroupDao.append_entrants(existing_id, ids, session)
                    else:
                        group = EntrantGroupModel(title=g["title"])
                        session.add(group)
                        session.flush()
                        if ids:
                            EntrantsGroupDao.replace_entrants(group.id, ids, session)
                    processed += 1
                session.commit()
                return processed
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
                opp = ""
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
                            specialty = f"{top.speciality.code} {top.speciality.title} ({top.speciality.tag})"
                            opp = top.speciality.educational_and_professional_program or ""

                applicants.sort(key=lambda a: a["name"].lower())
                return {
                    "group_title": group.title or f"#{group_id}",
                    "specialty": specialty,
                    "opp": opp,
                    "subject": subject,
                    "applicants": applicants,
                }
        except Exception as e:
            print(f"[EntrantsGroupService][get_exam_sheet_payload][ERROR] {e}")
            raise
