import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entry_base import ListEntryBaseState, AddEntryBaseState, EditEntryBaseState, ViewEntryBaseState
from Dekanat.models import EntryBaseModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: EntryBaseModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ENTRY_BASE_VIEW}{item.id}"),
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
            rx.foreach(ListEntryBaseState.items, table_row),
            height="100%",
            width="100%"
        ),
        variant="surface",
        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListEntryBaseState.items.is_not_none() & (ListEntryBaseState.items.length() > 0)),
                table(),
                controls.empty_placeholder()),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewEntryBaseState.title),
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=AddEntryBaseState.title, on_change=AddEntryBaseState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=EditEntryBaseState.title, on_change=EditEntryBaseState.set_title, width="100%"),
        align="stretch",
        spacing="3",
        width="100%",
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListEntryBaseState.get_user_actions.contains(Actions.ENTRY_BASE_ADD),
                    controls.button_image_primary(name_icon="plus", on_click=ListEntryBaseState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListEntryBaseState.in_progress, height="100%")
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewEntryBaseState.get_user_actions.contains(Actions.ENTRY_BASE_DELETE),
                    controls.delete_with_confirm(on_confirm=ViewEntryBaseState.on_click_delete)),
            rx.cond(ViewEntryBaseState.get_user_actions.contains(Actions.ENTRY_BASE_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntryBaseState.on_click_edit)),
            left=controls.button_back(routes.ENTRY_BASE_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewEntryBaseState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddEntryBaseState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddEntryBaseState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditEntryBaseState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditEntryBaseState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditEntryBaseState.in_process, height="100%")
    )
