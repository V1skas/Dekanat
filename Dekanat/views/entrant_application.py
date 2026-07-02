import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.states.entrant_application import ListEntrantApplicationState
from Dekanat.services.entrant_application import EntrantApplicationRow

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


State = ListEntrantApplicationState


# ============================================================
# Helpers
# ============================================================

def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


def _select(options, value, on_change, placeholder: str = "Оберіть зі списку", **kw) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder=placeholder),
        rx.select.content(
            rx.foreach(options, _select_item),
        ),
        value=value,
        on_change=on_change,
        **kw,
    )


# ============================================================
# List table
# ============================================================

def _plain_header(title: str) -> rx.Component:
    return rx.table.column_header_cell(title, color=rx.color("accent", 2))


def _sortable_header(title: str, field: str) -> rx.Component:
    """Кликабельний заголовок столбця з індикатором сортування (↑/↓)."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(title, color=rx.color("accent", 2)),
            rx.text(
                State.sort_indicator[field],
                color=rx.color("accent", 2),
                weight="bold",
            ),
            spacing="1",
            align="center",
        ),
        color=rx.color("accent", 2),
        cursor="pointer",
        on_click=State.on_click_sort(field),
        _hover={"background_color": rx.color("accent", 10)},
    )


def _row(item: EntrantApplicationRow) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(
                item.pib,
                href=f"{routes.ENTRANT_VIEW}{item.entrant_id}?from=applications",
            ),
            align="left",
        ),
        rx.table.cell(rx.cond(item.created_at != "", item.created_at, "—")),
        rx.table.cell(rx.cond(item.phone_number != "", item.phone_number, "—")),
        rx.table.cell(rx.cond(item.email != "", item.email, "—")),
        rx.table.cell(rx.cond(item.entry_base != "", item.entry_base, "—")),
        rx.table.cell(rx.cond(item.source_of_funding != "", item.source_of_funding, "—")),
        rx.table.cell(item.priority),
        rx.table.cell(item.speciality),
        rx.table.cell(rx.cond(item.application_status != "", item.application_status, "—")),
    )


def _table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                _sortable_header("ПІБ", "pib"),
                _plain_header("Дата створення"),
                _plain_header("Номер телефону"),
                _plain_header("Електронна пошта"),
                _plain_header("База вступу"),
                _plain_header("Джерело фінансування"),
                _sortable_header("Пріоритет", "priority"),
                _sortable_header("Спеціальність", "speciality"),
                _plain_header("Статус заяви"),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(State.items, _row),
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
            State.items.is_not_none() & (State.items.length() > 0),
            _table(),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


# ============================================================
# Filter panel
# ============================================================

def _filter_field(label: str, control: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, weight="medium"),
        control,
        spacing="1",
        align="stretch",
        width="100%",
    )


def _date_filter() -> rx.Component:
    return rx.vstack(
        rx.text("Дата створення:", weight="medium"),
        rx.radio(
            ["День", "Період"],
            value=rx.cond(State.is_date_mode_period, "Період", "День"),
            on_change=State.set_filter_date_mode,
            direction="row",
            spacing="4",
        ),
        rx.cond(
            State.is_date_mode_period,
            rx.hstack(
                rx.vstack(
                    rx.text("З:", size="2"),
                    rx.input(
                        type="date",
                        value=State.filter_date_from,
                        on_change=State.set_filter_date_from,
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
                        value=State.filter_date_to,
                        on_change=State.set_filter_date_to,
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
                value=State.filter_date_day,
                on_change=State.set_filter_date_day,
                width="100%",
            ),
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


def _filter_panel() -> rx.Component:
    return controls.filter_panel(
        State.filter_open,
        rx.grid(
            _filter_field(
                "Вступна кампанія:",
                _select(
                    State.campaign_options,
                    State.filter_campaign_id_str,
                    State.set_filter_campaign_id,
                    placeholder="— Без фільтра —",
                    width="100%",
                ),
            ),
            _filter_field(
                "ПІБ містить:",
                rx.input(
                    value=State.filter_pib,
                    on_change=State.set_filter_pib,
                    placeholder="Пошук по ПІБ…",
                    width="100%",
                ),
            ),
            _filter_field(
                "Номер телефону містить:",
                rx.input(
                    value=State.filter_phone,
                    on_change=State.set_filter_phone,
                    placeholder="Пошук по телефону…",
                    width="100%",
                ),
            ),
            _filter_field(
                "Статус заяви:",
                _select(
                    State.application_status_options,
                    State.filter_status_id_str,
                    State.set_filter_status_id,
                    placeholder="Будь-який",
                    width="100%",
                ),
            ),
            _filter_field(
                "База вступу:",
                _select(
                    State.entry_base_options,
                    State.filter_entry_base_id_str,
                    State.set_filter_entry_base_id,
                    placeholder="Будь-яка",
                    width="100%",
                ),
            ),
            _filter_field(
                "Спеціальність у пріоритетах:",
                _select(
                    State.speciality_options,
                    State.filter_speciality_key,
                    State.set_filter_speciality_key,
                    placeholder="Будь-яка",
                    width="100%",
                ),
            ),
            _filter_field(
                "Пріоритетна спеціальність (№1):",
                _select(
                    State.speciality_options,
                    State.filter_top_speciality_key,
                    State.set_filter_top_speciality_key,
                    placeholder="Будь-яка",
                    width="100%",
                ),
            ),
            _date_filter(),
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            spacing="3",
            width="100%",
            align="start",
        ),
        on_clear=State.clear_filters,
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Заявки",
            controls.button_filter_toggle(State.filter_open, on_click=State.toggle_filter),
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=State.in_progress, height="100%"),
        filter_panel=_filter_panel(),
        on_mount=State.on_load,
    )
