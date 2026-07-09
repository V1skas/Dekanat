import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.kinship import ListKinshipState, AddKinshipState, EditKinshipState, ViewKinshipState
from Dekanat.models import KinshipModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: KinshipModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.KINSHIP_VIEW}{item.id}"),
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
            rx.foreach(ListKinshipState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListKinshipState.items.is_not_none() & (ListKinshipState.items.length() > 0)),
                table(),
                controls.empty_placeholder()
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewKinshipState.title),

        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(
            id="title",
            required=True,
            value=AddKinshipState.title,
            on_change=AddKinshipState.set_title,
            width="100%",
        ),
        align="stretch",
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(
            id="title",
            required=True,
            value=EditKinshipState.title,
            on_change=EditKinshipState.set_title,
            width="100%",
        ),
        align="stretch",
        width="100%",
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListKinshipState.get_user_actions.contains(Actions.KINSHIP_ADD), controls.button_image_primary(name_icon="plus", on_click=ListKinshipState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListKinshipState.in_progress, height="100%"),
        on_mount=ListKinshipState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewKinshipState.get_user_actions.contains(Actions.KINSHIP_DELETE), controls.delete_with_confirm(on_confirm=ViewKinshipState.on_click_delete)),
            rx.cond(ViewKinshipState.get_user_actions.contains(Actions.KINSHIP_EDIT), controls.button_image_primary(name_icon="pencil_line", on_click=ViewKinshipState.on_click_edit)),
            left=controls.button_back(routes.KINSHIP_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewKinshipState.in_process, height="100%"),
            audit_history_section("kinship"),
            width="100%",
            align="stretch",
            spacing="4",
        )
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddKinshipState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddKinshipState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditKinshipState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditKinshipState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditKinshipState.in_process, height="100%")
    )
