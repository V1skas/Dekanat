import reflex as rx

from typing import Dict

from Dekanat.actions import Actions
from Dekanat.states.registration_journal import ListRegistrationJournalState

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


# Короткі підписи колонок для екрана (повні формулювання МОН — у DOCX-шаблоні).
_COLUMNS = [
    ("edbo", "№ заяви ЄДЕБО"),
    ("accepted_at", "Дата прийому"),
    ("pib", "ПІБ"),
    ("sex", "Стать"),
    ("birth_date", "Дата народж."),
    ("education", "Документ про освіту"),
    ("priority", "Пріоритетність"),
    ("zno", "Результати ЗНО"),
    ("refusal", "Причини відмови"),
    ("signature", "Підпис про повернення"),
]


def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


def _date_filter() -> rx.Component:
    """Перемикач «день / період» + відповідні поля (дефолт — порожньо = весь період)."""
    return rx.vstack(
        rx.text("Дата прийому:", weight="bold"),
        rx.radio(
            ["День", "Період"],
            value=rx.cond(ListRegistrationJournalState.is_date_mode_period, "Період", "День"),
            on_change=ListRegistrationJournalState.set_filter_date_mode,
            direction="row",
            spacing="4",
        ),
        rx.cond(
            ListRegistrationJournalState.is_date_mode_period,
            rx.hstack(
                rx.vstack(
                    rx.text("З:", size="2"),
                    rx.input(
                        type="date",
                        value=ListRegistrationJournalState.filter_date_from,
                        on_change=ListRegistrationJournalState.set_filter_date_from,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("По:", size="2"),
                    rx.input(
                        type="date",
                        value=ListRegistrationJournalState.filter_date_to,
                        on_change=ListRegistrationJournalState.set_filter_date_to,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.input(
                type="date",
                value=ListRegistrationJournalState.filter_date_day,
                on_change=ListRegistrationJournalState.set_filter_date_day,
                width="100%",
            ),
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


def _controls_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.grid(
                rx.vstack(
                    rx.text("Вступна кампанія:", weight="bold"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Оберіть кампанію"),
                        rx.select.content(
                            rx.foreach(ListRegistrationJournalState.campaign_options, _select_item)
                        ),
                        value=ListRegistrationJournalState.selected_campaign_id_str,
                        on_change=ListRegistrationJournalState.set_selected_campaign_id,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                _date_filter(),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="3",
                width="100%",
                align="start",
            ),
            rx.hstack(
                rx.text(
                    ListRegistrationJournalState.period_label,
                    " · заяв: ",
                    rx.text.strong(ListRegistrationJournalState.rows_count.to_string()),
                    size="2",
                    color="gray",
                ),
                rx.spacer(),
                rx.cond(
                    ListRegistrationJournalState.get_user_actions.contains(Actions.REPORT_JOURNAL_DOCX),
                    controls.button_primary(
                        rx.icon("download", size=18),
                        "Завантажити DOCX",
                        on_click=ListRegistrationJournalState.on_click_download,
                        loading=ListRegistrationJournalState.downloading,
                        disabled=~ListRegistrationJournalState.has_rows,
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        padding="1rem",
        border_radius="0.6rem",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        width="100%",
    )


def _header_cell(title: str) -> rx.Component:
    return rx.table.column_header_cell(title, color=rx.color("accent", 2), white_space="nowrap")


def _journal_row(r: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(r["edbo"], white_space="nowrap"),
        rx.table.cell(r["accepted_at"], white_space="nowrap"),
        rx.table.cell(r["pib"], white_space="nowrap"),
        rx.table.cell(r["sex"]),
        rx.table.cell(r["birth_date"], white_space="nowrap"),
        rx.table.cell(r["education"], min_width="16rem"),
        rx.table.cell(r["priority"], min_width="10rem"),
        rx.table.cell(r["zno"], min_width="10rem"),
        rx.table.cell(r["refusal"]),
        rx.table.cell(r["signature"]),
    )


def _journal_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[_header_cell(title) for _, title in _COLUMNS],
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(
                rx.foreach(ListRegistrationJournalState.rows, _journal_row),
            ),
            variant="surface",
            size="1",
            width="100%",
        ),
        overflow_x="auto",
        width="100%",
    )


def list_page_content() -> rx.Component:
    return rx.cond(
        ListRegistrationJournalState.has_rows,
        _journal_table(),
        controls.empty_placeholder(
            "За обраною кампанією та періодом немає зареєстрованих заяв."
        ),
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage("Журнал реєстрації заяв", width="100%"),
        rx.skeleton(list_page_content(), loading=ListRegistrationJournalState.in_progress, height="100%"),
        filter_panel=_controls_panel(),
        on_mount=ListRegistrationJournalState.on_load,
    )
