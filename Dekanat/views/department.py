import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.department import (
    ListDepartmentState,
    AddDepartmentState,
    EditDepartmentState,
    ViewDepartmentState,
)
from Dekanat.models import DepartmentModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: DepartmentModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.DEPARTMENT_VIEW}{item.id}"),
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
            rx.foreach(ListDepartmentState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListDepartmentState.items.is_not_none() & (ListDepartmentState.items.length() > 0)),
                table(),
                controls.empty_placeholder()
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewDepartmentState.title, size="6"),

        spacing="3",
        align="stretch",
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=AddDepartmentState.title,
            on_change=AddDepartmentState.set_title,
        ),

        align="stretch",
        spacing="3",
        width="100%"
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=EditDepartmentState.title,
            on_change=EditDepartmentState.set_title,
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
                ListDepartmentState.get_user_actions.contains(Actions.DEPARTMENT_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListDepartmentState.on_click_add),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListDepartmentState.in_progress, height="100%"),
        on_mount=ListDepartmentState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewDepartmentState.get_user_actions.contains(Actions.DEPARTMENT_DELETE),
                controls.delete_with_confirm(on_confirm=ViewDepartmentState.on_click_delete),
            ),
            rx.cond(
                ViewDepartmentState.get_user_actions.contains(Actions.DEPARTMENT_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewDepartmentState.on_click_edit),
            ),
            left=controls.button_back(routes.DEPARTMENT_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewDepartmentState.in_process, height="100%"),
            audit_history_section(Actions.DEPARTMENT_HISTORY_VIEW.value, Actions.DEPARTMENT_HISTORY_DETAIL.value),
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
            controls.button_image_secondary(name_icon="circle_x", on_click=AddDepartmentState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddDepartmentState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditDepartmentState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditDepartmentState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditDepartmentState.in_process, height="100%")
    )
