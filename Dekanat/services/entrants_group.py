import math
import reflex as rx

from datetime import datetime
from types import SimpleNamespace
from typing import Optional, Sequence, Tuple, List, Dict

from sqlmodel import select
from sqlalchemy.orm import selectinload

from Dekanat.dao.entrants_group import EntrantsGroupDao
from Dekanat.dao.speciality import SpecialityDao
from Dekanat.models import (
    EntrantGroupModel,
    EntrantModel,
    EntrantExamModel,
    PersonModel,
    SpecialtieEntrantModel,
    SpecialityModel,
    EntryBaseModel,
    FormOfStudyModel,
    InformationAboutRelativesModel,
)
from Dekanat.services.admission_campaign import AdmissionCampaignService
from Dekanat.utils.clock import now_local
from Dekanat.audit import (
    record_action,
    GroupCreated,
    GroupUpdated,
    GroupDeleted,
    GroupMembersChanged,
)


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

    @staticmethod
    def _pibs_for_ids(session, ids) -> List[str]:
        """ПІБ абітурієнтів за їх id (для журналу зміни складу). id абітурієнта == id особи."""
        id_list = [i for i in (ids or [])]
        if not id_list:
            return []
        rows = session.exec(
            select(PersonModel.pib).where(PersonModel.id.in_(id_list))  # type: ignore[attr-defined]
        ).all()
        return sorted(rows)

    @staticmethod
    def _current_member_ids(session, group_id: int) -> List[int]:
        return list(session.exec(
            select(EntrantModel.id)
            .where(EntrantModel.id_entrant_group == group_id)
            .where(EntrantModel.is_deleted == False)
        ).all())

    def add_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None, actor_id: Optional[int] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                managed = EntrantsGroupDao.add_one(item, session)
                session.flush()
                if entrant_ids:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                record_action(session, actor_id, managed.id, GroupCreated(title=managed.title))
                if entrant_ids:
                    record_action(session, actor_id, managed.id, GroupMembersChanged(
                        added=self._pibs_for_ids(session, entrant_ids),
                    ))
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: EntrantGroupModel, entrant_ids: Optional[list[int]] = None, actor_id: Optional[int] = None) -> EntrantGroupModel:
        try:
            with rx.session() as session:
                old = EntrantsGroupDao.get_by_id(item.id, session)
                old_snap = SimpleNamespace(title=old.title if old else None)
                old_member_ids = set(self._current_member_ids(session, item.id)) if entrant_ids is not None else set()
                managed = EntrantsGroupDao.edit_one(item, session)
                if entrant_ids is not None:
                    EntrantsGroupDao.replace_entrants(managed.id, entrant_ids, session)
                session.flush()
                record_action(session, actor_id, item.id, GroupUpdated.from_diff(old_snap, managed))
                if entrant_ids is not None:
                    new_ids = set(entrant_ids)
                    added = new_ids - old_member_ids
                    removed = old_member_ids - new_ids
                    if added or removed:
                        record_action(session, actor_id, item.id, GroupMembersChanged(
                            added=self._pibs_for_ids(session, added),
                            removed=self._pibs_for_ids(session, removed),
                        ))
                session.commit()
                session.refresh(managed)
                return managed
        except Exception as e:
            print(f"[EntrantsGroupService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: EntrantGroupModel, actor_id: Optional[int] = None) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                EntrantsGroupDao.edit_one(item, session)
                record_action(session, actor_id, item.id, GroupDeleted(title=item.title))
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

    @staticmethod
    def _year_suffix(campaign) -> str:
        """Дві останні цифри року старту кампанії — для назви групи."""
        try:
            year_full = int(campaign.start_date[:4])
        except (ValueError, TypeError, AttributeError):
            year_full = now_local().year
        return f"{year_full % 100:02d}"

    @staticmethod
    def _top_specialty(e: EntrantModel) -> Optional[SpecialtieEntrantModel]:
        """Спеціальність найвищого пріоритету (найменше число) абітурієнта, або None,
        якщо спеціальностей немає взагалі (DK-48 — такі до груп не потрапляють)."""
        specs = list(e.specialties or [])
        if not specs:
            return None
        return min(specs, key=lambda s: s.priority if s.priority is not None else 10_000)

    @staticmethod
    def _bucket_prefix(
        spec: SpecialityModel, base: EntryBaseModel, form: FormOfStudyModel, yy: str
    ) -> str:
        """Префікс назви екзаменаційної групи: `<TAG>-<YY><тег>-` (DK-48).

        Тег береться з бази вступу; якщо у бази тег порожній — береться тег форми
        навчання. Якщо тег бази не порожній, тег форми не використовується взагалі
        (навіть якщо він теж заданий)."""
        base_prefix = (base.prefix or "").strip() if base is not None else ""
        form_prefix = (form.prefix or "").strip() if form is not None else ""
        tag_part = base_prefix if base_prefix else form_prefix
        return f"{spec.tag}-{yy}{tag_part}-"

    @staticmethod
    def _match_existing_groups(
        prefix: str, all_groups: List[EntrantGroupModel], counts: Dict[int, int]
    ) -> List[Tuple[int, str, int]]:
        """Наявні (не видалені) групи, чия назва відповідає шаблону `<prefix><N>`.

        Тип наявної групи визначається ВИКЛЮЧНО за її назвою — склад
        (спеціальності/форми/бази учасників) не враховується (DK-48). Групи з
        довільною назвою (що не збігається з жодним префіксом) не чіпаються.
        Повертає `(id, title, count)`, впорядковані за номером у назві."""
        matched: List[Tuple[int, str, int]] = []
        for g in all_groups:
            t = g.title or ""
            if t.startswith(prefix) and t[len(prefix):].isdigit():
                matched.append((g.id, t, counts.get(g.id, 0)))
        matched.sort(key=lambda x: int(x[1][len(prefix):]))
        return matched

    @staticmethod
    def _next_number(prefix: str, existing_titles) -> int:
        """Найбільший вже наявний номер з таким префіксом + 1."""
        max_n = 0
        for t in existing_titles:
            if not t or not t.startswith(prefix):
                continue
            suffix = t[len(prefix):]
            if suffix.isdigit():
                max_n = max(max_n, int(suffix))
        return max_n + 1

    def preview_auto_groups(self, max_size: int, use_existing: bool = False) -> List[Dict]:
        """Розрахувати склад нових екзаменаційних груп без збереження.

        Правила (DK-24, оновлено DK-48):
        * Беремо абітурієнтів активної кампанії (за `created_at`), ще не у групі.
        * У абітурієнта має бути хоча б одна спеціальність — інакше він пропускається
          (DK-48). Бакет = спеціальність найвищого пріоритету + база вступу особи +
          форма навчання цієї спеціальності.
        * Назва: `<TAG>-<YY><тег>-<N>` (див. `_bucket_prefix`).
        * Якщо `use_existing=True` — спершу дозаповнюємо наявні групи, чий бакет
          визначено ВИКЛЮЧНО за назвою (DK-48), до `max_size`; решту розкидаємо по нових.

        Повертає список словників:
        ``{"id": int, "title": str, "spec_code": str, "spec_dept": int, "spec_label": str,
           "existing_count": int, "entrants": List[{"id": int, "pib": str, "spec_label": str}]}``.
        """
        if max_size < 1:
            raise ValueError("Максимальний розмір групи має бути не менше 1")

        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None:
            raise RuntimeError("Немає активної вступної кампанії")
        yy = self._year_suffix(campaign)
        active_range = AdmissionCampaignService().get_active_range()

        with rx.session() as session:
            # Кандидати: абітурієнти кампанії, не в групі.
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

            # Бакет = (пріоритетна спеціальність, база вступу особи, форма навчання).
            # Абітурієнтів без жодної спеціальності пропускаємо (DK-48).
            by_spec: Dict[Tuple[int, int, int], Dict] = {}
            for e in candidates:
                top = self._top_specialty(e)
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

            # Усі не видалені групи — для продовження нумерації та дозаповнення.
            all_groups = list(
                session.exec(select(EntrantGroupModel).where(EntrantGroupModel.is_deleted == False)).all()
            )
            existing_titles = {g.title for g in all_groups if g.title}
            # Живі лічильники членів наявних груп — оновлюються при дозаповненні,
            # щоб бакети зі спільним префіксом не переповнили ту саму групу (DK-48).
            live_counts: Dict[int, int] = (
                dict(EntrantsGroupDao.get_entrant_counts([g.id for g in all_groups], session))
                if use_existing else {}
            )

            def _entrant_dict(e: EntrantModel, spec_label: str) -> Dict:
                return {
                    "id": e.id,
                    "pib": (e.person.pib if e.person and e.person.pib else f"#{e.id}"),
                    "spec_label": spec_label,
                }

            result: List[Dict] = []
            for bucket in by_spec.values():
                spec: SpecialityModel = bucket["spec"]
                base = bucket["base"]
                form = bucket["form"]
                ents: List[EntrantModel] = bucket["entrants"]
                # Стабільний порядок: за ПІБ.
                ents.sort(key=lambda e: (e.person.pib if e.person and e.person.pib else "").lower())
                spec_label = f"{spec.code} {spec.title} ({spec.tag}) · {base.title} · {form.title}"
                prefix = self._bucket_prefix(spec, base, form, yy)

                remaining = list(ents)

                # Крок 1 (DK-42/DK-48): дозаповнюємо наявні групи (за назвою) до max_size.
                if use_existing:
                    for gid, gtitle, gcount in self._match_existing_groups(prefix, all_groups, live_counts):
                        free = max_size - gcount
                        if free <= 0 or not remaining:
                            continue
                        take = remaining[:free]
                        remaining = remaining[free:]
                        live_counts[gid] = gcount + len(take)
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

                n = self._next_number(prefix, existing_titles)
                for chunk in chunks:
                    title = f"{prefix}{n}"
                    n += 1
                    # Реєструємо ім'я, щоб подальші бакети/виклики не повторили його.
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

    def suggest_group_for_entrant(
        self, top_spec_id: int, base_id: int, form_id: int, max_size: int
    ) -> Dict:
        """Підбір екзаменаційної групи для одного абітурієнта (DK-48).

        Той самий процес, що й при автоформуванні, але для однієї людини та з
        урахуванням наявних груп. Спершу шукаємо наявну (не видалену) групу
        відповідного бакета (визначеного за назвою) з вільним місцем (< `max_size`);
        якщо такої немає — пропонуємо назву нової групи за тими самими правилами.
        Групу в БД тут НЕ створюємо — це робиться при збереженні картки абітурієнта.

        Повертає:
          ``{"status": "existing", "group_id": int, "title": str}``
          ``{"status": "new", "group_id": 0, "title": str}``
          ``{"status": "error", "message": str}``
        """
        if max_size < 1:
            return {"status": "error", "message": "Некоректний ліміт розміру групи"}
        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None:
            return {"status": "error", "message": "Немає активної вступної кампанії"}
        yy = self._year_suffix(campaign)
        try:
            with rx.session() as session:
                spec = session.get(SpecialityModel, top_spec_id)
                base = session.get(EntryBaseModel, base_id)
                form = session.get(FormOfStudyModel, form_id)
                if spec is None or base is None or form is None:
                    return {
                        "status": "error",
                        "message": "Не вдалося визначити спеціальність, базу вступу або форму навчання",
                    }
                prefix = self._bucket_prefix(spec, base, form, yy)
                all_groups = list(
                    session.exec(
                        select(EntrantGroupModel).where(EntrantGroupModel.is_deleted == False)
                    ).all()
                )
                counts = EntrantsGroupDao.get_entrant_counts([g.id for g in all_groups], session)
                for gid, gtitle, gcount in self._match_existing_groups(prefix, all_groups, counts):
                    if gcount < max_size:
                        return {"status": "existing", "group_id": gid, "title": gtitle}
                existing_titles = {g.title for g in all_groups if g.title}
                n = self._next_number(prefix, existing_titles)
                return {"status": "new", "group_id": 0, "title": f"{prefix}{n}"}
        except Exception as e:
            print(f"[EntrantsGroupService][suggest_group_for_entrant][ERROR] {e}")
            return {"status": "error", "message": "Під час підбору групи сталася помилка"}

    def suggest_entrants_for_group(
        self, group_id: int, exclude_ids: Optional[Sequence[int]] = None
    ) -> List[EntrantModel]:
        """Вільні абітурієнти активної кампанії, які «пасують» групі за її назвою (DK-48).

        Спеціальність/базу/форму, під які створена група, визначаємо НЕ зворотним
        розбором назви (він неоднозначний — тег бази й тег форми зливаються в один
        сегмент), а симетрично до автоформування: для кожного вільного кандидата
        рахуємо його бакет-префікс (`_bucket_prefix` за спеціальністю найвищого
        пріоритету + базою особи + формою) і беремо тих, чий префікс збігається з
        назвою групи (`<prefix><N>`). Тобто саме тих, кого автоформування помістило б
        у групу з такою назвою. Порядок — за ПІБ. Ліміт розміру тут НЕ застосовуємо —
        це робить викликаюча сторона (знає поточний склад форми).
        """
        campaign = AdmissionCampaignService().get_active_campaign()
        if campaign is None:
            return []
        yy = self._year_suffix(campaign)
        exclude = set(exclude_ids or [])
        active_range = AdmissionCampaignService().get_active_range()
        with rx.session() as session:
            group = session.get(EntrantGroupModel, group_id)
            if group is None or not group.title:
                return []
            title = group.title

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

            def _is_free(e: EntrantModel) -> bool:
                if e.id_entrant_group is None:
                    return True
                return bool(e.entrant_group and e.entrant_group.is_deleted)

            result: List[EntrantModel] = []
            for e in entrants:
                if e.id in exclude or not _is_free(e):
                    continue
                top = self._top_specialty(e)
                if top is None or top.speciality is None or top.form_of_study is None:
                    continue
                if e.person is None or e.person.entry_base is None:
                    continue
                prefix = self._bucket_prefix(top.speciality, e.person.entry_base, top.form_of_study, yy)
                if title.startswith(prefix) and title[len(prefix):].isdigit():
                    result.append(e)
            result.sort(key=lambda e: (e.person.pib if e.person and e.person.pib else "").lower())
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

    def bulk_create_with_entrants(self, groups: List[Dict], actor_id: Optional[int] = None) -> int:
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
                    entrants = g.get("entrants", [])
                    ids = [e["id"] for e in entrants]
                    added_pibs = sorted(e.get("pib", f"#{e['id']}") for e in entrants)
                    existing_id = g.get("id") or 0
                    if existing_id:
                        # Дозаповнення наявної групи — тільки дописуємо нових.
                        if ids:
                            EntrantsGroupDao.append_entrants(existing_id, ids, session)
                            record_action(session, actor_id, existing_id, GroupMembersChanged(added=added_pibs))
                    else:
                        group = EntrantGroupModel(title=g["title"])
                        session.add(group)
                        session.flush()
                        if ids:
                            EntrantsGroupDao.replace_entrants(group.id, ids, session)
                        record_action(session, actor_id, group.id, GroupCreated(title=group.title))
                        if ids:
                            record_action(session, actor_id, group.id, GroupMembersChanged(added=added_pibs))
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

    @staticmethod
    def _resolve_speciality_by_group_tag(group_title: str, session) -> Tuple[str, str, bool]:
        """Визначає спеціальність/ОПП відомості за тегом у назві групи (DK-66),
        а не за пріоритетними спеціальностями абітурієнтів (ті можуть відрізнятись
        від того, під яку спеціальність фактично сформована група).

        Тег — початковий сегмент назви групи (`<TAG>-<YY><тег>-<N>`, `_bucket_prefix`).
        Матчимо префіксом (`group_title.startswith(f"{spec.tag}-")`), а не парсингом
        по першому дефісу — тег сам може містити дефіс. Якщо збігів немає або
        збігів декілька (тег не унікальний) — визначити однозначно неможливо,
        поля лишаються порожніми (`specialty_unknown=True`), відомість підсвічує
        їх жовтим, щоб оператор заповнив вручну."""
        candidates = [
            s for s in SpecialityDao.get_all(session)
            if group_title.startswith(f"{s.tag}-")
        ]
        if len(candidates) == 1:
            spec = candidates[0]
            specialty = f"{spec.code} {spec.title} ({spec.tag})"
            opp = spec.educational_and_professional_program or ""
            return specialty, opp, False
        return "", "", True

    def get_exam_sheet_payload(self, group_id: int) -> Dict:
        """Збирає дані для екзаменаційних відомостей по групі (DK-29).

        Повертає `{group_title, specialty, opp, specialty_unknown, subject,
        applicants}`, де applicants — список `{name, phone, relatives}`.
        specialty/opp визначаються за тегом назви групи (DK-66, див.
        `_resolve_speciality_by_group_tag`), subject — з предметів запланованих
        іспитів групи. Один запит за абітурієнтами (з особою, родичами) і один —
        за іспитами.
        """
        try:
            with rx.session() as session:
                group = session.get(EntrantGroupModel, group_id)
                if group is None:
                    raise ValueError(f"Групу #{group_id} не знайдено")

                specialty, opp, specialty_unknown = self._resolve_speciality_by_group_tag(
                    group.title or "", session,
                )

                entrants = list(session.exec(
                    select(EntrantModel)
                    .options(
                        selectinload(EntrantModel.person)
                        .selectinload(PersonModel.information_about_relatives)
                        .selectinload(InformationAboutRelativesModel.kinship),
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

                applicants.sort(key=lambda a: a["name"].lower())
                return {
                    "group_title": group.title or f"#{group_id}",
                    "specialty": specialty,
                    "opp": opp,
                    "specialty_unknown": specialty_unknown,
                    "subject": subject,
                    "applicants": applicants,
                }
        except Exception as e:
            print(f"[EntrantsGroupService][get_exam_sheet_payload][ERROR] {e}")
            raise
