import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.application_status import (
    ListApplicationStatusState,
    AddApplicationStatusState,
    EditApplicationStatusState,
    ViewApplicationStatusState,
)
from Dekanat.models import ApplicationStatusModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: ApplicationStatusModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.APPLICATION_STATUS_VIEW}{item.id}"),
            align="left"
        ),
        rx.table.cell(
            rx.text(rx.cond(item.description, item.description, "—")),
            align="left"
        ),
        rx.table.cell(
            rx.cond(item.is_default, rx.icon("check", color=rx.color("accent", 9)), rx.text("—")),
            align="center"
        ),
        rx.table.cell(
            rx.cond(item.is_allowed_in_rating, rx.icon("check", color=rx.color("accent", 9)), rx.text("—")),
            align="center"
        ),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Опис", color=rx.color("accent", 2)),
                rx.table.column_header_cell("За замовчуванням", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Допуск до рейтингу", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListApplicationStatusState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListApplicationStatusState.items.is_not_none() & (ListApplicationStatusState.items.length() > 0)),
                table(),
                controls.empty_placeholder()
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewApplicationStatusState.title, size="6"),
        rx.cond(
            ViewApplicationStatusState.description,
            rx.text(ViewApplicationStatusState.description),
        ),
        rx.cond(
            ViewApplicationStatusState.is_default,
            rx.badge("Статус за замовчуванням для нових карток абітурієнтів", color_scheme="brown"),
        ),
        rx.badge(
            rx.cond(
                ViewApplicationStatusState.is_allowed_in_rating,
                "Допускається до рейтингового списку",
                "Не допускається до рейтингового списку",
            ),
            color_scheme=rx.cond(ViewApplicationStatusState.is_allowed_in_rating, "green", "gray"),
        ),

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
            value=AddApplicationStatusState.title,
            on_change=AddApplicationStatusState.set_title,
        ),
        rx.text("Опис:"),
        rx.text_area(
            value=AddApplicationStatusState.description,
            on_change=AddApplicationStatusState.set_description,
        ),
        rx.hstack(
            rx.switch(
                checked=AddApplicationStatusState.is_default,
                on_change=AddApplicationStatusState.set_is_default,
            ),
            rx.text("Використовувати за замовчуванням для нових карток абітурієнтів"),
            align="center",
            spacing="2",
        ),
        rx.hstack(
            rx.switch(
                checked=AddApplicationStatusState.is_allowed_in_rating,
                on_change=AddApplicationStatusState.set_is_allowed_in_rating,
            ),
            rx.text("Допускати абітурієнтів із цим статусом до рейтингового списку"),
            align="center",
            spacing="2",
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
            value=EditApplicationStatusState.title,
            on_change=EditApplicationStatusState.set_title,
        ),
        rx.text("Опис:"),
        rx.text_area(
            value=EditApplicationStatusState.description,
            on_change=EditApplicationStatusState.set_description,
        ),
        rx.hstack(
            rx.switch(
                checked=EditApplicationStatusState.is_default,
                on_change=EditApplicationStatusState.set_is_default,
            ),
            rx.text("Використовувати за замовчуванням для нових карток абітурієнтів"),
            align="center",
            spacing="2",
        ),
        rx.hstack(
            rx.switch(
                checked=EditApplicationStatusState.is_allowed_in_rating,
                on_change=EditApplicationStatusState.set_is_allowed_in_rating,
            ),
            rx.text("Допускати абітурієнтів із цим статусом до рейтингового списку"),
            align="center",
            spacing="2",
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
                ListApplicationStatusState.get_user_actions.contains(Actions.APPLICATION_STATUS_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListApplicationStatusState.on_click_add),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListApplicationStatusState.in_progress, height="100%"),
        on_mount=ListApplicationStatusState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewApplicationStatusState.get_user_actions.contains(Actions.APPLICATION_STATUS_DELETE),
                controls.delete_with_confirm(on_confirm=ViewApplicationStatusState.on_click_delete),
            ),
            rx.cond(
                ViewApplicationStatusState.get_user_actions.contains(Actions.APPLICATION_STATUS_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewApplicationStatusState.on_click_edit),
            ),
            left=controls.button_back(routes.APPLICATION_STATUS_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewApplicationStatusState.in_process, height="100%"),
            audit_history_section("application_statuses"),
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
            controls.button_image_secondary(name_icon="circle_x", on_click=AddApplicationStatusState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddApplicationStatusState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditApplicationStatusState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditApplicationStatusState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditApplicationStatusState.in_process, height="100%")
    )
