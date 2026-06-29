import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.role import ListRoleState, AddRoleState, EditRoleState, ViewRoleState
from Dekanat.models import RoleModel, ActionModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: RoleModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ROLES_VIEW}{item.id}"),
            align="left"
        ),
        rx.table.cell(
            rx.text(rx.cond(item.description, item.description, "—")),
            align="left"
        ),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Опис", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListRoleState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListRoleState.items,
                table(),
                controls.empty_placeholder()
                ),
    )


def view_action_row(action: ActionModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(action.title, weight="bold"),
            rx.text(action.description, color="gray", size="2"),
            spacing="1",
            align="start",
        ),
        width="100%",
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewRoleState.title, size="6"),
        rx.cond(
            ViewRoleState.description,
            rx.text(ViewRoleState.description, color="gray"),
        ),
        rx.divider(),
        rx.heading("Доступні дії", size="5"),
        rx.cond(
            ViewRoleState.actions,
            rx.vstack(
                rx.foreach(ViewRoleState.actions, view_action_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Дій не призначено", color="gray"),
        ),

        spacing="3",
        align="stretch",
        width="100%"
    )


def add_action_row(action: ActionModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=AddRoleState.selected_action_ids.contains(action.id),
                on_change=AddRoleState.toggle_action(action.id),
            ),
            rx.vstack(
                rx.text(action.title, weight="bold"),
                rx.text(action.description, color="gray", size="2"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(required=True, value=AddRoleState.title, on_change=AddRoleState.set_title),
        rx.text("Опис:"),
        rx.text_area(value=AddRoleState.description, on_change=AddRoleState.set_description),

        rx.divider(),
        rx.heading("Доступні дії", size="5"),
        rx.cond(
            AddRoleState.all_actions,
            rx.vstack(
                rx.foreach(AddRoleState.all_actions, add_action_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Дій не знайдено", color="gray"),
        ),

        spacing="3",
        align="stretch",
        width="100%"
    )


def edit_action_row(action: ActionModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=EditRoleState.selected_action_ids.contains(action.id),
                on_change=EditRoleState.toggle_action(action.id),
            ),
            rx.vstack(
                rx.text(action.title, weight="bold"),
                rx.text(action.description, color="gray", size="2"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(required=True, value=EditRoleState.title, on_change=EditRoleState.set_title),
        rx.text("Опис:"),
        rx.text_area(value=EditRoleState.description, on_change=EditRoleState.set_description),

        rx.divider(),
        rx.heading("Доступні дії", size="5"),
        rx.cond(
            EditRoleState.all_actions,
            rx.vstack(
                rx.foreach(EditRoleState.all_actions, edit_action_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Дій не знайдено", color="gray"),
        ),

        spacing="3",
        align="stretch",
        width="100%"
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListRoleState.get_user_actions.contains(Actions.ROLE_ADD), controls.button_image_primary(name_icon="plus", on_click=ListRoleState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListRoleState.in_progress, height="100%"),
        on_mount=ListRoleState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewRoleState.get_user_actions.contains(Actions.ROLE_DELETE), controls.delete_with_confirm(on_confirm=ViewRoleState.on_click_delete)),
            rx.cond(ViewRoleState.get_user_actions.contains(Actions.ROLE_EDIT), controls.button_image_primary(name_icon="pencil_line", on_click=ViewRoleState.on_click_edit)),
            left=controls.button_back(routes.ROLES_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewRoleState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddRoleState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddRoleState.on_save),
            width="100%"
        ),
        rx.skeleton(add_page_content(), loading=AddRoleState.in_process, height="100%")
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditRoleState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditRoleState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditRoleState.in_process, height="100%")
    )
