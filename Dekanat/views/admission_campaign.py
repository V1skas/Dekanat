import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.admission_campaign import (
    ListAdmissionCampaignState,
    AddAdmissionCampaignState,
    EditAdmissionCampaignState,
    ViewAdmissionCampaignState,
)
from Dekanat.models import AdmissionCampaignModel, AdmissionCampaignSpecialityModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
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


# ============================================================
# Helpers for quotas table
# ============================================================

def _quotas_header(*titles: str) -> rx.Component:
    return rx.table.header(
        rx.table.row(*[rx.table.column_header_cell(t, color=rx.color("accent", 2)) for t in titles]),
        background_color=rx.color("accent", 9),
    )


def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


# ---------- View page ----------

def _view_quota_row(item: AdmissionCampaignSpecialityModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.cond(
                item.speciality,
                item.speciality.code + " " + item.speciality.title + " (" + item.speciality.tag + ")",
                "—",
            ),
            align="left",
        ),
        rx.table.cell(rx.cond(item.entry_base, item.entry_base.title, "—")),
        rx.table.cell(rx.cond(item.form_of_study, item.form_of_study.title, "—")),
        rx.table.cell(item.budget_places),
        rx.table.cell(item.contract_places),
        rx.table.cell(item.budget_places + item.contract_places),
    )


def _view_quotas_section() -> rx.Component:
    return rx.vstack(
        rx.heading("Спеціальності та квоти", size="3"),
        rx.cond(
            ViewAdmissionCampaignState.quotas.length() > 0,
            rx.table.root(
                _quotas_header("Спеціальність", "База вступу", "Форма навчання", "Бюджет", "Контракт", "Всього"),
                rx.table.body(rx.foreach(ViewAdmissionCampaignState.quotas, _view_quota_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        spacing="2",
        align="stretch",
        width="100%",
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
        _view_quotas_section(),
        spacing="3",
        align="stretch",
        height="100%",
        width="100%",
    )


# ---------- Add / Edit form helpers ----------

def _form_quota_row_factory(form_state):
    def _row(item: AdmissionCampaignSpecialityModel, idx: int) -> rx.Component:
        return rx.table.row(
            rx.table.row_header_cell(
                form_state.speciality_labels[item.id_speciality.to_string()],
                align="left",
            ),
            rx.table.cell(form_state.entry_base_labels[item.id_entry_base.to_string()]),
            rx.table.cell(form_state.form_labels[item.id_form_of_study.to_string()]),
            rx.table.cell(item.budget_places),
            rx.table.cell(item.contract_places),
            rx.table.cell(item.budget_places + item.contract_places),
            rx.table.cell(
                rx.hstack(
                    controls.button_image_primary(
                        name_icon="pencil_line",
                        on_click=form_state.open_q_edit(idx),
                    ),
                    controls.delete_with_confirm(
                        on_confirm=form_state.delete_q(idx),
                        description="Видалити цю спеціальність з кампанії?",
                    ),
                    spacing="2",
                )
            ),
        )

    return _row


def _form_quotas_section(form_state) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Спеціальності та квоти", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=form_state.open_q_add),
            width="100%",
        ),
        rx.cond(
            form_state.quotas.length() > 0,
            rx.table.root(
                _quotas_header("Спеціальність", "База вступу", "Форма навчання", "Бюджет", "Контракт", "Всього", "Дії"),
                rx.table.body(rx.foreach(form_state.quotas, _form_quota_row_factory(form_state))),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def _quota_dialog(form_state) -> rx.Component:
    # Поле спеціальності неактивне лише при редагуванні існуючої квоти (q_index >= 0).
    # При додаванні нової квоти (в т.ч. на сторінці редагування кампанії) — звичайний select.
    speciality_field = rx.cond(
        form_state.q_index >= 0,
        rx.input(
            value=form_state.speciality_labels[form_state.q_speciality_combined],
            disabled=True,
            width="100%",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Оберіть спеціальність"),
            rx.select.content(
                rx.foreach(form_state.speciality_options, _select_item),
            ),
            value=form_state.q_speciality_combined,
            on_change=form_state.set_q_speciality_combined,
            width="100%",
        ),
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Спеціальність та квоти"),
            rx.vstack(
                rx.text("*Спеціальність:"),
                speciality_field,
                rx.text("*База вступу:"),
                rx.select.root(
                    rx.select.trigger(placeholder="Оберіть базу вступу"),
                    rx.select.content(
                        rx.foreach(form_state.entry_base_options, _select_item),
                    ),
                    value=form_state.q_id_entry_base_str,
                    on_change=form_state.set_q_id_entry_base,
                    width="100%",
                ),
                rx.text("*Форма навчання:"),
                rx.select.root(
                    rx.select.trigger(placeholder="Оберіть форму навчання"),
                    rx.select.content(
                        rx.foreach(form_state.form_of_study_options, _select_item),
                    ),
                    value=form_state.q_id_form_of_study_str,
                    on_change=form_state.set_q_id_form_of_study,
                    width="100%",
                ),
                rx.text("*Бюджетних місць:"),
                rx.input(
                    type="number",
                    value=form_state.q_budget_places.to_string(),
                    on_change=form_state.set_q_budget_places,
                    width="100%",
                ),
                rx.text("*Контрактних місць:"),
                rx.input(
                    type="number",
                    value=form_state.q_contract_places.to_string(),
                    on_change=form_state.set_q_contract_places,
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        controls.button_secondary("Скасувати", on_click=form_state.close_q),
                    ),
                    controls.button_primary("Зберегти", on_click=form_state.save_q),
                    justify="end",
                    spacing="2",
                    width="100%",
                ),
                spacing="2",
                align="stretch",
            ),
        ),
        open=form_state.q_open,
        on_open_change=form_state.set_q_open,
    )


# ---------- Add page ----------

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
        _form_quotas_section(AddAdmissionCampaignState),
        _quota_dialog(AddAdmissionCampaignState),
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
        _form_quotas_section(EditAdmissionCampaignState),
        _quota_dialog(EditAdmissionCampaignState),
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
        on_mount=ListAdmissionCampaignState.on_load,
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
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewAdmissionCampaignState.in_process, height="100%"),
            audit_history_section("admission_campaigns"),
            width="100%",
            align="stretch",
            spacing="4",
        ),
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
