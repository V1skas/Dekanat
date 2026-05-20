import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entrant_exam import (
    ListEntrantExamState,
    AddEntrantExamState,
    EditEntrantExamState,
    ViewEntrantExamState,
    PrintEntrantExamState,
)

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


# ============================================================
# Shared helpers
# ============================================================

def _select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])


def _select(options, value, on_change, placeholder: str = "Оберіть зі списку", **kw) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder=placeholder),
        rx.select.content(rx.foreach(options, _select_item)),
        value=value,
        on_change=on_change,
        **kw,
    )


def _table_header(*titles: str) -> rx.Component:
    return rx.table.header(
        rx.table.row(*[rx.table.column_header_cell(t, color=rx.color("accent", 2)) for t in titles]),
        background_color=rx.color("accent", 9),
    )


# ============================================================
# List page
# ============================================================

def _list_row(row: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(row["group"], href=routes.ENTRANT_EXAM_VIEW + row["id"]),
            align="left",
        ),
        rx.table.cell(row["item_zno"]),
        rx.table.cell(row["date"]),
        rx.table.cell(row["time_start"]),
        rx.table.cell(row["time_end"]),
        rx.table.cell(row["workers"]),
    )


def _list_table() -> rx.Component:
    return rx.table.root(
        _table_header("Група", "Предмет", "Дата", "Початок", "Кінець", "Відповідальні"),
        rx.table.body(
            rx.foreach(ListEntrantExamState.items_display, _list_row),
            height="100%",
            width="100%",
        ),
        variant="surface",
        height="100%",
        width="100%",
    )


def _filter_panel() -> rx.Component:
    return controls.filter_panel(
        ListEntrantExamState.filter_open,
        rx.vstack(
            rx.text("Вступна кампанія:"),
            _select(
                ListEntrantExamState.campaign_options,
                ListEntrantExamState.filter_campaign_id_str,
                ListEntrantExamState.set_filter_campaign_id,
                width="100%",
            ),
            rx.text("Група:"),
            _select(
                ListEntrantExamState.group_options,
                ListEntrantExamState.filter_group_id_str,
                ListEntrantExamState.set_filter_group_id,
                width="100%",
            ),
            rx.text("Предмет:"),
            _select(
                ListEntrantExamState.item_zno_options,
                ListEntrantExamState.filter_item_zno_id_str,
                ListEntrantExamState.set_filter_item_zno_id,
                width="100%",
            ),
            rx.text("Відповідальний:"),
            _select(
                ListEntrantExamState.worker_options,
                ListEntrantExamState.filter_worker_id_str,
                ListEntrantExamState.set_filter_worker_id,
                width="100%",
            ),
            spacing="2",
            align="stretch",
            width="100%",
        ),
        on_clear=ListEntrantExamState.clear_filters,
    )


def list_page_content() -> rx.Component:
    return rx.vstack(
        _filter_panel(),
        rx.cond(
            ListEntrantExamState.items_display.length() > 0,
            _list_table(),
            controls.empty_placeholder(),
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


# ============================================================
# Form (Add / Edit) helpers
# ============================================================

def _worker_chip_row(row: Dict[str, str], form_state) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(row["pib"], align="left"),
        rx.table.cell(row["email"]),
        rx.table.cell(
            controls.delete_with_confirm(
                on_confirm=form_state.remove_worker(row["id"]),
                description="Прибрати співробітника зі списку відповідальних?",
            )
        ),
    )


def _picker_row(row: Dict[str, str], form_state) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(row["pib"], align="left"),
        rx.table.cell(row["email"]),
        rx.table.cell(
            controls.button_image_primary(
                name_icon="plus",
                on_click=form_state.pick_worker(row["id"]),
            )
        ),
    )


def _workers_section(form_state) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Відповідальні співробітники", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=form_state.open_w_picker),
            width="100%",
        ),
        rx.cond(
            form_state.chosen_workers_display.length() > 0,
            rx.table.root(
                _table_header("ПІБ", "Email", "Дії"),
                rx.table.body(
                    rx.foreach(
                        form_state.chosen_workers_display,
                        lambda row: _worker_chip_row(row, form_state),
                    )
                ),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder("Відповідальних не вибрано"),
        ),
        spacing="2",
        align="stretch",
        width="100%",
    )


def _worker_picker_dialog(form_state) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Обрати відповідального"),
            rx.vstack(
                rx.input(
                    placeholder="Пошук за ПІБ / email / логіном",
                    value=form_state.w_search,
                    on_change=form_state.set_w_search,
                    width="100%",
                ),
                rx.cond(
                    form_state.picker_worker_rows.length() > 0,
                    rx.table.root(
                        _table_header("ПІБ", "Email", "Дії"),
                        rx.table.body(
                            rx.foreach(
                                form_state.picker_worker_rows,
                                lambda row: _picker_row(row, form_state),
                            )
                        ),
                        variant="surface",
                        width="100%",
                    ),
                    controls.empty_placeholder("Нікого не знайдено"),
                ),
                rx.hstack(
                    rx.dialog.close(controls.button_secondary("Закрити", on_click=form_state.close_w_picker)),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                align="stretch",
                max_height="60vh",
                overflow_y="auto",
            ),
            max_width="40rem",
        ),
        open=form_state.w_open,
        on_open_change=form_state.set_w_open,
    )


def _form_content(form_state) -> rx.Component:
    return rx.vstack(
        rx.text("*Група:"),
        _select(
            form_state.group_options,
            form_state.id_group_str,
            form_state.set_id_group,
            placeholder="Оберіть групу",
            width="100%",
        ),
        rx.text("*Предмет:"),
        _select(
            form_state.item_zno_options,
            form_state.id_item_zno_str,
            form_state.set_id_item_zno,
            placeholder="Оберіть предмет",
            width="100%",
        ),
        rx.text("*Дата:"),
        rx.input(
            type="date",
            value=form_state.date,
            on_change=form_state.set_date,
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("*Час початку:"),
                rx.input(
                    type="time",
                    value=form_state.time_start,
                    on_change=form_state.set_time_start,
                    width="100%",
                ),
                align="stretch",
                width="100%",
                spacing="1",
            ),
            rx.vstack(
                rx.text("*Час завершення:"),
                rx.input(
                    type="time",
                    value=form_state.time_end,
                    on_change=form_state.set_time_end,
                    width="100%",
                ),
                align="stretch",
                width="100%",
                spacing="1",
            ),
            spacing="3",
            width="100%",
        ),
        rx.text("Опис / додаткова інформація:"),
        rx.text_area(
            value=form_state.description,
            on_change=form_state.set_description,
            width="100%",
        ),
        _workers_section(form_state),
        _worker_picker_dialog(form_state),
        align="stretch",
        spacing="3",
        width="100%",
    )


# ============================================================
# View page
# ============================================================

def _view_worker_row(row: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(row["pib"], align="left"),
        rx.table.cell(row["email"]),
        rx.table.cell(row["phone"]),
    )


def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewEntrantExamState.item_zno_title, size="6"),
        rx.hstack(rx.text("Група:", weight="bold"), rx.text(ViewEntrantExamState.group_title), spacing="2"),
        rx.hstack(rx.text("Дата:", weight="bold"), rx.text(ViewEntrantExamState.date), spacing="2"),
        rx.hstack(
            rx.text("Час:", weight="bold"),
            rx.text(ViewEntrantExamState.time_start + " — " + ViewEntrantExamState.time_end),
            spacing="2",
        ),
        rx.cond(
            ViewEntrantExamState.description != "",
            rx.vstack(
                rx.text("Опис:", weight="bold"),
                rx.text(ViewEntrantExamState.description),
                spacing="1",
                align="stretch",
            ),
        ),
        rx.heading("Відповідальні співробітники", size="3"),
        rx.cond(
            ViewEntrantExamState.responsible_workers_display.length() > 0,
            rx.table.root(
                _table_header("ПІБ", "Email", "Телефон"),
                rx.table.body(rx.foreach(ViewEntrantExamState.responsible_workers_display, _view_worker_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder("Відповідальних не призначено"),
        ),
        spacing="3",
        align="stretch",
        width="100%",
    )


# ============================================================
# Print page
# ============================================================

def _print_row(row: Dict[str, str]) -> rx.Component:
    return rx.table.row(
        rx.table.cell(row["group"]),
        rx.table.cell(row["item_zno"]),
        rx.table.cell(row["date"]),
        rx.table.cell(row["time_start"]),
        rx.table.cell(row["time_end"]),
        rx.table.cell(row["workers"]),
    )


def _print_styles() -> rx.Component:
    # Сховати весь хром застосунку (шапку, сайдбар, кнопки) при друку та прибрати
    # обмеження висоти контейнера контенту, щоб таблиця могла рости вертикально.
    return rx.html(
        """
        <style>
          @media print {
            .no-print { display: none !important; }
            html, body { background: white !important; }
            body * { visibility: hidden; }
            #print-area, #print-area * { visibility: visible; }
            #print-area {
              position: absolute;
              left: 0;
              top: 0;
              width: 100%;
              padding: 1rem;
            }
          }
        </style>
        """
    )


def print_page_content() -> rx.Component:
    return rx.box(
        _print_styles(),
        rx.hstack(
            controls.button_secondary("Назад", on_click=PrintEntrantExamState.on_click_back),
            rx.spacer(),
            controls.button_primary("Друк", on_click=PrintEntrantExamState.on_click_print),
            class_name="no-print",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.box(
            rx.heading("Графік іспитів", size="5", margin_bottom="0.75rem"),
            rx.cond(
                ListEntrantExamState.items_display.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Група"),
                            rx.table.column_header_cell("Назва екзамену"),
                            rx.table.column_header_cell("Дата"),
                            rx.table.column_header_cell("Початок"),
                            rx.table.column_header_cell("Кінець"),
                            rx.table.column_header_cell("Відповідальні"),
                        ),
                    ),
                    rx.table.body(rx.foreach(ListEntrantExamState.items_display, _print_row)),
                    variant="surface",
                    width="100%",
                ),
                rx.text("Записи відсутні", color="gray"),
            ),
            id="print-area",
            width="100%",
        ),
        width="100%",
        padding="1rem",
    )


# ============================================================
# Add / Edit content wrappers
# ============================================================

def add_page_content() -> rx.Component:
    return _form_content(AddEntrantExamState)


def edit_page_content() -> rx.Component:
    return _form_content(EditEntrantExamState)


# ============================================================
# Pages
# ============================================================

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Графік іспитів",
            controls.button_filter_toggle(
                ListEntrantExamState.filter_open,
                ListEntrantExamState.toggle_filter,
            ),
            controls.button_image_secondary(name_icon="printer", on_click=ListEntrantExamState.on_click_print),
            rx.cond(
                ListEntrantExamState.get_user_actions.contains(Actions.ENTRANT_EXAM_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListEntrantExamState.on_click_add),
            ),
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListEntrantExamState.in_progress, height="100%"),
    )


@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд іспиту",
            rx.cond(
                ViewEntrantExamState.get_user_actions.contains(Actions.ENTRANT_EXAM_DELETE),
                controls.delete_with_confirm(on_confirm=ViewEntrantExamState.on_click_delete),
            ),
            rx.cond(
                ViewEntrantExamState.get_user_actions.contains(Actions.ENTRANT_EXAM_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntrantExamState.on_click_edit),
            ),
            left=controls.button_back(routes.ENTRANT_EXAM_LIST),
            width="100%",
        ),
        rx.skeleton(view_page_content(), loading=ViewEntrantExamState.in_process, height="100%"),
    )


@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання іспиту",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddEntrantExamState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddEntrantExamState.on_save),
            width="100%",
        ),
        rx.skeleton(add_page_content(), loading=AddEntrantExamState.in_process, height="100%"),
    )


@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування іспиту",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditEntrantExamState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditEntrantExamState.on_save),
            width="100%",
        ),
        rx.skeleton(edit_page_content(), loading=EditEntrantExamState.in_process, height="100%"),
    )


@require_login
def print_page() -> rx.Component:
    # Окрема сторінка з друкарською розміткою: використовує дані з ListEntrantExamState
    # (фільтри застосовані на списочній сторінці зберігаються в сесійному стані клієнта).
    return print_page_content()
