import reflex as rx

from Dekanat.views.tamplates.layouts import base_layout, header_subpage
from Dekanat.views.auth import require_login
from Dekanat.declared import submenu

def dashboard_base_layout(page_header, page_content) -> rx.Component:
    return base_layout(
        page_header,
        page_content,
        "Головна",
        submenu.MAIN
    )

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
    return dashboard_base_layout(
        rx.box(),
        dashboard_page_content()
    )
