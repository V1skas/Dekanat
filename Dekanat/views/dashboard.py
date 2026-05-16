import reflex as rx

from Dekanat.views.templates.layouts import page_wrapper
from Dekanat.views.auth import require_login

def dashboard_page_content():
    return rx.center(
        rx.vstack(
            rx.heading("Вітаю в системі Деканат!", size="9"),
            rx.text("Для початку роботи оберіть необхідний розділ ліворуч."),
        ),

        height="100%"
    )

@require_login
def dashboard_page() -> rx.Component:
    return page_wrapper(
        rx.box(),
        dashboard_page_content()
    )
