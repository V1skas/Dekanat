import reflex as rx

config = rx.Config(
    app_name="Dekanat",
    db_url="sqlite:///reflex.db",
    # Reflex 0.8.9+ депрекейтить auto-setters. У нас усі `set_*` оголошені явно
    # у відповідних State-класах — це дозволяє наочно знати, які поля «прив'язані»
    # до інпутів, і не плодити мовчазні сетери на кожне поле state.
    state_auto_setters=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
