# CLAUDE.md

Справочник по проекту для Claude Code (claude.ai/code).

## Стек

- **Python 3.13.12** (зафиксирован в `pyproject.toml`, `.python-version`)
- **Менеджер окружения и пакетов: uv.** Любые команды и установки идут через `uv` (`uv run ...`, `uv add ...`, `uv sync`). Никаких `pip`/`venv` напрямую.
- **Фреймворк: Reflex 0.8.28.post1** — полностековый Python: модели, состояние и UI описаны в Python.
- **ORM:** SQLModel поверх SQLAlchemy. БД — SQLite (`reflex.db`, конфиг в `rxconfig.py`).
- **Стили:** Tailwind v4 (плагин Reflex). Дизайн-токены берутся из темы `rx.theme(accent_color="brown")`.
- **Миграции:** Alembic (папка `alembic/`).

## Команды

```bash
uv run reflex run       # dev-сервер
uv run pyright          # тайпчек
uv run python deploy.py # первичный деплой: синхронизация Actions + создание admin/admin
uv run python update.py # синхронизация enum Actions в БД после добавления новых
```

## Архитектура: 4 слоя на каждую сущность

| Слой | Расположение | Ответственность |
|------|--------------|-----------------|
| Model | `Dekanat/models.py` | `SQLModel`-классы, декорированные `@rx.ModelRegistry.register`. Все модели лежат в одном файле. |
| DAO | `Dekanat/dao/<entity>.py` | Класс `<Entity>Dao` со static-методами. Принимают `session: Session`, возвращают модели/коллекции. Никаких commit. |
| Service | `Dekanat/services/<entity>.py` | Класс `<Entity>Service`. Открывает `with rx.session()`, дергает DAO, делает `commit`/`refresh`. Ловит исключения, логирует, **пробрасывает дальше** (`raise`). |
| State | `Dekanat/states/<entity>.py` | `rx.State`-наследники от `AppState`. Хранят UI-состояние, проверяют права, вызывают Service. |
| View | `Dekanat/views/<entity>.py` | Чистые компоненты Reflex. Страницы — функции `list_page/add_page/edit_page/view_page`, декорированные `@require_login`. |

Страницы регистрируются в `Dekanat/Dekanat.py` через `app.add_page(...)` с `on_load=...State.on_load`.

### Соглашения по именам

- **DAO:** `KinshipDao`, методы `get_all`, `get_by_id(id, session, with_del=False)`, `add_one`, `edit_one`.
- **Service:** `KinshipService`, методы `get_list_items`, `get_by_id`, `add_one`, `edit_one`, `delete_one`. Внутри — `try/except` с `print(f"[KinshipService][method][ERROR] {e}")` и `raise`.
- **State:** четыре класса на сущность — `List<E>State`, `Add<E>State`, `Edit<E>State`, `View<E>State`. Все наследуют `AppState`.
- **View:** `list_page_content`, `view_page_content`, `add_page_content`, `edit_page_content` + 4 публичные страницы.
- **Routes:** константы в `Dekanat/routes.py`. Пары `<E>_LIST/_ADD/_EDIT/_VIEW`. Для edit/view URL заканчивается на `/` — id подклеивается параметром `[id]` в `app.add_page`.
- **Actions (StrEnum):** `Dekanat/actions.py`. Значение — код `entity:operation` (`worker:list`, `kinship:add`). У каждого пункта есть атрибуты `title_attr`, `description_attr` (украинский язык). После добавления новых пунктов запускать `uv run python update.py`.

### Soft delete

Все удаляемые модели имеют поле `is_deleted: bool = False`. `delete_one` в сервисе ставит `is_deleted = True` и вызывает `edit_one` — записи **не удаляются физически**. DAO-методы фильтруют по `is_deleted == False`, если не передан `with_del=True`.

## Auth и права

- **`AppState`** (`Dekanat/states/app.py`) — базовый класс всех protected-стейтов. Хранит `worker`, `actions_worker`, cookie `auth_token`.
- **Cookie** `auth_token` (`max_age=86400`, SameSite=Lax) → `AuthTokenModel` → `WorkerModel`.
- **`@require_login`** (`Dekanat/views/auth.py`) — обёртка над компонентом страницы. Рендерит спиннер с `on_mount=AppState.require_auth`, который валидирует токен; при невалидном — редирект на `/login`.
- **`AppState.has_permission(action: Actions) -> bool`** — проверяет, есть ли у пользователя право (через прямое назначение в `WorkersActionsModel` или через роль в `WorkersRolesModel`).
- **Где проверять права:**
  - В **начале каждого `on_load`** state'а: при отсутствии — `yield rx.toast.error(...)` + `yield rx.redirect(routes.DASHBOARD)` + `return`.
  - В **каждом мутирующем event-обработчике** (`on_save`, `on_click_delete`, `on_click_edit`): при отсутствии — `yield rx.toast.error(...)` + `return`.
  - В **UI** для скрытия кнопок: `rx.cond(SomeState.get_user_actions.contains(Actions.X), ...)`.

## Добавление новой сущности — чек-лист

1. Модель в `Dekanat/models.py` (`@rx.ModelRegistry.register`).
2. Константы прав в `Dekanat/actions.py` (`<E>_LIST/ADD/EDIT/DELETE/VIEW`) — значение в формате `entity:operation`.
3. Маршруты в `Dekanat/routes.py`.
4. DAO в `Dekanat/dao/<entity>.py`.
5. Service в `Dekanat/services/<entity>.py`.
6. State'ы в `Dekanat/states/<entity>.py` (4 класса, наследуют `AppState`).
7. View в `Dekanat/views/<entity>.py` (4 страницы, декорированы `@require_login`).
8. Регистрация страниц в `Dekanat/Dekanat.py` (`app.add_page` + `on_load=...State.on_load`, для edit/view добавляется `+"[id]"`).
9. Если сущность нужна в сайдбаре — добавить пункт в `Dekanat/declared/submenu.py` (`MAIN` — единственный реально используемый список).
10. **`uv run python update.py`** — синхронизировать новые `Actions` в БД.

### Тонкости из практики

- **Reflex запрещает path-param, имя которого совпадает с `@rx.var` ЛЮБОГО State в проекте** (`DynamicRouteArgShadowsStateVarError`). Конфликты глобальные, не локальные. Имена `code`, `id` уже зарезервированы существующими маршрутами — используй уникальные (`spec_code`, `dept_id`, и т.п.) и/или переименовывай computed var (например, `entity_code`).
- **Composite PK** требует двух path-параметров (`route+"[a]/[b]"`), DAO-метода `get_by_pk(a, b, session)` и read-only обоих ключей при редактировании.
- **Свежесозданная `Model()` без аргументов оставляет required-поля как None.** Все `@rx.var def x -> str` должны защищаться: `return self.item.x if self.item is not None and self.item.x is not None else ""`. Иначе в логах появится `Computed var ... must return value of type str, got None`.
- **FK-поля редактируются через `rx.select`** (см. `views/speciality.py`). В state хранится computed var-обёртка `..._str: str` для значения select и event `set_*`, парсящий int. Список опций готовится в `on_load` через сервис связанной сущности (например, `DepartmentService.get_list_items()`).

### Дочерние коллекции — диалоги + "replace_all" при сохранении

Для сущностей, у которых есть набор дочерних записей, редактируемых не отдельной CRUD-страницей, а прямо на форме родителя (Entrant, AdmissionCampaign), сложилась устойчивая связка:

1. **State.** Каждая коллекция — `List[ChildModel] = []` в state. На каждую — отдельный набор полей диалога: `<x>_open: bool`, `<x>_index: int = -1` (≥0 — редактирование существующего элемента), плюс зеркальные поля диалога (например, `q_budget_places: int`). Обработчики: `open_<x>_add` / `open_<x>_edit(idx)` / `close_<x>` / `set_<x>_open(value)` / `save_<x>` / `delete_<x>(idx)`. См. `EntrantFormState` (`states/entrant.py`) и `_CampaignFormBase` (`states/admission_campaign.py`).
2. **View.** Диалог — `rx.dialog.root` с `open=...<x>_open` и `on_open_change=...set_<x>_open`. Таблица собственных записей — `rx.foreach(form_state.<collection>, _row_factory(form_state))`. Кнопка «+» рядом с заголовком таблицы; в строке — кнопки edit и `controls.delete_with_confirm`. Поля FK, доступные только при добавлении, оборачивайте в `rx.cond(form_state.<x>_index >= 0, _disabled_input, _select)` — иначе при редактировании юзер сможет случайно перевыбрать ключ.
3. **Подписи в строках через словарь.** Поскольку добавленные в памяти модели не имеют подгруженного relationship, имя FK-сущности рендерится через computed-var-словарь (`speciality_labels`, `item_zno_titles` и т.п.), построенный из dropdown-опций. Доступ — `<labels>[item.fk_a + "|" + item.fk_b.to_string()]`.
4. **Persistence.** Дочерние коллекции сохраняются вместе с родителем единым транзакционным «replace_all»: сервис очищает все старые записи по `id_parent` и вставляет переданный список заново. Эталоны — `EntrantService.edit_one(..., specialties=, results_zno=, ...)` и `AdmissionCampaignSpecialityService.replace_all_for_campaign(id, items)`. Не пытайтесь делать diff — это лишняя сложность; полный список из state всегда канонический.

## Доменна структура

Система веде облік **абітурієнтів** та **студентів** ВНЗ, навчального процесу і документообігу.
Центральна сутність БД — **`PersonModel` (особа)**: абітурієнт і студент — це Person + додаткові поля.

### Карта сутностей і статус реалізації

#### Повний CRUD (Model + DAO + Service + State + View + Actions + sidebar)

| Сутність | Модель | Маршрут | Призначення |
|----------|--------|---------|-------------|
| Worker | `WorkerModel` | `/admin/workers` | Користувачі системи (логін, пароль, ролі) |
| Role | `RoleModel` | `/admin/roles` | Ролі для RBAC |
| Identity document type | `IdentityDocumentTypeModel` | `/base/identity_document_type` | Типи документів |
| Kinship | `KinshipModel` | `/base/kinship` | Типи родинних зв'язків |
| Special condition | `SpecialConditionModel` | `/base/special_condition` | Спеціальні умови вступу |
| Source of funding | `SourceOfFundingModel` | `/base/source_of_funding` | Джерела фінансування |
| Entry base | `EntryBaseModel` | `/base/entry_base` | Бази вступу |
| Department | `DepartmentModel` | `/base/department` | Відділення |
| Speciality | `SpecialityModel` | `/base/speciality` | Спеціальності (composite PK `(code, id_department)`) |
| Application status | `ApplicationStatusModel` | `/base/application_status` | Статуси заявок |
| Item ZNO | `ItemZnoModel` | `/base/item_zno` | Предмети ЗНО |
| Entrants group | `EntrantGroupModel` | `/admission_commission/entrants_group` | Групи абітурієнтів на ЗНО (+ `EntrantExamModel` як підсутність у формі) |
| Admission campaign | `AdmissionCampaignModel` | `/admission_commission/campaign` | Вступна кампанія: назва, період + квоти по спеціальностям (`AdmissionCampaignSpecialityModel`) |
| Entrant | `EntrantModel` | `/contingent/entrants` | Абітурієнт = `PersonModel` + статус заявки + комент + усі дочірні сутності особи, керовані діалогами на одній формі |

#### Підсутності, що редагуються діалогами всередині батьківської форми

Не мають окремих сторінок — створюються/змінюються в модальних вікнах на формі батька і зберігаються разом із ним:

- На формі **Entrant** (`views/entrant.py`, `states/entrant.py:EntrantFormState`):
  `IdentityDocumentModel`, `DocumentAboutEducationModel`, `MilitaryAccountingModel`,
  `MedicalReferenceModel`, `InformationAboutRelativesModel`, `SpecialConditionPersonModel`,
  `SpecialtieEntrantModel` (пріоритетний список), `ResultZnoModel`.
- На формі **Admission campaign** (`views/admission_campaign.py`,
  `states/admission_campaign.py:_CampaignFormBase`): `AdmissionCampaignSpecialityModel`
  (квоти бюджет/контракт по спеціальностям).

#### За ER-схемою заплановані, моделей ще немає

- **students** — Студенти (Person + group)
- **groups** — Навчальні групи (`title`, FK speciality, FK curator)
- **curators** — Куратори (Worker з прив'язкою до групи)
- **subjects** + **subjects_workers** — Навчальні предмети + викладачі (M2M)
- **schedule** + **lessons** — Розклад і заняття
- **orders** + **type_orders** — Накази та їх типи (signed/requires_approval/approved)

> **Примітка про ER-схему.** Реалізовані моделі є нормативом. Якщо ER-схема десь розходиться з кодом (наприклад, `specialties.PK = code` на схемі vs composite `(code, id_department)` у моделі; `entrants.application_status` як вільне поле vs FK на `ApplicationStatusModel`; `mokpp`, `place_of_registration_city`, `departments` тощо) — схема перемальовується під код, а не навпаки.

### Логічні блоки і ключові зв'язки

1. **Особа і її документи**: `person ← identity_document, document_about_education, military_accounting, medical_reference, information_about_relatives, special_conditions_person, results_zno`
2. **Абітурієнти**: `entrants (id_person → person, id_entrant_group?) → specialties_entrant (priority list)`; `entrants_groups → entrants_exams (date_time, item_zno)`
3. **Вступна кампанія**: `admission_campaigns ← admission_campaigns_specialties (speciality, budget_places, contract_places)` — задає перелік спеціальностей, доступних абітурієнту при подачі пріоритетів у межах поточної кампанії.
4. **Студенти і навчання**: `students (id_person → person, id_group) → groups (id_specialties, id_curator) → specialties`
5. **Викладання**: `subjects (id_specialties) ↔ workers (через subjects_workers)`; `schedule (group, period) → lessons (subject, worker, schedule)`
6. **Документообіг**: `orders (id_type → type_orders, id_worker → workers)`

### Угода: FK на `SpecialityModel` — завжди composite

`SpecialityModel` має composite PK `(code, id_department)`. Будь-яка таблиця, що посилається на спеціальність, повинна мати **два FK-стовпці** (`id_speciality_code`, `id_speciality_department`) і `ForeignKeyConstraint` через `__table_args__` — single FK на `code` логічно зламаний. Приклади — `SpecialtieEntrantModel`, `AdmissionCampaignSpecialityModel` (`models.py`). Для майбутніх `groups`, `subjects` тощо діє те саме правило.

### Активна вступна кампанія

`AdmissionCampaignService` надає два хелпери для бізнес-логіки, що мусить обмежуватись поточною кампанією:

- `get_active_campaign()` — повертає не видалену кампанію, чий діапазон `[start_date, end_date]` містить сьогоднішню дату (якщо їх декілька — найновіша за `start_date`).
- `get_active_range()` — та сама кампанія у вигляді пари `datetime` (00:00 початку та 23:59:59 кінця) — зручно для фільтрації за `created_at`.

Використовується, зокрема:

- У фільтрі списку абітурієнтів (`ListEntrantState`) — за замовчуванням показує лише абітурієнтів, створених у межах активної кампанії.
- У формі абітурієнта (`EntrantFormState._load_dropdowns`) — список спеціальностей у діалозі пріоритету обмежується тими, що входять до квот активної кампанії. Повний довідник зберігається у `all_speciality_options` і використовується в `speciality_labels`, щоб уже збережені пріоритети завжди мали підпис.

## Локализация UI

**Весь пользовательский текст — украинский.** Это касается:
- заголовков страниц и кнопок,
- toast-сообщений (`rx.toast.error("Під час виконання запиту трапилась помилка...")`),
- значений `title_attr`/`description_attr` в `Actions`,
- лейблов в `submenu.py`.

Технические/диагностические сообщения (`print`-логи ошибок) — на английском.

## Стилистика UI

### Цвета и градиенты
- Акцент темы — `brown` (см. `Dekanat/Dekanat.py`, `rx.theme`).
- Фирменный градиент акцента используется в шапке, сайдбаре, primary-кнопках и подчёркивании заголовков:
  ```python
  f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)"
  ```
- Тень панелей: `inset 0 0 0 0.1rem rgba(255,255,255,0.4), 0.2rem 0.2rem 0.4rem 0 rgba(0,0,0,0.25)`.

### Каркас страницы
- **Persistent layout** (шапка + сайдбар) подключается через `app.extra_app_wraps` в `Dekanat/Dekanat.py` — `app_shell_wrap` и `content_area_wrap`. Они **не пересоздаются при навигации**.
- Тело страницы оборачивается в `page_wrapper(page_header, page_content)` из `Dekanat/views/templates/layouts.py`.
- Заголовок подстраницы — `header_subpage("Назва", *action_buttons)`. Это `hstack` с градиентным текстом и градиентным подчёркиванием снизу.

### Кнопки и контролы (`Dekanat/views/templates/controls.py`)
- `controls.button_primary(...)` — заполненная градиентом, белый текст.
- `controls.button_secondary(...)` — `variant="outline"`.
- `controls.button_image_primary(name_icon=..., on_click=...)` — иконочная primary 2×2rem.
- `controls.button_image_secondary(name_icon=..., on_click=...)` — иконочная secondary.
- `controls.button_back(href)` — secondary-иконка `arrow_left`, делает `rx.redirect(href)`.
- `controls.delete_with_confirm(on_confirm=..., title=..., description=..., trigger=...)` — `rx.alert_dialog` с trigger-иконкой `trash_2`; `on_confirm` вызывается только после подтверждения. Используйте для всех необратимых действий.
- `controls.empty_placeholder(message="Записи відсутні")` — пунктирная карточка-заглушка для пустых таблиц/списков.
- `controls.button_filter_toggle(is_open, on_click)` + `controls.filter_panel(is_open, *fields, on_clear=...)` — пара для анимированной панели фильтров над таблицей списка (пример — `views/entrant.py`).

### Стандартные иконки действий
- Добавить: `plus`
- Сохранить: `save`
- Отмена: `circle_x`
- Редактировать: `pencil_line`
- Удалить: `trash_2`

### Skeleton при загрузке
Для list/view/edit-страниц контент оборачивается в `rx.skeleton(..., loading=SomeState.in_progress, height="100%")` — у state'а должен быть флаг `in_progress`/`in_process` (текущие имена варьируются).

## Логирование ошибок

В сервисах и `AppState` принят паттерн:

```python
try:
    ...
except Exception as e:
    print(f"[<ClassName>][<method>][ERROR] {e}")
    raise   # в сервисах
    # или return False / fallback — в зависимости от контекста
```

Тег `[Class][method][ERROR]` помогает грепать логи.

## Прочее

- Все `Optional[List[...]]` отношения в `models.py` намеренно — Reflex/SQLModel требует именно так для lazy-loading.
- Сессия БД открывается только в сервисах через `with rx.session():`. В DAO `Session` передаётся аргументом — DAO **не управляет** транзакцией.
- В `submenu.py` структура сайдбара декларативная: `MenuItem(label, icon, url, children=[...], required_action=Actions.X)`. Группа автоматически скрывается, если ни одно её дитя не доступно пользователю (см. `_menu_visibility` в `layouts.py`).
