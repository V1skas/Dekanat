import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entrants_group import (
    ListEntrantsGroupState,
    AddEntrantsGroupState,
    EditEntrantsGroupState,
    ViewEntrantsGroupState,
)
from Dekanat.models import EntrantGroupModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: EntrantGroupModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ENTRANTS_GROUP_VIEW}{item.id}"),
            align="left"
        ),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListEntrantsGroupState.items, table_row),
            height="100%",
            width="100%"
        ),
        variant="surface",
        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListEntrantsGroupState.items.is_not_none(),
                table(),
                rx.text("Дані відсутні")),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewEntrantsGroupState.title),
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=AddEntrantsGroupState.title, on_change=AddEntrantsGroupState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=EditEntrantsGroupState.title, on_change=EditEntrantsGroupState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_ADD),
                    controls.button_image_primary(name_icon="plus", on_click=ListEntrantsGroupState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListEntrantsGroupState.in_progress, height="100%")
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_DELETE),
                    controls.button_image_secondary(name_icon="trash_2", on_click=ViewEntrantsGroupState.on_click_delete)),
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntrantsGroupState.on_click_edit)),
            left=controls.button_back(routes.ENTRANTS_GROUP_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewEntrantsGroupState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddEntrantsGroupState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddEntrantsGroupState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditEntrantsGroupState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditEntrantsGroupState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditEntrantsGroupState.in_process, height="100%")
    )
