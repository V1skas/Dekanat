import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entrants_group import (
    ListEntrantsGroupState,
    AddEntrantsGroupState,
    EditEntrantsGroupState,
    ViewEntrantsGroupState,
)
from Dekanat.models import EntrantGroupModel, EntrantModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


# ============================================================
# List page
# ============================================================

def _list_row(item: EntrantGroupModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ENTRANTS_GROUP_VIEW}{item.id}"),
            align="left"
        ),
    )

def _list_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListEntrantsGroupState.items, _list_row),
            height="100%",
            width="100%"
        ),
        variant="surface",
        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListEntrantsGroupState.items.is_not_none() & (ListEntrantsGroupState.items.length() > 0),
                _list_table(),
                controls.empty_placeholder()),
    )


def _list_filter_panel() -> rx.Component:
    return controls.filter_panel(
        ListEntrantsGroupState.filter_open,
        rx.vstack(
            rx.text("Вступна кампанія:", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder="— Без фільтра —"),
                rx.select.content(
                    rx.foreach(
                        ListEntrantsGroupState.campaign_options,
                        lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                    ),
                ),
                value=ListEntrantsGroupState.filter_campaign_id_str,
                on_change=ListEntrantsGroupState.set_filter_campaign_id,
                width="100%",
            ),
            spacing="1",
            align="stretch",
            width="100%",
        ),
        rx.vstack(
            rx.text("Назва містить:", weight="medium"),
            rx.input(
                value=ListEntrantsGroupState.filter_title,
                on_change=ListEntrantsGroupState.set_filter_title,
                placeholder="Пошук по назві…",
                width="100%",
            ),
            spacing="1",
            align="stretch",
            width="100%",
        ),
        on_clear=ListEntrantsGroupState.clear_filters,
    )


# ============================================================
# Common helpers (entrants table in form / view)
# ============================================================

def _entrants_form_row_factory(remove_event):
    def _row(item: EntrantModel, idx: int) -> rx.Component:
        return rx.table.row(
            rx.table.cell(rx.cond(item.person, item.person.pib, "—")),
            rx.table.cell(rx.cond(item.person, item.person.phone_number, "—")),
            rx.table.cell(rx.cond(item.person, rx.cond(item.person.email, item.person.email, "—"), "—")),
            rx.table.cell(
                controls.delete_with_confirm(
                    on_confirm=remove_event(idx),
                    description="Прибрати цього абітурієнта зі складу групи?",
                ),
            ),
        )
    return _row


def _entrants_form_table(items, remove_event) -> rx.Component:
    return rx.cond(
        items.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Телефон", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("E-mail", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дії", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(
                rx.foreach(items, _entrants_form_row_factory(remove_event)),
            ),
            variant="surface",
            width="100%",
        ),
        controls.empty_placeholder("До групи ще не додано жодного абітурієнта"),
    )


def _add_entrant_dialog(rows_var, search_value, set_search, pick_entrant, on_close, is_open) -> rx.Component:
    def _row(opt: Dict[str, str]) -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.text(opt["label"], weight="bold"),
                rx.cond(opt["subtitle"], rx.text(opt["subtitle"], size="1", color="gray")),
                spacing="0",
                align="start",
            ),
            on_click=pick_entrant(opt["value"]),
            cursor="pointer",
            padding="0.5rem 0.75rem",
            border_radius="0.5rem",
            width="100%",
            _hover={"background_color": rx.color("accent", 3)},
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Додавання абітурієнта до групи"),
            rx.vstack(
                rx.input(
                    placeholder="Пошук за ПІБ або телефоном…",
                    value=search_value,
                    on_change=set_search,
                    width="100%",
                ),
                rx.cond(
                    rows_var.length() > 0,
                    rx.vstack(
                        rx.foreach(rows_var, _row),
                        spacing="1",
                        max_height="22rem",
                        overflow_y="auto",
                        width="100%",
                    ),
                    rx.text("Збігів не знайдено", color="gray"),
                ),
                rx.hstack(
                    rx.dialog.close(controls.button_secondary("Закрити", on_click=on_close)),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                align="stretch",
            ),
        ),
        open=is_open,
    )


# ============================================================
# View page
# ============================================================

def _view_entrant_row(item: EntrantModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(
                rx.cond(item.person, item.person.pib, "—"),
                href=f"{routes.ENTRANT_VIEW}{item.id}",
            ),
            align="left",
        ),
        rx.table.cell(rx.cond(item.person, item.person.phone_number, "—")),
        rx.table.cell(rx.cond(item.person, rx.cond(item.person.email, item.person.email, "—"), "—")),
    )


def _view_entrants_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Телефон", color=rx.color("accent", 2)),
                rx.table.column_header_cell("E-mail", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(rx.foreach(ViewEntrantsGroupState.entrants_in_group, _view_entrant_row)),
        variant="surface",
        width="100%",
    )


def _view_exam_row(row: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["subject"]),
        rx.table.cell(row["date_time"]),
    )


def _view_exams_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Предмет", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Дата та час", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(rx.foreach(ViewEntrantsGroupState.exams_display, _view_exam_row)),
        variant="surface",
        width="100%",
    )


def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewEntrantsGroupState.title, size="6"),

        rx.heading("Абітурієнти у групі", size="4"),
        rx.cond(
            ViewEntrantsGroupState.entrants_in_group.length() > 0,
            _view_entrants_table(),
            controls.empty_placeholder("До групи ще не додано жодного абітурієнта"),
        ),

        rx.heading("Розклад іспитів", size="4"),
        rx.cond(
            ViewEntrantsGroupState.exams.length() > 0,
            _view_exams_table(),
            controls.empty_placeholder("Іспити для цієї групи ще не призначені"),
        ),

        spacing="4",
        align="stretch",
        width="100%",
    )


# ============================================================
# Add page
# ============================================================

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(
            id="title",
            required=True,
            value=AddEntrantsGroupState.title,
            on_change=AddEntrantsGroupState.set_title,
            width="100%",
        ),

        rx.hstack(
            rx.heading("Абітурієнти у групі", size="4"),
            rx.spacer(),
            controls.button_image_primary(
                name_icon="plus",
                on_click=AddEntrantsGroupState.open_add_entrant_dialog,
            ),
            width="100%",
            align="center",
        ),
        _entrants_form_table(
            AddEntrantsGroupState.entrants_in_group,
            AddEntrantsGroupState.remove_entrant_from_group,
        ),

        _add_entrant_dialog(
            AddEntrantsGroupState.available_to_add_rows,
            AddEntrantsGroupState.add_entrant_dialog_search,
            AddEntrantsGroupState.set_add_entrant_dialog_search,
            AddEntrantsGroupState.pick_entrant_to_add,
            AddEntrantsGroupState.close_add_entrant_dialog,
            AddEntrantsGroupState.add_entrant_dialog_open,
        ),

        align="stretch",
        spacing="3",
        width="100%",
    )


# ============================================================
# Edit page
# ============================================================

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(
            id="title",
            required=True,
            value=EditEntrantsGroupState.title,
            on_change=EditEntrantsGroupState.set_title,
            width="100%",
        ),

        rx.hstack(
            rx.heading("Абітурієнти у групі", size="4"),
            rx.spacer(),
            controls.button_image_primary(
                name_icon="plus",
                on_click=EditEntrantsGroupState.open_add_entrant_dialog,
            ),
            width="100%",
            align="center",
        ),
        _entrants_form_table(
            EditEntrantsGroupState.entrants_in_group,
            EditEntrantsGroupState.remove_entrant_from_group,
        ),

        _add_entrant_dialog(
            EditEntrantsGroupState.available_to_add_rows,
            EditEntrantsGroupState.add_entrant_dialog_search,
            EditEntrantsGroupState.set_add_entrant_dialog_search,
            EditEntrantsGroupState.pick_entrant_to_add,
            EditEntrantsGroupState.close_add_entrant_dialog,
            EditEntrantsGroupState.add_entrant_dialog_open,
        ),

        align="stretch",
        spacing="3",
        width="100%",
    )


# ============================================================
# Pages
# ============================================================

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            controls.button_filter_toggle(ListEntrantsGroupState.filter_open, on_click=ListEntrantsGroupState.toggle_filter),
            rx.cond(ListEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_ADD),
                    controls.button_image_primary(name_icon="plus", on_click=ListEntrantsGroupState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListEntrantsGroupState.in_progress, height="100%"),
        filter_panel=_list_filter_panel(),
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_DELETE),
                    controls.delete_with_confirm(on_confirm=ViewEntrantsGroupState.on_click_delete)),
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntrantsGroupState.on_click_edit)),
            left=controls.button_back(routes.ENTRANTS_GROUP_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewEntrantsGroupState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddEntrantsGroupState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddEntrantsGroupState.on_save),
            width="100%"
        ),
        rx.skeleton(add_page_content(), loading=AddEntrantsGroupState.in_process, height="100%"),
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditEntrantsGroupState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditEntrantsGroupState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditEntrantsGroupState.in_process, height="100%")
    )
