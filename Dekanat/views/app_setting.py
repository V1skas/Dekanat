import reflex as rx

from Dekanat.actions import Actions
from Dekanat.states.app_setting import ListAppSettingState, SettingDraft

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def _setting_input(item: SettingDraft) -> rx.Component:
    return rx.cond(
        item.value_type == "int",
        rx.input(
            type="number",
            value=item.value,
            on_change=ListAppSettingState.set_value(item.key),
            width="100%",
        ),
        rx.input(
            value=item.value,
            on_change=ListAppSettingState.set_value(item.key),
            width="100%",
        ),
    )


def _setting_row(item: SettingDraft) -> rx.Component:
    return rx.vstack(
        # Заголовок секції рендериться лише для першого елемента в категорії
        # (Reflex не дає прямо рендерити вкладений foreach над rx.Base, тому
        # для розбиття за категоріями використовуємо плоский список з sentinel'ом).
        rx.cond(
            item.section_header != "",
            rx.heading(item.section_header, size="4", margin_top="0.5rem"),
        ),
        rx.box(
            rx.vstack(
                rx.text(item.title, weight="bold"),
                rx.cond(
                    item.description != "",
                    rx.text(item.description, size="2", color="gray"),
                ),
                _setting_input(item),
                spacing="1",
                align="stretch",
                width="100%",
            ),
            padding="0.8rem",
            border_radius="0.5rem",
            background_color=rx.color("gray", 2),
            border=f"1px solid {rx.color('gray', 5)}",
            width="100%",
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.foreach(ListAppSettingState.drafts, _setting_row),
        spacing="3",
        align="stretch",
        width="100%",
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Налаштування",
            rx.cond(
                ListAppSettingState.get_user_actions.contains(Actions.SETTINGS_EDIT),
                controls.button_image_primary(name_icon="save", on_click=ListAppSettingState.on_save),
            ),
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListAppSettingState.in_progress, height="100%"),
    )
