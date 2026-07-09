import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.source_of_funding import (
    ListSourceOfFundingState,
    AddSourceOfFundingState,
    EditSourceOfFundingState,
    ViewSourceOfFundingState,
)
from Dekanat.models import SourceOfFundingModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: SourceOfFundingModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.SOURCE_OF_FUNDING_VIEW}{item.id}"),
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
            rx.foreach(ListSourceOfFundingState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListSourceOfFundingState.items.is_not_none() & (ListSourceOfFundingState.items.length() > 0)),
                table(),
                controls.empty_placeholder()
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewSourceOfFundingState.title, size="6"),
        rx.hstack(
            rx.text("Пріоритет (sequence):", weight="bold"),
            rx.text(ViewSourceOfFundingState.sequence_str),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.text("Колір:", weight="bold"),
            rx.box(width="1.5rem", height="1.5rem", border_radius="4px",
                   background_color=ViewSourceOfFundingState.color, border="1px solid #0002"),
            rx.text(ViewSourceOfFundingState.color),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.text("Також конкурує у ресурсах:", weight="bold"),
            rx.text(ViewSourceOfFundingState.eligible_titles_str),
            spacing="2",
            align="center",
        ),

        spacing="3",
        align="stretch",
        height="100%",
        width="100%"
    )


def _eligible_checkbox(form_state):
    def _item(opt: Dict[str, str]) -> rx.Component:
        return rx.hstack(
            rx.checkbox(
                checked=form_state.eligible_ids.contains(opt["value"]),
                on_change=lambda _: form_state.toggle_eligible(opt["value"]),
            ),
            rx.text(opt["label"]),
            spacing="2",
            align="center",
        )

    return _item


def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=AddSourceOfFundingState.title,
            on_change=AddSourceOfFundingState.set_title,
        ),
        rx.text("*Пріоритет (менше — раніше в конкурсі):"),
        rx.input(
            type="number",
            required=True,
            value=AddSourceOfFundingState.sequence_str,
            on_change=AddSourceOfFundingState.set_sequence,
        ),
        rx.text("Колір підсвітки:"),
        rx.input(
            type="color",
            value=AddSourceOfFundingState.color,
            on_change=AddSourceOfFundingState.set_color,
        ),
        rx.text("Також конкурує у ресурсах (лише з вищим пріоритетом):"),
        rx.vstack(
            rx.foreach(AddSourceOfFundingState.other_resource_options, _eligible_checkbox(AddSourceOfFundingState)),
            spacing="1",
            align="start",
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
            value=EditSourceOfFundingState.title,
            on_change=EditSourceOfFundingState.set_title,
        ),
        rx.text("*Пріоритет (менше — раніше в конкурсі):"),
        rx.input(
            type="number",
            required=True,
            value=EditSourceOfFundingState.sequence_str,
            on_change=EditSourceOfFundingState.set_sequence,
        ),
        rx.text("Колір підсвітки:"),
        rx.input(
            type="color",
            value=EditSourceOfFundingState.color,
            on_change=EditSourceOfFundingState.set_color,
        ),
        rx.text("Також конкурує у ресурсах (лише з вищим пріоритетом):"),
        rx.vstack(
            rx.foreach(EditSourceOfFundingState.other_resource_options, _eligible_checkbox(EditSourceOfFundingState)),
            spacing="1",
            align="start",
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
                ListSourceOfFundingState.get_user_actions.contains(Actions.SOURCE_OF_FUNDING_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListSourceOfFundingState.on_click_add),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListSourceOfFundingState.in_progress, height="100%"),
        on_mount=ListSourceOfFundingState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewSourceOfFundingState.get_user_actions.contains(Actions.SOURCE_OF_FUNDING_DELETE),
                controls.delete_with_confirm(on_confirm=ViewSourceOfFundingState.on_click_delete),
            ),
            rx.cond(
                ViewSourceOfFundingState.get_user_actions.contains(Actions.SOURCE_OF_FUNDING_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewSourceOfFundingState.on_click_edit),
            ),
            left=controls.button_back(routes.SOURCE_OF_FUNDING_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewSourceOfFundingState.in_process, height="100%"),
            audit_history_section(Actions.SOURCE_OF_FUNDING_HISTORY_VIEW.value, Actions.SOURCE_OF_FUNDING_HISTORY_DETAIL.value),
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
            controls.button_image_secondary(name_icon="circle_x", on_click=AddSourceOfFundingState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddSourceOfFundingState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditSourceOfFundingState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditSourceOfFundingState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditSourceOfFundingState.in_process, height="100%")
    )
