import reflex as rx

from typing import Dict

from Dekanat.actions import Actions
from Dekanat.states.rating import ListRatingState, RatingGroup

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


# Кольорова кодировка статусів (фон рядка)
_STATUS_BG = {
    "budget": "rgba(34, 197, 94, 0.18)",   # зелений
    "contract": "rgba(249, 115, 22, 0.18)", # помаранчевий
    "rejected": "rgba(239, 68, 68, 0.20)",  # червоний
    "kvota": "rgba(59, 130, 246, 0.20)",    # синій
}

_STATUS_LABEL = {
    "budget": "Бюджет",
    "contract": "Контракт",
    "rejected": "Не проходить",
    "kvota": "Квота",
}


def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


def _row_bg(status):
    return rx.match(
        status,
        ("budget", _STATUS_BG["budget"]),
        ("contract", _STATUS_BG["contract"]),
        ("kvota", _STATUS_BG["kvota"]),
        ("rejected", _STATUS_BG["rejected"]),
        "transparent",
    )


def _row_status_label(status):
    return rx.match(
        status,
        ("budget", _STATUS_LABEL["budget"]),
        ("contract", _STATUS_LABEL["contract"]),
        ("kvota", _STATUS_LABEL["kvota"]),
        ("rejected", _STATUS_LABEL["rejected"]),
        "",
    )


def _rating_row(item: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(item["position"], align="left"),
        rx.table.cell(item["pib"]),
        rx.table.cell(item["total"]),
        rx.table.cell(_row_status_label(item["status"])),
        background_color=_row_bg(item["status"]),
    )


def _group_table(group: RatingGroup) -> rx.Component:
    return rx.vstack(
        rx.heading(group.spec_label, size="4"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("№", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Сума балів", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Статус", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(group.rows, _rating_row)),
            variant="surface",
            width="100%",
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def _legend() -> rx.Component:
    def _pill(label: str, color: str) -> rx.Component:
        return rx.hstack(
            rx.box(width="0.9rem", height="0.9rem", border_radius="0.2rem", background_color=color),
            rx.text(label, size="2"),
            spacing="2",
            align="center",
        )

    return rx.hstack(
        _pill("Бюджет", _STATUS_BG["budget"]),
        _pill("Контракт", _STATUS_BG["contract"]),
        _pill("Квота", _STATUS_BG["kvota"]),
        _pill("Не проходить", _STATUS_BG["rejected"]),
        spacing="4",
        wrap="wrap",
    )


def _controls_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Вступна кампанія:", weight="bold"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Оберіть кампанію"),
                        rx.select.content(
                            rx.foreach(ListRatingState.campaign_options, _select_item),
                        ),
                        value=ListRatingState.selected_campaign_id_str,
                        on_change=ListRatingState.set_selected_campaign_id,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Спеціальність:", weight="bold"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Усі спеціальності"),
                        rx.select.content(
                            rx.foreach(ListRatingState.speciality_options, _select_item),
                        ),
                        value=ListRatingState.selected_spec_key,
                        on_change=ListRatingState.set_selected_spec_key,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                spacing="3",
                align="end",
                width="100%",
            ),
            rx.hstack(
                rx.cond(
                    ListRatingState.generated_at_display != "",
                    rx.text(
                        "Останнє формування: ",
                        rx.text.strong(ListRatingState.generated_at_display),
                        size="2",
                        color="gray",
                    ),
                    rx.text("Рейтинг ще не формувався для цієї кампанії", size="2", color="gray"),
                ),
                rx.spacer(),
                rx.cond(
                    ListRatingState.get_user_actions.contains(Actions.RATING_GENERATE),
                    controls.button_primary(
                        rx.icon("refresh-cw", size=18),
                        "Сформувати рейтинг",
                        on_click=ListRatingState.on_click_generate,
                        loading=ListRatingState.generating,
                    ),
                ),
                width="100%",
                align="center",
            ),
            _legend(),
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


def list_page_content() -> rx.Component:
    return rx.vstack(
        _controls_panel(),
        rx.cond(
            ListRatingState.groups.length() > 0,
            rx.vstack(
                rx.foreach(ListRatingState.groups, _group_table),
                spacing="5",
                align="stretch",
                width="100%",
            ),
            controls.empty_placeholder("Рейтинг порожній. Натисніть «Сформувати рейтинг»."),
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Рейтинговий список",
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListRatingState.in_progress, height="100%"),
    )
