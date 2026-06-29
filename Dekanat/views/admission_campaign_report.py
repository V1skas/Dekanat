import reflex as rx

from typing import Dict

from Dekanat.actions import Actions
from Dekanat.states.admission_campaign_report import ListAdmissionReportState

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


# Кольори для двох серій (primary / compare) — використовуються у Bar/Line.
_COLOR_PRIMARY = "#7f4a25"   # під фірмовий brown
_COLOR_COMPARE = "#3b82f6"   # синій

# Палітра для секторів pie. Більше за кількість бакетів — обертаємось по модулю.
_PIE_PALETTE = [
    "#7f4a25", "#3b82f6", "#22c55e", "#f97316", "#a855f7",
    "#ef4444", "#06b6d4", "#84cc16", "#eab308", "#ec4899",
]


def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


def _controls_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("Вступна кампанія:", weight="bold"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Оберіть кампанію"),
                        rx.select.content(rx.foreach(ListAdmissionReportState.campaign_options, _select_item)),
                        value=ListAdmissionReportState.selected_campaign_id_str,
                        on_change=ListAdmissionReportState.set_selected_campaign_id,
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Порівняти з:", weight="bold"),
                    rx.select.root(
                        rx.select.trigger(placeholder="— Без порівняння —"),
                        rx.select.content(rx.foreach(ListAdmissionReportState.compare_options, _select_item)),
                        value=ListAdmissionReportState.compare_campaign_id_str,
                        on_change=ListAdmissionReportState.set_compare_campaign_id,
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
                    ListAdmissionReportState.has_report,
                    rx.text(
                        "Останнє формування: ",
                        rx.text.strong(ListAdmissionReportState.primary_generated_at),
                        size="2",
                        color="gray",
                    ),
                    rx.text("Звіт ще не сформовано для цієї кампанії", size="2", color="gray"),
                ),
                rx.spacer(),
                rx.cond(
                    ListAdmissionReportState.get_user_actions.contains(Actions.REPORT_ADMISSION_GENERATE),
                    controls.button_primary(
                        rx.icon("refresh-cw", size=18),
                        "Сформувати звіт",
                        on_click=ListAdmissionReportState.on_click_generate,
                        loading=ListAdmissionReportState.generating,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                ListAdmissionReportState.has_compare,
                rx.text(
                    "Порівняння: ",
                    rx.cond(
                        ListAdmissionReportState.compare_has_report,
                        rx.text.strong(ListAdmissionReportState.compare_generated_at),
                        rx.text.em("звіт ще не сформовано"),
                    ),
                    size="2",
                    color="gray",
                ),
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


def _totals_card(label: str, primary_value, compare_value, accent: bool = False) -> rx.Component:
    """Карточка з великим числом основної кампанії + (опційно) значенням порівняння."""
    return rx.box(
        rx.vstack(
            rx.text(label, size="2", color="gray"),
            rx.heading(primary_value.to_string(), size="7", color=_COLOR_PRIMARY),
            rx.cond(
                ListAdmissionReportState.has_compare,
                rx.text(
                    "vs ",
                    rx.text.strong(compare_value.to_string(), color=_COLOR_COMPARE),
                    size="2",
                    color="gray",
                ),
            ),
            spacing="1",
            align="start",
        ),
        padding="1rem",
        border_radius="0.6rem",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        width="14rem",
        height="100%",
    )


def _totals_row() -> rx.Component:
    return rx.hstack(
        _totals_card("За сьогодні", ListAdmissionReportState.total_today_primary, ListAdmissionReportState.total_today_compare),
        _totals_card("За тиждень", ListAdmissionReportState.total_week_primary, ListAdmissionReportState.total_week_compare),
        _totals_card("За весь період", ListAdmissionReportState.total_period_primary, ListAdmissionReportState.total_period_compare),
        spacing="3",
        wrap="wrap",
        width="100%",
    )


def _day_bar_chart() -> rx.Component:
    return rx.recharts.bar_chart(
        rx.recharts.bar(data_key="primary", fill=_COLOR_PRIMARY, name="Основна"),
        rx.cond(
            ListAdmissionReportState.has_compare,
            rx.recharts.bar(data_key="compare", fill=_COLOR_COMPARE, name="Порівняння"),
        ),
        rx.recharts.x_axis(data_key="label"),
        rx.recharts.y_axis(allow_decimals=False),
        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
        rx.recharts.graphing_tooltip(),
        rx.recharts.legend(),
        data=ListAdmissionReportState.day_bar_data,
        height=260,
        width="100%",
    )


def _line_chart(data_var) -> rx.Component:
    return rx.recharts.line_chart(
        rx.recharts.line(data_key="primary", stroke=_COLOR_PRIMARY, name="Основна", type_="monotone"),
        rx.cond(
            ListAdmissionReportState.has_compare,
            rx.recharts.line(data_key="compare", stroke=_COLOR_COMPARE, name="Порівняння", type_="monotone"),
        ),
        rx.recharts.x_axis(data_key="date"),
        rx.recharts.y_axis(allow_decimals=False),
        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
        rx.recharts.graphing_tooltip(),
        rx.recharts.legend(),
        data=data_var,
        height=300,
        width="100%",
    )


def _pie_cell(item: Dict, index: int) -> rx.Component:
    # `index` тут — Reflex Var; звичайний Python-індекс по списку palette не
    # спрацює. Конвертуємо палітру у Var і робимо modulo через Var-операції.
    palette = rx.Var.create(_PIE_PALETTE)
    return rx.recharts.cell(fill=palette[index % len(_PIE_PALETTE)])


def _pie_chart(data_var) -> rx.Component:
    return rx.recharts.pie_chart(
        rx.recharts.pie(
            rx.foreach(data_var, _pie_cell),
            data=data_var,
            data_key="value",
            name_key="name",
            outer_radius=110,
        ),
        rx.recharts.graphing_tooltip(),
        rx.recharts.legend(),
        height=320,
        width="100%",
    )


def _spec_count_row(item: Dict) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(item["name"], align="left"),
        rx.table.cell(item["value"].to_string()),
    )


def _spec_count_table(data_var) -> rx.Component:
    """Текстова таблиця «спеціальність → кількість» — дублюємо те, що показує pie,
    щоб користувач бачив точні числа без наведення на сектор."""
    return rx.cond(
        data_var.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Спеціальність", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Кількість", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(data_var, _spec_count_row)),
            variant="surface",
            width="100%",
        ),
        rx.text("Немає даних", color="gray", size="2"),
    )


def _pie_with_list(data_var) -> rx.Component:
    return rx.vstack(
        _pie_chart(data_var),
        _spec_count_table(data_var),
        spacing="3",
        align="stretch",
        width="100%",
    )


def _chart_block(title: str, body: rx.Component) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(title, size="4"),
            body,
            spacing="2",
            align="stretch",
            width="100%",
        ),
        padding="1rem",
        border_radius="0.6rem",
        background_color=rx.color("gray", 2),
        border=f"1px solid {rx.color('gray', 5)}",
        width="100%",
    )


def _spec_section() -> rx.Component:
    return rx.cond(
        ListAdmissionReportState.has_compare,
        rx.vstack(
            rx.hstack(
                _chart_block(
                    "За приоритетной специальностью (основна)",
                    _pie_with_list(ListAdmissionReportState.spec_top_primary),
                ),
                _chart_block(
                    "За приоритетной специальностью (порівняння)",
                    _pie_with_list(ListAdmissionReportState.spec_top_compare),
                ),
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            rx.hstack(
                _chart_block(
                    "За будь-яким пріоритетом (основна)",
                    _pie_with_list(ListAdmissionReportState.spec_any_primary),
                ),
                _chart_block(
                    "За будь-яким пріоритетом (порівняння)",
                    _pie_with_list(ListAdmissionReportState.spec_any_compare),
                ),
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        rx.vstack(
            _chart_block(
                "За приоритетной специальностью",
                _pie_with_list(ListAdmissionReportState.spec_top_primary),
            ),
            _chart_block(
                "За будь-яким пріоритетом",
                _pie_with_list(ListAdmissionReportState.spec_any_primary),
            ),
            spacing="3",
            align="stretch",
            width="100%",
        ),
    )


def _labeled_count_table(data_var, head_label: str) -> rx.Component:
    return rx.cond(
        data_var.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(head_label, color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Кількість", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(data_var, _spec_count_row)),
            variant="surface",
            width="100%",
        ),
        rx.text("Немає даних", color="gray", size="2"),
    )


def _pie_with_labeled_list(data_var, head_label: str) -> rx.Component:
    return rx.vstack(
        _pie_chart(data_var),
        _labeled_count_table(data_var, head_label),
        spacing="3",
        align="stretch",
        width="100%",
    )


def _dk26_section() -> rx.Component:
    """Розділи DK-26: розподіл по базах вступу та формах навчання, а також
    загальні підсумки по специальностях (з розрізненням бази/форми) і по відділеннях."""
    return rx.vstack(
        rx.hstack(
            _chart_block(
                "За базою вступу",
                _pie_with_labeled_list(ListAdmissionReportState.by_entry_base_primary, "База вступу"),
            ),
            _chart_block(
                "За формою навчання",
                _pie_with_labeled_list(ListAdmissionReportState.by_form_primary, "Форма навчання"),
            ),
            spacing="3",
            wrap="wrap",
            width="100%",
        ),
        _chart_block(
            "Всього по специальностям (з урахуванням бази та форми)",
            _pie_with_labeled_list(ListAdmissionReportState.totals_by_spec_primary, "Спеціальність"),
        ),
        _chart_block(
            "Всього по відділеннях",
            _pie_with_labeled_list(ListAdmissionReportState.totals_by_department_primary, "Відділення"),
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


def _period_pill(label: str, is_active, on_click) -> rx.Component:
    """Один сегмент перемикача періоду: primary якщо активний, secondary інакше."""
    return rx.cond(
        is_active,
        controls.button_primary(label, on_click=on_click),
        controls.button_secondary(label, on_click=on_click),
    )


def _period_toggle() -> rx.Component:
    return rx.hstack(
        _period_pill("За сьогодні", ListAdmissionReportState.is_period_day, ListAdmissionReportState.set_selected_period("day")),
        _period_pill("За тиждень", ListAdmissionReportState.is_period_week, ListAdmissionReportState.set_selected_period("week")),
        _period_pill("За весь період", ListAdmissionReportState.is_period_period, ListAdmissionReportState.set_selected_period("period")),
        spacing="2",
        align="center",
    )


def _main_chart() -> rx.Component:
    """Один графік на блок «динаміка»: bar для дня, line для тижня/всього періоду."""
    return rx.match(
        ListAdmissionReportState.selected_period,
        ("day", _day_bar_chart()),
        ("week", _line_chart(ListAdmissionReportState.week_series_data)),
        ("period", _line_chart(ListAdmissionReportState.period_series_data)),
        _line_chart(ListAdmissionReportState.period_series_data),
    )


def _main_chart_title() -> rx.Component:
    return rx.match(
        ListAdmissionReportState.selected_period,
        ("day", rx.text("Динаміка за сьогодні")),
        ("week", rx.text("Динаміка за тиждень")),
        ("period", rx.text("Динаміка за весь період")),
        rx.text("Динаміка"),
    )


def _report_body() -> rx.Component:
    return rx.vstack(
        _totals_row(),
        # Перемикач періоду — впливає на головний графік і розподіл по специальностях.
        rx.box(
            _period_toggle(),
            padding="0.5rem",
            width="100%",
        ),
        _chart_block_dyn(_main_chart_title(), _main_chart()),
        _spec_section(),
        _dk26_section(),
        spacing="4",
        align="stretch",
        width="100%",
    )


def _chart_block_dyn(title_component: rx.Component, body: rx.Component) -> rx.Component:
    """Те саме що `_chart_block`, але приймає компонент-заголовок (для динамічної підписки)."""
    return rx.box(
        rx.vstack(
            rx.heading(title_component, size="4"),
            body,
            spacing="2",
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
        rx.cond(
            ListAdmissionReportState.has_report,
            _report_body(),
            controls.empty_placeholder(
                "Звіт ще не сформовано для цієї кампанії. Натисніть «Сформувати звіт»."
            ),
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage("Звіт приймальної кампанії", width="100%"),
        rx.skeleton(list_page_content(), loading=ListAdmissionReportState.in_progress, height="100%"),
        filter_panel=_controls_panel(),
        on_mount=ListAdmissionReportState.on_load,
    )
