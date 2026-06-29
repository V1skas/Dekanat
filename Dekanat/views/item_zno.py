import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.item_zno import ListItemZnoState, AddItemZnoState, EditItemZnoState, ViewItemZnoState
from Dekanat.models import ItemZnoModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: ItemZnoModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ITEM_ZNO_VIEW}{item.id}"),
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
            rx.foreach(ListItemZnoState.items, table_row),
            height="100%",
            width="100%"
        ),
        variant="surface",
        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListItemZnoState.items.is_not_none() & (ListItemZnoState.items.length() > 0)),
                table(),
                controls.empty_placeholder()),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewItemZnoState.title),
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=AddItemZnoState.title, on_change=AddItemZnoState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=EditItemZnoState.title, on_change=EditItemZnoState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_ADD),
                    controls.button_image_primary(name_icon="plus", on_click=ListItemZnoState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListItemZnoState.in_progress, height="100%"),
        on_mount=ListItemZnoState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_DELETE),
                    controls.delete_with_confirm(on_confirm=ViewItemZnoState.on_click_delete)),
            rx.cond(ViewItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewItemZnoState.on_click_edit)),
            left=controls.button_back(routes.ITEM_ZNO_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewItemZnoState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddItemZnoState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddItemZnoState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditItemZnoState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditItemZnoState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditItemZnoState.in_process, height="100%")
    )
