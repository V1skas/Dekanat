import os

import reflex as rx

# Для локального запуску — SQLite (за замовчуванням). У Docker/compose рядок
# підключення приходить через змінну оточення DB_URL (compose формує MySQL-URL
# сам, Dockerfile ставить SQLite у /Dekanat/data для одиночного контейнера).
DB_URL = os.environ.get("DB_URL", "sqlite:///reflex.db")

# Публічна адреса бекенду, до якої браузер підключає вебсокет Reflex. На проді
# фронт зібраний статикою і роздається nginx'ом, тому api_url мусить вказувати на
# зовнішній хост (через nginx). Значення вшивається у фронт на етапі збірки
# (`reflex export --frontend-only`) і читається бекендом при `reflex run
# --backend-only`. Локально лишається дефолтний http://localhost:8000.
API_URL = os.environ.get("API_URL", "http://localhost:8000")
DEPLOY_URL = os.environ.get("DEPLOY_URL", "http://localhost:3000")

config = rx.Config(
    app_name="Dekanat",
    db_url=DB_URL,
    api_url=API_URL,
    deploy_url=DEPLOY_URL,
    # Reflex 0.8.9+ депрекейтить auto-setters. У нас усі `set_*` оголошені явно
    # у відповідних State-класах — це дозволяє наочно знати, які поля «прив'язані»
    # до інпутів, і не плодити мовчазні сетери на кожне поле state.
    state_auto_setters=False,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
