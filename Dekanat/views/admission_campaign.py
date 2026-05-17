import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.admission_campaign import (
    ListAdmissionCampaignState,
    AddAdmissionCampaignState,
    EditAdmissionCampaignState,
    ViewAdmissionCampaignState,
)
from Dekanat.models import AdmissionCampaignModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def _row(item: AdmissionCampaignModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ADMISSION_CAMPAIGN_VIEW}{item.id}"),
            align="left",
        ),
        rx.table.cell(item.start_date),
        rx.table.cell(item.end_date),
    )


def _table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Дата початку", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Дата завершення", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListAdmissionCampaignState.items, _row),
            height="100%",
            width="100%",
        ),
        variant="surface",
        height="100%",
        width="100%",
    )


def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            ListAdmissionCampaignState.items.is_not_none() & (ListAdmissionCampaignState.items.length() > 0),
            _table(),
            controls.empty_placeholder(),
        ),
    )


def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewAdmissionCampaignState.title, size="6"),
        rx.hstack(
            rx.text("Дата початку:", weight="bold"),
            rx.text(ViewAdmissionCampaignState.start_date),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.text("Дата завершення:", weight="bold"),
            rx.text(ViewAdmissionCampaignState.end_date),
            spacing="2",
            align="center",
        ),
        spacing="3",
        align="stretch",
        height="100%",
        width="100%",
    )


def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=AddAdmissionCampaignState.title,
            on_change=AddAdmissionCampaignState.set_title,
            width="100%",
        ),
        rx.text("*Дата початку:"),
        rx.input(
            type="date",
            required=True,
            value=AddAdmissionCampaignState.start_date,
            on_change=AddAdmissionCampaignState.set_start_date,
            width="100%",
        ),
        rx.text("*Дата завершення:"),
        rx.input(
            type="date",
            required=True,
            value=AddAdmissionCampaignState.end_date,
            on_change=AddAdmissionCampaignState.set_end_date,
            width="100%",
        ),
        align="stretch",
        spacing="3",
        width="100%",
    )


def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=EditAdmissionCampaignState.title,
            on_change=EditAdmissionCampaignState.set_title,
            width="100%",
        ),
        rx.text("*Дата початку:"),
        rx.input(
            type="date",
            required=True,
            value=EditAdmissionCampaignState.start_date,
            on_change=EditAdmissionCampaignState.set_start_date,
            width="100%",
        ),
        rx.text("*Дата завершення:"),
        rx.input(
            type="date",
            required=True,
            value=EditAdmissionCampaignState.end_date,
            on_change=EditAdmissionCampaignState.set_end_date,
            width="100%",
        ),
        align="stretch",
        spacing="3",
        width="100%",
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(
                ListAdmissionCampaignState.get_user_actions.contains(Actions.ADMISSION_CAMPAIGN_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListAdmissionCampaignState.on_click_add),
            ),
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListAdmissionCampaignState.in_progress, height="100%"),
    )


@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewAdmissionCampaignState.get_user_actions.contains(Actions.ADMISSION_CAMPAIGN_DELETE),
                controls.delete_with_confirm(on_confirm=ViewAdmissionCampaignState.on_click_delete),
            ),
            rx.cond(
                ViewAdmissionCampaignState.get_user_actions.contains(Actions.ADMISSION_CAMPAIGN_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewAdmissionCampaignState.on_click_edit),
            ),
            left=controls.button_back(routes.ADMISSION_CAMPAIGN_LIST),
            width="100%",
        ),
        rx.skeleton(view_page_content(), loading=ViewAdmissionCampaignState.in_process, height="100%"),
    )


@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddAdmissionCampaignState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddAdmissionCampaignState.on_save),
            width="100%",
        ),
        rx.skeleton(add_page_content(), loading=AddAdmissionCampaignState.in_process, height="100%"),
    )


@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditAdmissionCampaignState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditAdmissionCampaignState.on_save),
            width="100%",
        ),
        rx.skeleton(edit_page_content(), loading=EditAdmissionCampaignState.in_process, height="100%"),
    )
