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

## Git

**Сообщения коммитов пишем на русском языке** (украинский в описаниях фич/тикетов тоже допустим, но язык коммитов — русский). Заголовок начинается с тикета (`DK-NN <короткое описание>`), тело — кратко по сути изменений; деталями не загромождать.

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

- **`AppState`** (`Dekanat/states/app.py`) — базовый класс всех protected-стейтов. Хранит `worker`, `actions_worker`, `permissions_version_seen`, cookie `auth_token`.
- **Cookie** `auth_token` (`max_age=60*60*24*30`, SameSite=Lax) — длинная, но реальное закрытие сессии контролируется серверным `AuthTokenModel.expires_at` (см. ниже).
- **`@require_login`** (`Dekanat/views/auth.py`) — обёртка над компонентом страницы. Рендерит спиннер с `on_mount=AppState.require_auth`, который валидирует токен; при невалидном/просроченном — редирект на `/login`.
- **`AppState.has_permission(action: Actions) -> bool`** — проверяет, есть ли у пользователя право (через прямое назначение в `WorkersActionsModel` или через роль в `WorkersRolesModel`).
- **Где проверять права:**
  - В **начале каждого `on_load`** state'а: при отсутствии — `yield rx.toast.error(...)` + `yield rx.redirect(routes.DASHBOARD)` + `return`.
  - В **каждом мутирующем event-обработчике** (`on_save`, `on_click_delete`, `on_click_edit`): при отсутствии — `yield rx.toast.error(...)` + `return`.
  - В **UI** для скрытия кнопок: `rx.cond(SomeState.get_user_actions.contains(Actions.X), ...)`.

### Тайм-аут сессии (ковзне вікно)

- `AuthTokenModel` має `expires_at` і `last_activity_at`. При логіні `AuthService.auth()` ставить `expires_at = now + session_timeout_minutes` (з `app_settings`, дефолт — 60 хв).
- `AuthService.get_auth_token(token)` викликається з кожного `require_auth`: видаляє протерміновані токени, перевіряє `expires_at` поточного, а потім **продовжує** його через `AuthTokenDao.touch(...)` (= ковзне вікно). Протерміновані видаляються ліниво тут же та при логіні — окремого крон-скрипта немає.
- Налаштування `session_timeout_minutes` редагується на `/admin/settings` (право `settings:edit`). Зміна застосовується до **нових** токенів і до наступного `touch` існуючих.

### Негайне застосування прав (без релогіну)

- `WorkerModel.permissions_version` — лічильник, що бампиться:
  - у `WorkerService.edit_one` (зміна персональних прав/ролей користувача);
  - у `RoleService.edit_one` для **всіх воркерів**, що мають цю роль (зміна набору прав ролі).
- `AppState.require_auth` після першого завантаження порівнює `worker.permissions_version` з кешем `permissions_version_seen`; при невідповідності перечитує `actions_worker` і оновлює кеш. Тобто наступний перехід сторінок у вже залогіненої сесії побачить нові права.
- Не варто покладатися на `actions_worker.length() == 0` як ознаку «треба перечитати» — після виходу з сесії воркера зі скиданням прав це призведе до циклу запитів. Завжди звіряйтесь з `permissions_version`.

## Добавление новой сущности — чек-лист

1. Модель в `Dekanat/models.py` (`@rx.ModelRegistry.register`).
2. Константы прав в `Dekanat/actions.py` (`<E>_LIST/ADD/EDIT/DELETE/VIEW`) — значение в формате `entity:operation`.
3. Маршруты в `Dekanat/routes.py`.
4. DAO в `Dekanat/dao/<entity>.py`.
5. Service в `Dekanat/services/<entity>.py`.
6. State'ы в `Dekanat/states/<entity>.py` (4 класса, наследуют `AppState`).
7. View в `Dekanat/views/<entity>.py` (4 страницы, декорированы `@require_login`).
8. Регистрация страниц в `Dekanat/Dekanat.py` (`app.add_page` + `on_load=...State.on_load`, для edit/view добавляется `+"[id]"`).
9. Если сущность нужна в сайдбаре — добавить пункт в `Dekanat/declared/submenu.py` (`MAIN` — единственный реально используемый список). Хочешь показать её только на dashboard'е раздела, но не в боковом меню — постав `dashboard_only=True`.
10. **`uv run python update.py`** — синхронизировать новые `Actions` в БД.

### Тонкости из практики

- **Reflex запрещает path-param, имя которого совпадает с `@rx.var` ЛЮБОГО State в проекте** (`DynamicRouteArgShadowsStateVarError`). Конфликты глобальные, не локальные. Имена `code`, `id` уже зарезервированы существующими маршрутами — используй уникальные (`spec_code`, `dept_id`, и т.п.) и/или переименовывай computed var (например, `entity_code`).
- **Composite PK** требует двух path-параметров (`route+"[a]/[b]"`), DAO-метода `get_by_pk(a, b, session)` и read-only обоих ключей при редактировании.
- **Свежесозданная `Model()` без аргументов оставляет required-поля как None.** Все `@rx.var def x -> str` должны защищаться: `return self.item.x if self.item is not None and self.item.x is not None else ""`. Иначе в логах появится `Computed var ... must return value of type str, got None`.
- **FK-поля редактируются через `rx.select`** (см. `views/speciality.py`). В state хранится computed var-обёртка `..._str: str` для значения select и event `set_*`, парсящий int. Список опций готовится в `on_load` через сервис связанной сущности (например, `DepartmentService.get_list_items()`).
- **`rx.select.item` не приймає `value=""`** (Radix кидає `A <Select.Item /> must have a value prop that is not an empty string`). Для пункту «всі / без фільтра» використовуйте sentinel-рядок (наприклад, `"__all__"` у `ListRatingState.selected_spec_key`), а порівняння у логіці робіть з ним же.
- **SQLite: ніяких неявних INSERT'ів на hot path авторизації.** `AuthService.get_auth_token` смикається з кожного `require_auth` і пише в `auth_tokens` (touch/cleanup). Якщо в цей самий момент будь-який інший сервіс відкриє другу сесію з INSERT'ом — отримаєте `database is locked`. Урок із DK-21: `AppSettingService.get_by_key` повинен бути read-only; seed дефолтів — окремий `ensure_defaults()`, який викликається з `deploy.py` та з `on_load` сторінки настройок, але не з гарячих read'ів.
- **`rx.foreach` не можна викликати на атрибуті `rx.Base`-моделі всередині зовнішнього `rx.foreach`** (Reflex: `Cannot pass a Var to a built-in function ... Happened while evaluating page ...`). Замість вкладеного циклу зробіть плоский список з sentinel-полем-заголовком (див. `SettingDraft.section_header` у `states/app_setting.py`) і відображайте заголовок секції через `rx.cond(item.section_header != "", ...)`.
- **Зміна вкладеного поля `rx.Base` всередині списку state може не тригерити реренд.** Reflex реагує надійно на присвоєння списку цілком; точкова мутація `self.drafts[i].value = ...` може лишитися непомітною для UI. Перепризначуйте список новими обʼєктами (зразок — `ListAppSettingState.set_value`).
- **Усі `set_*` оголошуємо явно.** У `rxconfig.py` стоїть `state_auto_setters=False` (інакше Reflex 0.8.9+ кидає deprecation). Сетер — це `@rx.event def set_field(self, value: <type>): self.field = value`; для полів, що приходять у вигляді рядка з браузера (int/bool), пишіть парсинг у тілі (`int(value) if value else 0`, тощо). Перед мерджем зручно перевірити покриття: для кожного `<State>.set_X`, що використовується у `Dekanat/views/`, у `Dekanat/states/` має бути відповідний метод (із врахуванням успадкування).
- **Path-параметри маршрутів — через `AppState._route_param(name, default)`.** Прямий доступ `self.router.page.params.get(...)` зараз депрекейтнутий у Reflex 0.8; новий публічний API ще не дає path-params окремо від query. Helper інкапсулює доступ через `router._page.params`, щоб не плодити приватні виклики по всьому коду.
- **Одна картка, різні точки входу — контекст через `?from` query-параметр (DK-35).** Коли та сама сторінка перегляду/редагування абітурієнта відкривається з двох списків (абітурієнти та «Заявки»), кнопка «назад» має вести туди, звідки прийшли. Рішення: посилання зі списку заявок додає `?from=applications`; `ViewEntrantState`/`EntrantFormState` читають його в `on_load` (`self.router.url.query_parameters.get("from", "")`), computed var `back_route` віддає потрібний маршрут, а `_from_suffix(came_from)` протягує контекст крізь перехід картка → редагування → картка (save/cancel/edit також клеять суфікс). Шапка підсторінки не хардкодить `href`, а бере `left=controls.button_back(ViewEntrantState.back_route)`.
- **`rx.Base` депрекейтнутий — для нових нащадків state-моделей використовуйте `pydantic.BaseModel`** (`from pydantic import BaseModel, Field`). Для `List[Model]`-полів усередині такого класу не забувайте `Field(default_factory=list)`.
- **Computed var `-> str` зобовʼязаний повертати рядок навіть до `on_load`.** `Model()` без аргументів залишає required-поля як `None`, тому захищайтесь повністю: `return self.item.field if self.item is not None and self.item.field is not None else ""`. Часткова перевірка (`if self.item is not None else ""`) ловить лише перший шар і дає у логах `Computed var ... must return a value of type str, got None`.
- **Індексування Python-списку всередині `rx.foreach` не працює.** Якщо потрібно мати палітру/мапу і брати її за `index` (Var), то `MY_PALETTE[index]` кидає `Cannot index into a primitive sequence with a Var`. Загортайте у `rx.Var.create(MY_PALETTE)` — отримана Var підтримує `[index % len(MY_PALETTE)]` як Var-операцію (зразок — `views/admission_campaign_report.py:_pie_cell`).
- **SQLite за замовчуванням сортує кирилицю неправильно.** Стандартне BINARY-collation порівнює побайтно по UTF-8, а літера `І` (U+0406) у Юнікоді стоїть **перед** кириличними А-Я (U+0410+) — тому «Іваненко» опиняється на початку списку. `lower()` теж не знає кирилицю. Рішення — кастомний collation `UA_CI` із `Dekanat/utils/db.py:register_ua_collation()` (реєструється у `Dekanat/Dekanat.py` при старті). У DAO для текстових сортувань пишіть `col.collate("UA_CI")` (зразок — `Dekanat/dao/entrant.py:_apply_sort`). Для латиниці (телефони, email) колацію не потрібно.
- **SQLite `lower()` не опускає кирилицю — це ламає пошук по `LIKE`.** Якщо запит привести до нижнього регістру в Python (`q.lower()`), а в SQL писати `func.lower(col).like(...)`, кириличні великі літери в БД не опускаються і збіг не знаходиться (DK-36: пошук «Захарченко» нічого не давав, «ахарченко» — давав). Collation тут не допомагає: SQLite `LIKE` його не використовує. Рішення — `Dekanat/utils/db.py:ua_lower(col)`: на SQLite це власна функція `ua_lower` (Python `str.lower`, реєструється на connect поряд із `UA_CI`), на MySQL — нативний `lower()`. Для латиниці (телефон) досить звичайного `func.lower`.
- **Важкі синхронні операції в event-обробнику підвішують застосунок для ВСІХ користувачів (DK-41).** Reflex виконує тіло sync-обробника (`def ...`, включно з кодом між `yield`) прямо в єдиному потоці asyncio (`reflex/state.py`: для sync-генераторів робиться `next(events)` в event loop). Тому важкий рендер документів (`docxtpl`/`lxml`, `openpyxl` — `report.render_bytes()`) блокує обробку websocket-подій усіх клієнтів, доки документ не сформується. Рішення — обробник робимо `async def`, а блокуючу частину (читання даних + рендер) виносимо у фоновий потік через `await run_blocking(fn, ...)` з `Dekanat/utils/background.py` (виділений `ThreadPoolExecutor`). Правила офлоуду: `fn` — `@staticmethod`/чиста функція, приймає примітиви (стан знімаємо на event loop **до** виклику), **не мутує стан і не `yield`-ить**, лише повертає готові `(bytes, filename)`; тости/`rx.download`/`self.downloading` лишаються в async-обробнику. Робота у потоці має бути **read-only** по БД (SQLite `check_same_thread=False` дозволяє крос-потокові сесії, але паралельний INSERT дасть `database is locked` — не виносьте у потік запис, напр. `RatingService.generate`). Зразки — `states/rating.py:on_click_download_group/on_click_download_all`, `states/entrants_group.py:on_click_sheet`.

### Дружелюбная к печати страница (reuse session state)

`/admission_commission/entrant_exam/print` — приклад "лёгкого" варианта: окрема сторінка не має власних DAO-запитів, а **переиспользует** `ListEntrantExamState` (Reflex тримає state у межах сесії клієнта — навігація на інший роут не скидає `items_display`/фільтри). Сценарій:

1. У списочному state'і є event `on_click_print → rx.redirect(routes.<...>_PRINT)`.
2. На print-сторінці окремий `PrintEntrantExamState.on_load` робить `yield rx.call_script("setTimeout(() => window.print(), 300)")` — щоб браузер встиг намалювати таблицю.
3. У view використовується контейнер `<div id="print-area">` навколо друкарського контенту, а в `_print_styles()` через `rx.html("<style>@media print { body * { visibility: hidden } #print-area, #print-area * { visibility: visible } ... }</style>")` гасяться шапка/сайдбар/кнопки. Хром застосунку не треба чіпати.

Використовуйте цей патерн, коли треба експорт «список → таблиця для друку» без дублювання запитів. Для повноцінного PDF-експорту/складних шаблонів — будуйте окрему сутність зі своїм state.

**Варіант із вибором набору (`?ids=…`).** У `entrants_group/print` сценарій інший: треба роздрукувати **довільний підмножина** записів — або обрану зі списку чекбоксами, або один зі сторінки перегляду. Тут окремий `PrintEntrantsGroupState` сам тягне дані з сервісу за списком id з query-параметра:

1. `ListEntrantsGroupState` має `select_mode: bool` + `selected_ids: List[int]` + computed `selected_set: List[str]` (для `contains`-перевірки чекбокса у `rx.cond`). Перемикач режиму — окрема іконка `printer` у шапці; у режимі вибору ця кнопка стає `circle_x`-primary, а ліворуч зʼявляється група «виділити все / зняти / підтвердити».
2. У таблиці списку стовпчик-чекбокс рендериться через `rx.cond(...select_mode, rx.table.cell(rx.checkbox(...)), fragment)` — і в `header`, і в кожній `row`. Те саме і для заголовка стовпчика.
3. `on_click_print_confirm` робить `rx.redirect(f"{routes.<...>_PRINT}?ids={','.join(...)}")`. Сторінка перегляду одного запису посилає той самий маршрут, але з одним id.
4. `PrintEntrantsGroupState.on_load` читає `self.router.url.query_parameters.get("ids", "")`, ходить у сервіс за кожним id, заповнює `groups: List[PrintGroup]` (pydantic.BaseModel) і вже потім зве `window.print()`. Кожна група рендериться окремою таблицею; через CSS `.print-group { page-break-after: always }` кожна друкується з нової сторінки.

### Pop-up редактор по списку (carousel-style)

Шаблон «таблиця рядків → діалог з навігацією попередній/наступний» — для масового редагування одного поля. Реалізація в `ViewEntrantExamState` (секція «Оцінювання»):

- `grading_rows: List[Dict[str, str]]` — перерендерені рядки (`id`, `pib`, `grade`).
- Стан діалогу: `g_open`, `g_index` (поточний рядок), `g_grade_input` (буфер вводу), `g_grade_original` (значення до правки — для кнопки «Скинути»).
- Computed: `current_entrant_pib`, `grading_indicator` (`"X / N"`), `has_prev_entrant`, `has_next_entrant` — для заголовка діалога й `disabled` стрілок.
- Events: `open_grading_dialog(index)` / `open_grading_dialog_for(row_id)` — за індексом або за ключем; `prev_entrant`/`next_entrant` — рухати `g_index`, перезавантажуючи буфер; `reset_grade` — `g_grade_input = g_grade_original`; `save_grade` — викликає upsert у БД, оновлює мапу `grades_by_entrant` і перерендерює `grading_rows` (без перечитування групи).
- Persistence — без «replace_all», точковий upsert через окремий сервіс (`ResultZnoService.upsert(...)`), бо ми працюємо з однією парою ключів за раз.

### Дочерние коллекции — диалоги + "replace_all" при сохранении

Для сущностей, у которых есть набор дочерних записей, редактируемых не отдельной CRUD-страницей, а прямо на форме родителя (Entrant, AdmissionCampaign), сложилась устойчивая связка:

1. **State.** Каждая коллекция — `List[ChildModel] = []` в state. На каждую — отдельный набор полей диалога: `<x>_open: bool`, `<x>_index: int = -1` (≥0 — редактирование существующего элемента), плюс зеркальные поля диалога (например, `q_budget_places: int`). Обработчики: `open_<x>_add` / `open_<x>_edit(idx)` / `close_<x>` / `set_<x>_open(value)` / `save_<x>` / `delete_<x>(idx)`. См. `EntrantFormState` (`states/entrant.py`) и `_CampaignFormBase` (`states/admission_campaign.py`).
2. **View.** Диалог — `rx.dialog.root` с `open=...<x>_open` и `on_open_change=...set_<x>_open`. Таблица собственных записей — `rx.foreach(form_state.<collection>, _row_factory(form_state))`. Кнопка «+» рядом с заголовком таблицы; в строке — кнопки edit и `controls.delete_with_confirm`. Поля FK, доступные только при добавлении, оборачивайте в `rx.cond(form_state.<x>_index >= 0, _disabled_input, _select)` — иначе при редактировании юзер сможет случайно перевыбрать ключ.
3. **Подписи в строках через словарь.** Поскольку добавленные в памяти модели не имеют подгруженного relationship, имя FK-сущности рендерится через computed-var-словарь (`speciality_labels`, `item_zno_titles` и т.п.), построенный из dropdown-опций. Доступ — `<labels>[item.fk_a + "|" + item.fk_b.to_string()]`.
4. **Persistence.** Дочерние коллекции сохраняются вместе с родителем единым транзакционным «replace_all»: сервис очищает все старые записи по `id_parent` и вставляет переданный список заново. Эталоны — `EntrantService.edit_one(..., specialties=, results_zno=, ...)` и `AdmissionCampaignSpecialityService.replace_all_for_campaign(id, items)`. Не пытайтесь делать diff — это лишняя сложность; полный список из state всегда канонический.

### Автогенерація з preview-state і bulk-save

Шаблон «згенерувати багато сутностей за один клік, дати поправити руками, зберегти однією транзакцією». Реалізація — `/admission_commission/entrants_group/auto` (`EntrantsGroupService.preview_auto_groups / bulk_create_with_entrants` + `AutoGenerateEntrantsGroupState`).

1. **Сервіс — два методи.** `preview_*(params) -> List[Dict]` рахує наповнення груп **без жодного INSERT**. `bulk_create_with_entrants(payload)` пише все в одній транзакції — приймає вже відредаговану структуру і не дублює бізнес-логіку розрахунку.
2. **State.** Чернеткові групи живуть у `List[GeneratedGroup]` (pydantic.BaseModel із `Field(default_factory=list)`). Кожна `GeneratedGroup` має `entrants: List[GeneratedEntrant]`. Для UI-індикації — `generating: bool` (запуск формування) та `saving: bool` (запис). Перед важкою операцією — `self.generating = True; yield` (без yield на момент стартового рендеру Reflex не покаже спіннер).
3. **Ручне редагування.** Діалог складу групи (`composition_index`, `composition_open`) дозволяє виключати/додавати абітурієнтів. Доступний пул для додавання — окремий `_pool` із сервісу, picker мінусом тих, хто вже потрапив у будь-яку чернеткову групу. **Жодних лімітів розміру** при ручній правці — користувач сам вирішує.
4. **Мутації списку — через перепризначення.** `self.generated_groups[i].entrants.append(...)` Reflex може не побачити; завжди робіть нову `GeneratedGroup` і переписуйте список `self.generated_groups = new_groups` (див. `add_entrant_to_group`).
5. **Збереження** — фільтруємо порожні групи перед відправкою у `bulk_create_with_entrants` (тост «пропущено порожніх: N»). По успіху — `rx.redirect` на список. `on_cancel` просто редиректить, нічого не пише.
6. **Рівномірний розподіл.** Якщо для бакета потрібно більше однієї групи, ділимо `total // n` базово плюс `extras = total % n` додаткових: перші `extras` груп отримують +1, решта — порівну. Реалізація — у `preview_auto_groups`. Дає 25/24/24 замість 30/30/13.
7. **Скидання при заході (DK-42).** `on_load` завжди очищає `generated_groups`/`_pool`/діалоги — інакше після `on_cancel` (який лише редиректить) повторний вхід показав би старий, уже скасований результат. Видалення цілої чернеткової групи — `remove_group(index)` (перепризначення списку), кнопка `trash_2` у рядку таблиці результатів.
8. **Дозаповнення наявних груп (DK-42).** Галочка `use_existing` біля «макс. розмір» вмикає режим, коли перед створенням нових груп абітурієнти дозаповнюють уже наявні (не видалені) групи тієї самої специальності/бази/форми до `max_size`. Бакет наявної групи визначається за її поточними членами (пріоритетна спеціальність + `entry_base` + `form_of_study`), точна кількість — окремим `EntrantsGroupDao.get_entrant_counts` (щоб урахувати й членів поза діапазоном кампанії і не переповнити). Топ-ап-групи повертаються з ненульовим `id` та `existing_count`; у `bulk_create_with_entrants` для них викликається `append_entrants` (дописування без чіпання поточного складу), а не `replace_entrants`. **Порожню, вручну створену групу** (членів нема, бакет за ними не визначити) бакет визначається за її назвою: `preview_auto_groups` спершу рахує бакети кандидатів і їх префікси (`prefix_by_key`), а тоді `_bucket_from_title` мапить назву групи, що відповідає шаблону `<TAG>-<YY><база><форма>-<N>`, на відповідний бакет — так порожня група теж дозаповнюється (DK-42 follow-up). Довільно названі наявні групи (назва не збігається з жодним префіксом кандидатів) не чіпаються. Нумерація нових груп (`_next_number`) завжди зважає на назви всіх наявних груп, включно з порожніми, тож індекси в іменах не колізять — і в режимі дозаповнення, і без нього.

### Звіти-знімки з графіками (recharts)

Шаблон «згенерувати знімок → зберегти JSON → рендерити графіками». Реалізація — `/reporting/admission_campaign` (`AdmissionCampaignReportService` + `ListAdmissionReportState` + `views/admission_campaign_report.py`).

1. **Модель.** Одна таблиця з `id_campaign`, `generated_at`, `payload: str`. Знімок — JSON цілком. Це дозволяє додавати нові секції звіту без міграцій і не змушує користувача перегенерувати при кожному відкритті сторінки.
2. **Сервіс.** `generate(id)` робить один запит, всередині рахує всі зрізи відразу (totals, серії, розподіли) і кладе у JSON. `get_payload(id)` повертає `(dict, generated_at)`. Попередній знімок кампанії видаляється — історія не потрібна.
3. **Структура payload.** Числові — `totals: {today, week, period}`. Серії — `week_series`, `period_series` як `List[{date, count}]`. Розподіли по специальностях — `by_spec_top` і `by_spec_any` як **словник трьох зрізів** `{day: [...], week: [...], period: [...]}`. Це потрібно, щоб глобальний перемикач періоду перемикав pie без перегенерації.
4. **Toggle періоду.** State тримає `selected_period: str` ("day"/"week"/"period") + computed `is_period_*`. У view — таблетка з трьох кнопок: `rx.cond(is_active, button_primary, button_secondary)` на кожній. Активний графік обирається через `rx.match(selected_period, ("day", bar), ("week", line_week), ...)`.
5. **Сумісність зі старими знімками.** Хелпер `_spec_bucket(payload, key)` дивиться, чи `payload[key]` — це `dict` (новий формат) чи `list` (legacy), і в обох випадках віддає список `{name, value}`. Так живі знімки не ламаються при розширенні структури.
6. **Recharts.** `rx.recharts.bar_chart`, `line_chart`, `pie_chart` із дочірніми `bar/line/pie`, `x_axis`, `y_axis`, `cartesian_grid`, `graphing_tooltip`, `legend`. Для порівняння двох кампаній — другий `bar`/`line` із тим самим `data` (поля `primary`/`compare` злиті у state). Для pie — окремий чарт біля основного, накладення секторів нечитабельне.
7. **Palette для pie.** Reflex не дозволяє `_PALETTE[index]` всередині `rx.foreach` (`index` — Var). Загорніть палітру у `rx.Var.create(_PALETTE)` і робіть `palette[index % len(_PALETTE)]` — це валідна Var-операція.
8. **Сравнение кампаний.** `compare_campaign_id: int = 0` (sentinel `__none__` у select). State склеює серії «по порядку днів», а не по конкретних датах — щоб кампанії різних років були сумірні; графік дня — це один-два бари в одному рядку.

### Серверна сортировка списочних таблиць

Шаблон «клік по заголовку столбця → ORDER BY на сервері». Реалізація — `ListEntrantState` + `EntrantDao._apply_sort` (`dao/entrant.py`).

1. **DAO.** `get_all(..., sort_field: Optional[str], sort_dir: str = "asc")`. Хелпер `_apply_sort` бере statement і додає `ORDER BY`; для join'ів на справочники використовує `aliased(...)` + `outerjoin(...)`, щоб не зачепити інші where'и/join'и. Для текстових колонок — `col.collate("UA_CI")` (див. «SQLite не сортує кирилицю»). Дефолт без поля — `created_at.desc()`.
2. **State.** Два поля: `sort_field: str = ""` і `sort_dir: str = "asc"`. Event `on_click_sort(field)` — якщо клік по поточному полю, перемикає `asc ⇄ desc`; інакше ставить нове поле і `asc`. Після зміни — `_reload_items()`. Computed var `sort_indicator: Dict[str, str]` мапить ключ поля у `" ↑"` / `" ↓"` / `""` — для рендеру стрілки поруч із назвою колонки.
3. **View.** Хелпер `_sortable_header(title, field)` рендерить `rx.table.column_header_cell` із hstack-у двох text'ів (`title` + `State.sort_indicator[field]`), `cursor="pointer"`, `on_click=State.on_click_sort(field)`. Hover-підсвітку робимо через `_hover={"background_color": rx.color("accent", 10)}`.

Якщо у таблиці є фільтри по серверу — їх state-поля живуть поряд із сортуванням, всі обробники сетерів закінчуються одним `_reload_items()`, який пробрасує все це у Service.

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
| Application status | `ApplicationStatusModel` | `/base/application_status` | Статуси заявок. `is_default` — статус за замовчуванням для нових карток (DK-36). `is_allowed_in_rating` (bool, дефолт False, DK-43) — чи допускається абітурієнт із цим статусом до рейтингового списку; якщо ні — картка йде у самий низ знімка зі статусом `excluded` (сірий рядок). |
| Item ZNO | `ItemZnoModel` | `/base/item_zno` | Предмети ЗНО. Поле `coefficient` (float, дефолт 1.0) — ваговий коефіцієнт: бал, введений оператором/на тестуванні, домножається на нього при збереженні оцінки (DK-40). |
| Entrants group | `EntrantGroupModel` | `/admission_commission/entrants_group` | Групи абітурієнтів на ЗНО. Список і картка показують кількість абітурієнтів у групі (DK-42). Окремо: `/auto` — автоформування за приоритетной специальностью активної кампанії з рівномірним розподілом (DK-24), з опцією дозаповнення наявних груп і видаленням зайвих чернеткових груп (DK-42); `/print?ids=…` — друк складу обраних груп. Право `entrants_group:auto_generate` гейтить кнопку, доступ на сторінку та сам запуск формування. |
| Entrant exam | `EntrantExamModel` | `/admission_commission/entrant_exam` | Графік іспитів груп: дата, час початку/завершення, опис, M2M відповідальні співробітники (`EntrantExamWorkerModel`). На сторінці перегляду — секція «Оцінювання» з upsert'ом у `ResultZnoModel` |
| Admission campaign | `AdmissionCampaignModel` | `/admission_commission/campaign` | Вступна кампанія: назва, період + квоти по спеціальностям (`AdmissionCampaignSpecialityModel`) |
| Entrant | `EntrantModel` | `/contingent/entrants` | Абітурієнт = `PersonModel` + статус заявки + комент + усі дочірні сутності особи, керовані діалогами на одній формі |
| Заявки абітурієнтів | (окремої моделі немає — читає `SpecialtieEntrantModel`) | `/contingent/applications/list` | Окреме представлення абітурієнтів «за заявками»: один рядок на кожну спеціальність з пріоритетного списку (DK-35). Ті самі колонки, що у списку абітурієнтів, плюс `Пріоритет`. Фільтри — ідентичні списку абітурієнтів (відбирають ті самі картки на рівні абітурієнта); сортування завжди композитне з фіксованим порядком ключів `ПІБ → пріоритет → спеціальність` — клік по заголовку лише перемикає напрямок цього стовпця (asc⇄desc), не змінюючи пріоритет ключів; напрямки стовпців незалежні (`sort_dirs: Dict[str,str]`). Тільки `list` (право `entrant_application:list`) — картку/редагування переиспользуют сторінки абітурієнта з `?from=applications`, щоб «назад» вело у список заявок. Без кнопки додавання. DAO/сервіс — `entrant_application.py`; фільтри спільні з `EntrantDao` через `apply_entrant_filters`. |
| Rating | `RatingSnapshotModel` + `RatingEntryModel` | `/admission_commission/rating/list` | Знімок рейтингового списку для кампанії: дата формування + рядки (спеціальність, абітурієнт, позиція, сума балів, статус місця). Тільки `view` (фільтри по кампанії та спеціальності) і `generate` (кнопка формування) — без CRUD-сторінок. Абітурієнти, чий статус заявки не має `is_allowed_in_rating`, не беруть участі в рейтингу — йдуть у самий низ таблиці зі статусом `excluded` (сірий рядок; трактування є у легенді). Клік по будь-якому рядку веде на картку абітурієнта (DK-43). |
| App settings | `AppSettingModel` | `/admin/settings` | Загальні налаштування системи (key/value/category/value_type). Одна сторінка, секції за `category`: «Авторизація» (`session_timeout_minutes`) та «Рейтинг» (`max_total_points` — верхня межа суми балів при формуванні рейтингу, дефолт 200, DK-40). Дефолтні записи сидяться у `deploy.py` через `AppSettingService.ensure_defaults()`. Права: `settings:view` / `settings:edit`. |
| Admission campaign report | `AdmissionCampaignReportModel` | `/reporting/admission_campaign` | Знімок звіту по приймальній кампанії: totals (день/тиждень/період), серії по дням, розподіл по специальностях (`by_spec_top` priority=1, `by_spec_any` будь-який — обидва з зрізами `day/week/period`). Уся структура — JSON у полі `payload`, історія не зберігається (кампанія перезаписується). Сторінка дозволяє порівнювати з іншою кампанією. Права: `report_admission:view` / `report_admission:generate`. |

#### Підсутності, що редагуються діалогами всередині батьківської форми

Не мають окремих сторінок — створюються/змінюються в модальних вікнах на формі батька і зберігаються разом із ним:

- На формі **Entrant** (`views/entrant.py`, `states/entrant.py:EntrantFormState`):
  `IdentityDocumentModel`, `DocumentAboutEducationModel`, `MilitaryAccountingModel`,
  `MedicalReferenceModel`, `InformationAboutRelativesModel`, `SpecialConditionPersonModel`,
  `SpecialtieEntrantModel` (пріоритетний список), `ResultZnoModel`.
- На формі **Admission campaign** (`views/admission_campaign.py`,
  `states/admission_campaign.py:_CampaignFormBase`): `AdmissionCampaignSpecialityModel`
  (квоти бюджет/контракт по спеціальностям).
- На формі **Entrant exam** (`views/entrant_exam.py`,
  `states/entrant_exam.py:_ExamFormBase`): список відповідальних
  співробітників (`EntrantExamWorkerModel`, M2M) — обирається через
  пікер-діалог з пошуком за ПІБ/email/логіном.

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
2. **Абітурієнти**: `entrants (id_person → person, id_entrant_group?) → specialties_entrant (priority list)`; `entrants_groups → entrants_exams (date, time_start, time_end, item_zno) ↔ workers (entrants_exams_workers, M2M відповідальні)`.
3. **Іспити та оцінки**: оцінка за іспит зберігається в існуючому `results_zno` через ключ `(id_items_zno, id_person)`. Сторінка перегляду іспиту виставляє оцінки абітурієнтам групи через `ResultZnoService.upsert(...)`; порожня оцінка видаляє запис.
4. **Вступна кампанія**: `admission_campaigns ← admission_campaigns_specialties (speciality, budget_places, contract_places)` — задає перелік спеціальностей, доступних абітурієнту при подачі пріоритетів у межах поточної кампанії.
5. **Студенти і навчання**: `students (id_person → person, id_group) → groups (id_specialties, id_curator) → specialties`
6. **Викладання**: `subjects (id_specialties) ↔ workers (через subjects_workers)`; `schedule (group, period) → lessons (subject, worker, schedule)`
7. **Документообіг**: `orders (id_type → type_orders, id_worker → workers)`
8. **Рейтинг**: `rating_snapshots (id_campaign, generated_at) ← rating_entries (id_speciality, id_entrant, position, total_points, status)`. Знімок формується на вимогу через `RatingService.generate(id_campaign)`: сума `results_zno.points` по особі (обрізана зверху до `max_total_points` з налаштувань, дефолт 200, DK-40) + ознака «квота» (`special_conditions_person → special_conditions.is_kvota = True`) → впорядкування «квоти зверху, далі за сумою балів desc» → розподіл по квотах `admission_campaigns_specialties` у статуси `kvota`/`budget`/`contract`/`rejected`. Абітурієнти, чий `application_status.is_allowed_in_rating = False` (дефолт), у ранжуванні не беруть участі: місць не займають, отримують статус `excluded` і найбільші `position` (самий низ таблиці, сірий рядок; DK-43). До офіційного DOCX-документа вони не потрапляють. Попередній знімок кампанії перезаписується (історія не зберігається). **`results_zno.points` зберігає вже домножений на коефіцієнт предмета бал** (множення відбувається при збереженні оцінки — у діалозі картки абітурієнта та у діалозі оцінювання іспиту); сирий введений бал лежить у `results_zno.points_raw` (щоб повторне редагування не домножувало вдруге).

### Угода: FK на `SpecialityModel` — завжди composite

`SpecialityModel` має composite PK `(code, id_department)`. Будь-яка таблиця, що посилається на спеціальність, повинна мати **два FK-стовпці** (`id_speciality_code`, `id_speciality_department`) і `ForeignKeyConstraint` через `__table_args__` — single FK на `code` логічно зламаний. Приклади — `SpecialtieEntrantModel`, `AdmissionCampaignSpecialityModel` (`models.py`). Для майбутніх `groups`, `subjects` тощо діє те саме правило.

### Активна вступна кампанія

`AdmissionCampaignService` надає два хелпери для бізнес-логіки, що мусить обмежуватись поточною кампанією:

- `get_active_campaign()` — повертає не видалену кампанію, чий діапазон `[start_date, end_date]` містить сьогоднішню дату (якщо їх декілька — найновіша за `start_date`).
- `get_active_range()` — та сама кампанія у вигляді пари `datetime` (00:00 початку та 23:59:59 кінця) — зручно для фільтрації за `created_at`.

Використовується, зокрема:

- У фільтрі списку абітурієнтів (`ListEntrantState`) — за замовчуванням показує лише абітурієнтів, створених у межах активної кампанії.
- У фільтрі графіка іспитів (`ListEntrantExamState`) — за замовчуванням обмежує іспити діапазоном дат активної кампанії; фільтрація йде по полю `EntrantExamModel.date` (рядки `YYYY-MM-DD` лексикографічно порівнюються коректно).
- У формі абітурієнта (`EntrantFormState._load_dropdowns`) — список спеціальностей у діалозі пріоритету обмежується тими, що входять до квот активної кампанії. Повний довідник зберігається у `all_speciality_options` і використовується в `speciality_labels`, щоб уже збережені пріоритети завжди мали підпис.
- На сторінці рейтингу (`ListRatingState`) — за замовчуванням обирається активна кампанія; список спеціальностей у фільтрі береться з квот обраної кампанії.

## Seed-дані

`uv run python seed.py` — наповнює БД тестовими записами для перевірки рейтингу та форм: довідники (відділення, спеціальності, предмети ЗНО, джерела фінансування, бази вступу, статуси, типи документів, родинні зв'язки, спецумови з is_kvota), активна вступна кампанія з квотами і ~100 абітурієнтів з результатами ЗНО, пріоритетами спеціальностей і випадковими спецумовами. Скрипт ідемпотентний по довідниках (get-or-create) і захищений від дублів абітурієнтів (через унікальний суфікс `_seed` у `edbo`).

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
- Тело страницы оборачивается в `page_wrapper(page_header, page_content, filter_panel=None)` из `Dekanat/views/templates/layouts.py`.
- Заголовок подстраницы — `header_subpage("Назва", *action_buttons)`. Это `hstack` с градиентным текстом и градиентным подчёркиванием снизу.
- **`filter_panel=` — это слот для управляющей карточки** (фильтры, выбор кампании/специальности и т.п.), которая рендерится **между header и контентом** и НЕ оборачивается в `rx.skeleton`. Если кладёте карточку с контролами внутрь `list_page_content`, она будет мигать при каждой подгрузке списка. Эталоны — `views/entrant.py`, `views/entrant_exam.py`, `views/rating.py`.
- **«Деканат» в шапке** ведёт на `routes.DASHBOARD` (главный dashboard), не на `/`.

### Dashboard'и розділів (DK-22)
- `Dekanat/declared/submenu.py:MenuItem` має поле `url` навіть у груп — там лежить маршрут section-dashboard'а (`routes.DASHBOARD_BASE`/`_CONTINGENT`/`_ADMISSION_COMMISSION`/`_ADMIN`).
- `MenuItem.dashboard_only: bool = False` — якщо `True`, пункт ховається з бокового меню (`sidebar_item` повертає `rx.fragment()`), але потрапляє у картки section-dashboard'а. Зручно для «сервісних» сторінок, які не варто пхати у головну навігацію.
- `sidebar_group` має різну поведінку залежно від `AppState.sidebar_open`: розгорнутий sidebar — клік по голові групи тогглить розкриття дітей; згорнутий — `head` стає `rx.link` на `item.url` (section-dashboard).
- Сторінки dashboard'ів (`views/dashboard.py`) — головний (`/dashboard`) + чотири розділових. Усі будуються з `MAIN` через `_cards_grid([MenuItem])` → `_card(item)`. Картки приховуються згідно `required_action` через `rx.cond(AppState.get_user_actions.contains(...))`.
- Резолв «який розділ → яка група» — `find_group_by_url(url)` із `submenu.py`, щоб view не дублював дерево.

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
