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
        rx.hstack(
            rx.heading(group.spec_label, size="4"),
            rx.spacer(),
            rx.cond(
                ListRatingState.get_user_actions.contains(Actions.RATING_DOCX),
                controls.button_image_secondary(
                    name_icon="file-down",
                    on_click=ListRatingState.on_click_download_group(group.spec_key),
                ),
            ),
            width="100%",
            align="center",
        ),
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


def _filter_field(label: str, placeholder: str, options, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, weight="bold", size="2"),
        rx.select.root(
            rx.select.trigger(placeholder=placeholder),
            rx.select.content(rx.foreach(options, _select_item)),
            value=value,
            on_change=on_change,
            width="100%",
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


def _generated_text() -> rx.Component:
    return rx.cond(
        ListRatingState.generated_at_display != "",
        rx.text(
            "Останнє формування: ",
            rx.text.strong(ListRatingState.generated_at_display),
            size="2",
            color="gray",
        ),
        rx.text("Рейтинг ще не формувався для цієї кампанії", size="2", color="gray"),
    )


def _generate_button() -> rx.Component:
    return rx.cond(
        ListRatingState.get_user_actions.contains(Actions.RATING_GENERATE),
        controls.button_primary(
            rx.icon("refresh-cw", size=18),
            "Сформувати рейтинг",
            on_click=ListRatingState.on_click_generate,
            loading=ListRatingState.generating,
        ),
    )


def _download_all_button() -> rx.Component:
    # Завантаження доступне лише коли є що завантажувати (рейтинг сформовано).
    return rx.cond(
        ListRatingState.get_user_actions.contains(Actions.RATING_DOCX)
        & (ListRatingState.groups.length() > 0),
        controls.button_secondary(
            rx.icon("file-down", size=18),
            "Завантажити DOCX",
            on_click=ListRatingState.on_click_download_all,
            loading=ListRatingState.downloading,
        ),
    )


def _filters_grid() -> rx.Component:
    """Поля фільтрів у сітці 2×2."""
    return rx.grid(
        _filter_field(
            "Вступна кампанія:", "Оберіть кампанію",
            ListRatingState.campaign_options,
            ListRatingState.selected_campaign_id_str,
            ListRatingState.set_selected_campaign_id,
        ),
        _filter_field(
            "Спеціальність:", "Усі спеціальності",
            ListRatingState.speciality_options,
            ListRatingState.selected_spec_key,
            ListRatingState.set_selected_spec_key,
        ),
        _filter_field(
            "База вступу:", "Усі бази вступу",
            ListRatingState.base_filter_options,
            ListRatingState.selected_base_key,
            ListRatingState.set_selected_base_key,
        ),
        _filter_field(
            "Форма навчання:", "Усі форми навчання",
            ListRatingState.form_filter_options,
            ListRatingState.selected_form_key,
            ListRatingState.set_selected_form_key,
        ),
        columns="2",
        spacing="3",
        width="100%",
    )


def _controls_panel_expanded() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Фільтри", weight="bold", size="3"),
            rx.spacer(),
            controls.button_image_secondary(
                name_icon="chevrons-down-up",
                on_click=ListRatingState.toggle_filter_collapsed,
            ),
            width="100%",
            align="center",
        ),
        _filters_grid(),
        rx.hstack(
            _generated_text(),
            rx.spacer(),
            _download_all_button(),
            _generate_button(),
            spacing="3",
            width="100%",
            align="center",
            wrap="wrap",
        ),
        _legend(),
        spacing="3",
        align="stretch",
        width="100%",
    )


def _controls_panel_collapsed() -> rx.Component:
    """Згорнутий вид: лише маркери, дата формування та кнопка розгортання."""
    return rx.hstack(
        _legend(),
        rx.spacer(),
        _generated_text(),
        controls.button_image_secondary(
            name_icon="chevrons-up-down",
            on_click=ListRatingState.toggle_filter_collapsed,
        ),
        width="100%",
        align="center",
        spacing="3",
        wrap="wrap",
    )


def _controls_panel() -> rx.Component:
    return rx.box(
        rx.cond(
            ListRatingState.filter_collapsed,
            _controls_panel_collapsed(),
            _controls_panel_expanded(),
        ),
        padding="1rem",
        border_radius="0.6rem",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        width="100%",
    )


def list_page_content() -> rx.Component:
    return rx.vstack(
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
    # Карта з кампанією/спеціальністю/кнопкою генерації — поза скелетоном,
    # щоб не «мерехтіла» при перезавантаженні групи.
    return page_wrapper(
        header_subpage(
            "Рейтинговий список",
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListRatingState.in_progress, height="100%"),
        filter_panel=_controls_panel(),
        on_mount=ListRatingState.on_load,
    )
