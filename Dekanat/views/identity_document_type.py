import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.identity_document_type import AddIdentityDocumentTypeState, EditIdentityDocumentTypeState, ViewIdentityDocumentTypeState, ListIdentityDocumentTypeState
from Dekanat.models import IdentityDocumentTypeModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: IdentityDocumentTypeModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.IDENTITY_DOCUMENT_TYPE_VIEW}{item.id}"),
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
            rx.foreach(ListIdentityDocumentTypeState.items, table_row), #type: ignore
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListIdentityDocumentTypeState.items.is_not_none(), #type: ignore
            table(),
            rx.text("Дані відсутні")
        ),
    )

def view_page_content():
    return rx.vstack(
        rx.heading(ViewIdentityDocumentTypeState.title),
        rx.text(ViewIdentityDocumentTypeState.description),

        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(required=True, value=AddIdentityDocumentTypeState.title, on_change=AddIdentityDocumentTypeState.set_title),
        rx.text("Опис:"),
        rx.text_area(value=AddIdentityDocumentTypeState.description, on_change=AddIdentityDocumentTypeState.set_description),

        align="stretch",
        width="100%"
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(required=True, value=EditIdentityDocumentTypeState.title, on_change=EditIdentityDocumentTypeState.set_title),
        rx.text("Опис:"),
        rx.text_area(value=EditIdentityDocumentTypeState.description, on_change=EditIdentityDocumentTypeState.set_description),

        align="stretch",
        width="100%"
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListIdentityDocumentTypeState.get_user_actions.contains(Actions.IDENTITY_DOCUMENT_TYPE_ADD), controls.button_image_primary(name_icon="plus", on_click=ListIdentityDocumentTypeState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListIdentityDocumentTypeState.process_items, height="100%")
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewIdentityDocumentTypeState.get_user_actions.contains(Actions.IDENTITY_DOCUMENT_TYPE_DELETE), controls.button_image_secondary(name_icon="trash_2", on_click=ViewIdentityDocumentTypeState.on_click_delete)),
            rx.cond(ViewIdentityDocumentTypeState.get_user_actions.contains(Actions.IDENTITY_DOCUMENT_TYPE_EDIT), controls.button_image_primary(name_icon="pencil_line", on_click=ViewIdentityDocumentTypeState.on_click_edit)),
            left=controls.button_back(routes.IDENTITY_DOCUMENT_TYPE_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewIdentityDocumentTypeState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddIdentityDocumentTypeState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddIdentityDocumentTypeState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditIdentityDocumentTypeState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditIdentityDocumentTypeState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditIdentityDocumentTypeState.in_process, height="100%")
    )
