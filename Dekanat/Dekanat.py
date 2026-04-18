import reflex as rx

from rxconfig import config
from Dekanat.views.auth import require_login, index as login_page
from Dekanat import models, routes
from Dekanat.views.tamplates.layouts import base_layout, header_subpage
from Dekanat.views.tamplates.controlls import button_primery, button_secondary, button_image_primery, button_image_secondary
from Dekanat.declared import submenu
from Dekanat import routes


def index_content() -> rx.Component:
    # Welcome Page (Index)
    return rx.vstack(
        rx.heading("Welcome to Reflex!", size="9"),
        rx.text(
            "Get started by editing ",
            rx.code(f"{config.app_name}/{config.app_name}.py"),
            size="5",
        ),
        rx.hstack(
            button_secondary("Secondary button"),
            button_primery("Primery button"),
        ),
        rx.hstack(
            button_image_secondary(name_icon="graduation-cap"),
            button_image_primery(name_icon="graduation-cap"),
        ),
        spacing="5",
        width="100%"
    )

def index():
    return base_layout(
        header_subpage(button_image_secondary(name_icon="graduation-cap"), button_image_primery(name_icon="graduation-cap"), width="100%"),
        index_content(),
        "Головна",
        submenu.MAIN
    )


app = rx.App(
    theme=rx.theme(
            appearance="light",
            has_background=True,
            radius="large",
            accent_color="brown",
        )
)

app.add_page(index, route=routes.DASHBOARD)
app.add_page(login_page, route=routes.LOGIN)
