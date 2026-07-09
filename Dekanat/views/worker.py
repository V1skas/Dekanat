import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.worker import ListWorkerState, AddWorkerState, EditWorkerState, ViewWorkerState
from Dekanat.models import WorkerModel, RoleModel, ActionModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: WorkerModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.pib, href=f"{routes.WORKERS_VIEW}{item.id}"),
            align="left"
        ),
        rx.table.cell(rx.text(item.login), align="left"),
        rx.table.cell(rx.text(rx.cond(item.email, item.email, "—")), align="left"),
        rx.table.cell(rx.text(rx.cond(item.phone_number, item.phone_number, "—")), align="left"),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Логін", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Email", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Телефон", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListWorkerState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListWorkerState.items,
                table(),
                controls.empty_placeholder()
                ),
    )


def view_role_row(role: RoleModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(role.title, weight="bold"),
            rx.text(rx.cond(role.description, role.description, ""), color="gray", size="2"),
            spacing="1",
            align="start",
        ),
        width="100%",
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
        rx.heading(ViewWorkerState.pib, size="6"),
        rx.text(rx.cond(ViewWorkerState.login, "Логін: " + ViewWorkerState.login, ""), color="gray"),
        rx.cond(ViewWorkerState.email, rx.text("Email: " + ViewWorkerState.email, color="gray")),
        rx.cond(ViewWorkerState.phone_number, rx.text("Телефон: " + ViewWorkerState.phone_number, color="gray")),

        rx.divider(),
        rx.heading("Ролі", size="5"),
        rx.cond(
            ViewWorkerState.roles,
            rx.vstack(
                rx.foreach(ViewWorkerState.roles, view_role_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Ролі не призначено", color="gray"),
        ),

        rx.divider(),
        rx.heading("Додаткові дії", size="5"),
        rx.cond(
            ViewWorkerState.actions,
            rx.vstack(
                rx.foreach(ViewWorkerState.actions, view_action_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Додаткових дій не призначено", color="gray"),
        ),

        spacing="3",
        align="stretch",
        width="100%"
    )


def add_role_row(role: RoleModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=AddWorkerState.selected_role_ids.contains(role.id),
                on_change=AddWorkerState.toggle_role(role.id),
            ),
            rx.vstack(
                rx.text(role.title, weight="bold"),
                rx.text(rx.cond(role.description, role.description, ""), color="gray", size="2"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
    )

def add_action_row(action: ActionModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=AddWorkerState.selected_action_ids.contains(action.id),
                on_change=AddWorkerState.toggle_action(action.id),
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
        rx.text("*ПІБ:"),
        rx.input(required=True, value=AddWorkerState.pib, on_change=AddWorkerState.set_pib),
        rx.text("*Логін:"),
        rx.input(required=True, value=AddWorkerState.login, on_change=AddWorkerState.set_login),
        rx.text("*Пароль:"),
        rx.input(required=True, type="password", value=AddWorkerState.password, on_change=AddWorkerState.set_password),
        rx.text("Телефон:"),
        rx.input(value=AddWorkerState.phone_number, on_change=AddWorkerState.set_phone_number),
        rx.text("Email:"),
        rx.input(value=AddWorkerState.email, on_change=AddWorkerState.set_email),
        rx.text("Фото (URL):"),
        rx.input(value=AddWorkerState.photo, on_change=AddWorkerState.set_photo),

        rx.divider(),
        rx.heading("Ролі", size="5"),
        rx.cond(
            AddWorkerState.all_roles,
            rx.vstack(
                rx.foreach(AddWorkerState.all_roles, add_role_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Ролі не знайдено", color="gray"),
        ),

        rx.divider(),
        rx.heading("Додаткові дії", size="5"),
        rx.cond(
            AddWorkerState.all_actions,
            rx.vstack(
                rx.foreach(AddWorkerState.all_actions, add_action_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Дій не знайдено", color="gray"),
        ),

        spacing="3",
        align="stretch",
        width="100%"
    )


def edit_role_row(role: RoleModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=EditWorkerState.selected_role_ids.contains(role.id),
                on_change=EditWorkerState.toggle_role(role.id),
            ),
            rx.vstack(
                rx.text(role.title, weight="bold"),
                rx.text(rx.cond(role.description, role.description, ""), color="gray", size="2"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
    )

def edit_action_row(action: ActionModel) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.checkbox(
                checked=EditWorkerState.selected_action_ids.contains(action.id),
                on_change=EditWorkerState.toggle_action(action.id),
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
        rx.text("*ПІБ:"),
        rx.input(required=True, value=EditWorkerState.pib, on_change=EditWorkerState.set_pib),
        rx.text("*Логін:"),
        rx.input(required=True, value=EditWorkerState.login, on_change=EditWorkerState.set_login),
        rx.text("Новий пароль (залиште порожнім, щоб не змінювати):"),
        rx.input(type="password", value=EditWorkerState.password, on_change=EditWorkerState.set_password),
        rx.text("Телефон:"),
        rx.input(value=EditWorkerState.phone_number, on_change=EditWorkerState.set_phone_number),
        rx.text("Email:"),
        rx.input(value=EditWorkerState.email, on_change=EditWorkerState.set_email),
        rx.text("Фото (URL):"),
        rx.input(value=EditWorkerState.photo, on_change=EditWorkerState.set_photo),

        rx.divider(),
        rx.heading("Ролі", size="5"),
        rx.cond(
            EditWorkerState.all_roles,
            rx.vstack(
                rx.foreach(EditWorkerState.all_roles, edit_role_row),
                spacing="2",
                width="100%",
            ),
            rx.text("Ролі не знайдено", color="gray"),
        ),

        rx.divider(),
        rx.heading("Додаткові дії", size="5"),
        rx.cond(
            EditWorkerState.all_actions,
            rx.vstack(
                rx.foreach(EditWorkerState.all_actions, edit_action_row),
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
            rx.cond(ListWorkerState.get_user_actions.contains(Actions.WORKER_ADD), controls.button_image_primary(name_icon="plus", on_click=ListWorkerState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListWorkerState.in_progress, height="100%"),
        on_mount=ListWorkerState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewWorkerState.get_user_actions.contains(Actions.WORKER_DELETE), controls.delete_with_confirm(on_confirm=ViewWorkerState.on_click_delete)),
            rx.cond(ViewWorkerState.get_user_actions.contains(Actions.WORKER_EDIT), controls.button_image_primary(name_icon="pencil_line", on_click=ViewWorkerState.on_click_edit)),
            left=controls.button_back(routes.WORKERS_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewWorkerState.in_process, height="100%"),
            audit_history_section("workers"),
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
            controls.button_image_secondary(name_icon="circle_x", on_click=AddWorkerState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddWorkerState.on_save),
            width="100%"
        ),
        rx.skeleton(add_page_content(), loading=AddWorkerState.in_process, height="100%")
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditWorkerState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditWorkerState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditWorkerState.in_process, height="100%")
    )
