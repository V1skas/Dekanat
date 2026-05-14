import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.special_condition import (
    ListSpecialConditionState,
    AddSpecialConditionState,
    EditSpecialConditionState,
    ViewSpecialConditionState,
)
from Dekanat.models import SpecialConditionModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: SpecialConditionModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.subcategory_code, align="center"),
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.SPECIAL_CONDITION_VIEW}{item.subcategory_code}"),
            align="left"
        ),
        rx.table.cell(
            rx.text(rx.cond(item.is_kvota, "Так", "Ні")),
            align="center"
        ),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Код", min_width="30px", width="30px", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Квота", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListSpecialConditionState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListSpecialConditionState.items.is_not_none(),
                table(),
                rx.text("Дані відсутні")
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewSpecialConditionState.title, size="6"),
        rx.text("Код: " + ViewSpecialConditionState.subcategory_code, color="gray"),
        rx.text("Квота: ", rx.cond(ViewSpecialConditionState.is_kvota, "Так", "Ні"), color="gray"),
        rx.cond(
            ViewSpecialConditionState.description,
            rx.text(ViewSpecialConditionState.description),
        ),

        spacing="3",
        align="stretch",
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Код підкатегорії:"),
        rx.input(
            required=True,
            value=AddSpecialConditionState.subcategory_code,
            on_change=AddSpecialConditionState.set_subcategory_code,
        ),
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=AddSpecialConditionState.title,
            on_change=AddSpecialConditionState.set_title,
        ),
        rx.text("Опис:"),
        rx.text_area(
            value=AddSpecialConditionState.description,
            on_change=AddSpecialConditionState.set_description,
        ),
        rx.hstack(
            rx.text("Квота:"),
            rx.switch(
                checked=AddSpecialConditionState.is_kvota,
                on_change=AddSpecialConditionState.set_is_kvota,
            ),
            align="center",
            spacing="3",
        ),

        align="stretch",
        spacing="3",
        width="100%"
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("Код підкатегорії:"),
        rx.input(
            value=EditSpecialConditionState.subcategory_code,
            disabled=True,
        ),
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=EditSpecialConditionState.title,
            on_change=EditSpecialConditionState.set_title,
        ),
        rx.text("Опис:"),
        rx.text_area(
            value=EditSpecialConditionState.description,
            on_change=EditSpecialConditionState.set_description,
        ),
        rx.hstack(
            rx.text("Квота:"),
            rx.switch(
                checked=EditSpecialConditionState.is_kvota,
                on_change=EditSpecialConditionState.set_is_kvota,
            ),
            align="center",
            spacing="3",
        ),

        align="stretch",
        spacing="3",
        width="100%"
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(
                ListSpecialConditionState.get_user_actions.contains(Actions.SPECIAL_CONDITION_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListSpecialConditionState.on_click_add),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListSpecialConditionState.in_progress, height="100%")
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewSpecialConditionState.get_user_actions.contains(Actions.SPECIAL_CONDITION_DELETE),
                controls.button_image_secondary(name_icon="trash_2", on_click=ViewSpecialConditionState.on_click_delete),
            ),
            rx.cond(
                ViewSpecialConditionState.get_user_actions.contains(Actions.SPECIAL_CONDITION_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewSpecialConditionState.on_click_edit),
            ),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewSpecialConditionState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddSpecialConditionState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddSpecialConditionState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditSpecialConditionState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditSpecialConditionState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditSpecialConditionState.in_process, height="100%")
    )
