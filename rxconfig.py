import os

import reflex as rx

# Для локального запуску — SQLite (за замовчуванням). У Docker/compose рядок
# підключення приходить через змінну оточення DB_URL (compose формує MySQL-URL
# сам, Dockerfile ставить SQLite у /Dekanat/data для одиночного контейнера).
DB_URL = os.environ.get("DB_URL", "sqlite:///reflex.db")

config = rx.Config(
    app_name="Dekanat",
    db_url=DB_URL,
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
