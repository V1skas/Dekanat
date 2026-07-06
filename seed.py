"""Заполняет БД тестовыми данными для проверки рейтинга (DK-18).

Запуск: uv run python seed.py

Идемпотентность: для справочников использует get-or-create по уникальному полю;
абитуриентов добавляет каждый запуск (по `edbo` — сначала проверяет дубль).
"""
import random
from datetime import datetime, timedelta

import reflex as rx
from sqlmodel import select

from Dekanat.models import (
    DepartmentModel,
    SpecialityModel,
    AdmissionCampaignModel,
    AdmissionCampaignSpecialityModel,
    ItemZnoModel,
    SourceOfFundingModel,
    EntryBaseModel,
    FormOfStudyModel,
    ApplicationStatusModel,
    IdentityDocumentTypeModel,
    KinshipModel,
    SpecialConditionModel,
    SpecialConditionPersonModel,
    PersonModel,
    EntrantModel,
    SpecialtieEntrantModel,
    ResultZnoModel,
)


random.seed(42)


UK_FIRST_NAMES_M = [
    "Олександр", "Іван", "Дмитро", "Андрій", "Сергій", "Богдан", "Юрій", "Володимир",
    "Михайло", "Артем", "Назар", "Максим", "Олег", "Роман", "Тарас",
]
UK_FIRST_NAMES_F = [
    "Олена", "Марія", "Анна", "Софія", "Катерина", "Юлія", "Наталія", "Оксана",
    "Ірина", "Вікторія", "Дарія", "Аліна", "Поліна", "Тетяна", "Христина",
]
UK_PATRONYMICS_M = ["Олександрович", "Іванович", "Петрович", "Сергійович", "Андрійович", "Миколайович"]
UK_PATRONYMICS_F = ["Олександрівна", "Іванівна", "Петрівна", "Сергіївна", "Андріївна", "Миколаївна"]
UK_LAST_NAMES = [
    "Коваленко", "Шевченко", "Бондаренко", "Ткаченко", "Кравченко", "Олійник",
    "Бойко", "Іваненко", "Мельник", "Поліщук", "Лисенко", "Гончаренко",
    "Савченко", "Морозенко", "Сидоренко", "Левченко", "Демченко", "Петренко",
    "Захарченко", "Романюк", "Гриценко", "Павленко", "Марченко", "Литвин",
]


def get_or_create(session, model, defaults=None, **kwargs):
    statement = select(model)
    for k, v in kwargs.items():
        statement = statement.where(getattr(model, k) == v)
    existing = session.exec(statement).first()
    if existing is not None:
        return existing, False
    obj = model(**kwargs, **(defaults or {}))
    session.add(obj)
    session.flush()
    return obj, True


def seed_reference_data(session):
    print("→ Довідники")

    departments = []
    dept_titles = [
        "Відділення інформаційних технологій",
        "Економічне відділення",
        "Гуманітарне відділення",
        "Інженерне відділення",
        "Медичне відділення",
    ]
    for t in dept_titles:
        d, _ = get_or_create(session, DepartmentModel, title=t)
        departments.append(d)

    spec_data = [
        ("121", departments[0], "Інженерія програмного забезпечення", "ІПЗ"),
        ("122", departments[0], "Комп'ютерні науки", "КН"),
        ("123", departments[0], "Комп'ютерна інженерія", "КІ"),
        ("051", departments[1], "Економіка", "ЕК"),
        ("071", departments[1], "Облік і оподаткування", "ОО"),
        ("035", departments[2], "Філологія", "ФЛ"),
        ("014", departments[2], "Середня освіта", "СО"),
        ("131", departments[3], "Прикладна механіка", "ПМ"),
        ("223", departments[4], "Медсестринство", "МС"),
    ]
    specialties = []
    for code, dept, title, tag in spec_data:
        s, _ = get_or_create(
            session, SpecialityModel,
            code=code, id_department=dept.id,
            defaults={"title": title, "tag": tag},
        )
        specialties.append(s)

    item_zno_titles = [
        "Українська мова та література", "Математика", "Історія України",
        "Англійська мова", "Біологія", "Фізика", "Хімія", "Географія",
    ]
    item_znos = []
    for t in item_zno_titles:
        # Seed-предмети враховуються у рейтингу, щоб знімок рейтингу мав ненульові
        # бали одразу після сідінгу (DK-47: дефолт False).
        i, _ = get_or_create(
            session, ItemZnoModel, defaults={"is_counted_in_rating": True}, title=t
        )
        item_znos.append(i)

    sof_titles = ["Бюджет", "Контракт", "Цільовий прийом"]
    sources = []
    for t in sof_titles:
        s, _ = get_or_create(session, SourceOfFundingModel, title=t)
        sources.append(s)

    eb_data = [
        ("Повна загальна середня освіта", "ПЗСО"),
        ("Базова середня освіта", "БСО"),
        ("Освітньо-кваліфікаційний рівень", "ОКР"),
    ]
    entry_bases = []
    for t, prefix in eb_data:
        b, _ = get_or_create(session, EntryBaseModel, title=t, defaults={"prefix": prefix})
        entry_bases.append(b)

    fos_data = [("Денна", "Д"), ("Заочна", "З")]
    forms_of_study = []
    for t, prefix in fos_data:
        f, _ = get_or_create(session, FormOfStudyModel, title=t, defaults={"prefix": prefix})
        forms_of_study.append(f)

    # Третій елемент — is_allowed_in_rating (DK-43): чи потрапляє картка в рейтинг.
    # «Відхилена» не допускається — щоб було видно сірі рядки унизу списку.
    status_data = [
        ("Подана", "Заявку подано", True),
        ("Розглядається", "Заявка на розгляді", True),
        ("Прийнята", "Заявку прийнято", True),
        ("Відхилена", "Заявку відхилено", False),
        ("Зарахований", "Абітурієнта зараховано", True),
    ]
    statuses = []
    for t, d, allowed in status_data:
        s, _ = get_or_create(
            session,
            ApplicationStatusModel,
            title=t,
            defaults={"description": d, "is_allowed_in_rating": allowed},
        )
        statuses.append(s)

    idt_titles = ["Паспорт громадянина України", "ID-картка", "Закордонний паспорт", "Свідоцтво про народження"]
    id_types = []
    for t in idt_titles:
        d, _ = get_or_create(session, IdentityDocumentTypeModel, title=t)
        id_types.append(d)

    kinship_titles = ["Батько", "Мати", "Опікун", "Чоловік/Дружина"]
    kinships = []
    for t in kinship_titles:
        k, _ = get_or_create(session, KinshipModel, title=t)
        kinships.append(k)

    sc_data = [
        ("sc_orphan", "Дитина-сирота", True),
        ("sc_disability", "Особа з інвалідністю I-II групи", True),
        ("sc_combatant", "Учасник бойових дій (родина)", True),
        ("sc_low_income", "Малозабезпечена сім'я", False),
        ("sc_large_family", "Багатодітна сім'я", False),
    ]
    special_conditions = []
    for code, title, is_kvota in sc_data:
        sc, _ = get_or_create(
            session, SpecialConditionModel, subcategory_code=code,
            defaults={"title": title, "description": title, "is_kvota": is_kvota},
        )
        special_conditions.append(sc)

    session.flush()
    return {
        "departments": departments,
        "specialties": specialties,
        "item_znos": item_znos,
        "sources": sources,
        "entry_bases": entry_bases,
        "forms_of_study": forms_of_study,
        "statuses": statuses,
        "id_types": id_types,
        "kinships": kinships,
        "special_conditions": special_conditions,
    }


def seed_campaign(session, specialties, entry_bases, forms_of_study):
    print("→ Вступна кампанія + квоти")
    today = datetime.now().date()
    start = today - timedelta(days=30)
    end = today + timedelta(days=60)

    campaign = session.exec(
        select(AdmissionCampaignModel).where(AdmissionCampaignModel.title == "Вступна кампанія 2026")
    ).first()
    if campaign is None:
        campaign = AdmissionCampaignModel(
            title="Вступна кампанія 2026",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
        )
        session.add(campaign)
        session.flush()
    else:
        campaign.start_date = start.isoformat()
        campaign.end_date = end.isoformat()
        session.flush()

    # Очистимо квоти і перестворимо для свіжих чисел
    for old in session.exec(
        select(AdmissionCampaignSpecialityModel).where(
            AdmissionCampaignSpecialityModel.id_admission_campaign == campaign.id
        )
    ).all():
        session.delete(old)
    session.flush()

    # Квоти тепер задаються по кортежу (спеціальність, база вступу, форма навчання).
    # Для повноти тестових даних створюємо квоту на кожну комбінацію (DK-26).
    for s in specialties:
        for base in entry_bases:
            for form in forms_of_study:
                budget = random.randint(5, 12)
                contract = random.randint(8, 18)
                session.add(AdmissionCampaignSpecialityModel(
                    id_admission_campaign=campaign.id,
                    id_speciality=s.id,
                    id_entry_base=base.id,
                    id_form_of_study=form.id,
                    budget_places=budget,
                    contract_places=contract,
                ))
    session.flush()
    return campaign


def _make_pib_and_sex():
    if random.random() < 0.5:
        sex = "Чоловіча"
        pib = f"{random.choice(UK_LAST_NAMES)} {random.choice(UK_FIRST_NAMES_M)} {random.choice(UK_PATRONYMICS_M)}"
    else:
        sex = "Жіноча"
        pib = f"{random.choice(UK_LAST_NAMES)} {random.choice(UK_FIRST_NAMES_F)} {random.choice(UK_PATRONYMICS_F)}"
    return pib, sex


def seed_entrants(session, refs, campaign, count=100):
    print(f"→ Абітурієнти ({count} шт.)")

    specialties = refs["specialties"]
    item_znos = refs["item_znos"]
    sources = refs["sources"]
    entry_bases = refs["entry_bases"]
    forms_of_study = refs["forms_of_study"]
    statuses = refs["statuses"]
    special_conditions = refs["special_conditions"]

    created = 0
    for i in range(count):
        edbo = f"EDBO{1000000 + i:07d}_seed"

        existing = session.exec(select(PersonModel).where(PersonModel.edbo == edbo)).first()
        if existing is not None:
            continue

        pib, sex = _make_pib_and_sex()
        year = random.randint(2004, 2008)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        person = PersonModel(
            edbo=edbo,
            pib=pib,
            citizenship="Україна",
            sex=sex,
            date_of_birth=f"{year}-{month:02d}-{day:02d}",
            place_of_registration_city=random.choice(["Київ", "Львів", "Харків", "Одеса", "Дніпро"]),
            place_of_registration=f"вул. Тестова, буд. {random.randint(1, 200)}",
            mokpp=f"MOKPP{random.randint(10000, 99999)}",
            email=f"entrant{i}@example.com",
            phone_number=f"+38050{random.randint(1000000, 9999999)}",
            the_need_for_a_dormitory=random.random() < 0.3,
            id_source_of_funding=random.choice(sources).id,
            id_entry_base=random.choice(entry_bases).id,
        )
        session.add(person)
        session.flush()

        entrant = EntrantModel(
            id=person.id,
            id_application_status=random.choice(statuses).id,
            comment=None,
        )
        session.add(entrant)
        session.flush()

        # ResultZno: 3-4 предмета, по которым общая сумма формирует рейтинг
        chosen_items = random.sample(item_znos, k=random.randint(3, 4))
        for it in chosen_items:
            session.add(ResultZnoModel(
                id_items_zno=it.id,
                id_person=person.id,
                points=random.randint(100, 200),
            ))

        # Пріоритети — 1-3 спеціальностей з кампанії; кожному пріоритету призначаємо
        # форму навчання (квоти існують для будь-якої комбінації база×форма) (DK-26).
        chosen_specs = random.sample(specialties, k=random.randint(1, 3))
        for priority, sp in enumerate(chosen_specs, start=1):
            session.add(SpecialtieEntrantModel(
                id_entrant=entrant.id,
                id_speciality=sp.id,
                id_form_of_study=random.choice(forms_of_study).id,
                priority=priority,
            ))

        # ~10% — со спец. условием, из них ~70% попадает на квотную категорию
        if random.random() < 0.10:
            sc = random.choice(special_conditions)
            session.add(SpecialConditionPersonModel(
                id_person=person.id,
                id_special_condition=sc.subcategory_code,
                title=sc.title,
                number=f"SC{random.randint(10000, 99999)}",
                description=None,
                date_of_issue=datetime.now().strftime("%Y-%m-%d"),
            ))

        created += 1
        if (created % 25) == 0:
            session.flush()

    session.flush()
    print(f"   створено нових: {created}")


def main():
    print("=== Завантаження тестових даних ===\n")
    with rx.session() as session:
        refs = seed_reference_data(session)
        campaign = seed_campaign(session, refs["specialties"], refs["entry_bases"], refs["forms_of_study"])
        seed_entrants(session, refs, campaign, count=100)
        session.commit()
    print("\n=== Готово ===")


if __name__ == "__main__":
    main()
