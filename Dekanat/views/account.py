import reflex as rx

from Dekanat.states.account import AccountSettingsState

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def _password_row(title: str, value, on_change) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, weight="bold"),
            rx.input(
                value=value,
                on_change=on_change,
                type="password",
                width="100%",
            ),
            spacing="1",
            align="stretch",
            width="100%",
        ),
        padding="0.8rem",
        border_radius="0.5rem",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        width="100%",
    )


def settings_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading("Параметри входу", size="4", margin_top="0.5rem"),
        _password_row(
            "Поточний пароль",
            AccountSettingsState.current_password,
            AccountSettingsState.set_current_password,
        ),
        _password_row(
            "Новий пароль",
            AccountSettingsState.new_password,
            AccountSettingsState.set_new_password,
        ),
        _password_row(
            "Підтвердження нового пароля",
            AccountSettingsState.confirm_password,
            AccountSettingsState.set_confirm_password,
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


@require_login
def settings_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Налаштування облікового запису",
            controls.button_image_primary(
                name_icon="save",
                on_click=AccountSettingsState.on_save,
                loading=AccountSettingsState.saving,
            ),
            width="100%",
        ),
        settings_page_content(),
        on_mount=AccountSettingsState.on_load,
    )
