import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entrants_group import (
    ListEntrantsGroupState,
    AddEntrantsGroupState,
    EditEntrantsGroupState,
    ViewEntrantsGroupState,
    AutoGenerateEntrantsGroupState,
    GeneratedEntrant,
    PrintEntrantsGroupState,
    PrintGroup,
    PrintEntrantRow,
)
from Dekanat.models import EntrantGroupModel, EntrantModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


# ============================================================
# List page
# ============================================================

def _list_row(item: EntrantGroupModel) -> rx.Component:
    return rx.table.row(
        rx.cond(
            ListEntrantsGroupState.select_mode,
            rx.table.cell(
                rx.checkbox(
                    checked=ListEntrantsGroupState.selected_set.contains(item.id.to_string()),
                    on_change=ListEntrantsGroupState.toggle_selected(item.id),
                ),
                width="2.5rem",
            ),
        ),
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ENTRANTS_GROUP_VIEW}{item.id}"),
            align="left"
        ),
        rx.table.cell(ListEntrantsGroupState.counts[item.id.to_string()], align="center"),
    )

def _sortable_header(title: str, field: str, **kw) -> rx.Component:
    """Кликабельний заголовок столбця списку груп з індикатором сортування (DK-48)."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(title, color=rx.color("accent", 2)),
            rx.text(ListEntrantsGroupState.sort_indicator[field], color=rx.color("accent", 2), weight="bold"),
            spacing="1",
            align="center",
        ),
        color=rx.color("accent", 2),
        cursor="pointer",
        on_click=ListEntrantsGroupState.on_click_sort(field),
        _hover={"background_color": rx.color("accent", 10)},
        **kw,
    )


def _list_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.cond(
                    ListEntrantsGroupState.select_mode,
                    rx.table.column_header_cell("", color=rx.color("accent", 2), width="2.5rem"),
                ),
                _sortable_header("Назва", "title"),
                _sortable_header("Абітурієнтів", "count", width="8rem"),
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

        rx.hstack(
            rx.heading("Абітурієнти у групі", size="4"),
            rx.badge(
                ViewEntrantsGroupState.entrants_in_group.length().to_string(),
                color_scheme="brown",
                variant="soft",
                size="2",
            ),
            align="center",
            spacing="2",
        ),
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
            controls.button_secondary(
                rx.icon("wand-sparkles", size=18),
                "Автопідбір",
                on_click=EditEntrantsGroupState.on_click_autofill,
            ),
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
    # У режимі вибору ховаємо звичайні кнопки (фільтр/авто/додати) і показуємо
    # панель «виділити все / зняти / підтвердити». Сама кнопка-перемикач режиму
    # стає primary, щоб візуально показати активний стан.
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(
                ListEntrantsGroupState.select_mode,
                # У режимі вибору: панель «виділити всі / зняти / підтвердити» +
                # кнопка виходу з режиму (circle_x). Інших кнопок не показуємо.
                rx.hstack(
                    controls.button_secondary("Виділити всі", on_click=ListEntrantsGroupState.select_all),
                    controls.button_secondary("Зняти виділення", on_click=ListEntrantsGroupState.clear_selection),
                    controls.button_primary("Підтвердити", on_click=ListEntrantsGroupState.on_click_print_confirm),
                    controls.button_image_primary(name_icon="circle_x", on_click=ListEntrantsGroupState.toggle_select_mode),
                    spacing="2",
                ),
                # Звичайний режим: фільтр, авто-формування, друк, додавання — саме
                # у такому порядку. Кнопка друку має стояти перед «+» (DK-24 follow-up).
                rx.hstack(
                    controls.button_filter_toggle(ListEntrantsGroupState.filter_open, on_click=ListEntrantsGroupState.toggle_filter),
                    rx.cond(
                        ListEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_AUTO_GENERATE),
                        controls.button_image_secondary(
                            name_icon="wand-sparkles",
                            on_click=rx.redirect(routes.ENTRANTS_GROUP_AUTO),
                        ),
                    ),
                    controls.button_image_secondary(name_icon="printer", on_click=ListEntrantsGroupState.toggle_select_mode),
                    rx.cond(ListEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_ADD),
                            controls.button_image_primary(name_icon="plus", on_click=ListEntrantsGroupState.on_click_add)),
                    spacing="2",
                ),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListEntrantsGroupState.in_progress, height="100%"),
        filter_panel=_list_filter_panel(),
        on_mount=ListEntrantsGroupState.on_load,
    )


# ============================================================
# Auto-generate page (DK-24)
# ============================================================

def _auto_table_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.hstack(
                rx.link(
                    row["title"],
                    on_click=AutoGenerateEntrantsGroupState.open_composition(row["index"].to(int)),
                    cursor="pointer",
                    color=rx.color("accent", 11),
                    weight="bold",
                ),
                rx.cond(
                    row["is_existing"] != "",
                    rx.badge("наявна", color_scheme="grass", variant="soft"),
                ),
                align="center",
                spacing="2",
            ),
            align="left",
        ),
        rx.table.cell(row["spec_label"]),
        # Для наявних груп показуємо підсумок і скільки додається (DK-42).
        rx.table.cell(
            rx.cond(
                row["is_existing"] != "",
                row["total"] + " (+" + row["count"] + ")",
                row["count"],
            ),
        ),
        rx.table.cell(
            controls.delete_with_confirm(
                on_confirm=AutoGenerateEntrantsGroupState.remove_group(row["index"].to(int)),
                description="Прибрати цю сформовану групу з результату?",
            ),
        ),
    )


def _auto_results_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва групи", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Спеціальність", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Кількість", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Дії", color=rx.color("accent", 2), width="6rem"),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(rx.foreach(AutoGenerateEntrantsGroupState.group_rows, _auto_table_row)),
        variant="surface",
        width="100%",
    )


def _composition_row(item: GeneratedEntrant) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(item.pib, align="left"),
        rx.table.cell(item.spec_label),
        rx.table.cell(
            controls.delete_with_confirm(
                on_confirm=AutoGenerateEntrantsGroupState.remove_entrant_from_group(item.id),
                description="Виключити цього абітурієнта з групи?",
            )
        ),
    )


def _picker_row(item: GeneratedEntrant) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(item.pib, align="left"),
        rx.table.cell(item.spec_label),
        rx.table.cell(
            controls.button_image_primary(
                name_icon="plus",
                on_click=AutoGenerateEntrantsGroupState.add_entrant_to_group(item.id),
            )
        ),
    )


def _picker_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Додати абітурієнта"),
            rx.vstack(
                rx.input(
                    placeholder="Пошук за ПІБ",
                    value=AutoGenerateEntrantsGroupState.picker_search,
                    on_change=AutoGenerateEntrantsGroupState.set_picker_search,
                    width="100%",
                ),
                rx.cond(
                    AutoGenerateEntrantsGroupState.picker_rows.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                                rx.table.column_header_cell("Пріоритетна спеціальність", color=rx.color("accent", 2)),
                                rx.table.column_header_cell("Дії", color=rx.color("accent", 2)),
                            ),
                            background_color=rx.color("accent", 9),
                        ),
                        rx.table.body(
                            rx.foreach(AutoGenerateEntrantsGroupState.picker_rows, _picker_row),
                        ),
                        variant="surface",
                        width="100%",
                    ),
                    controls.empty_placeholder("Кандидатів не знайдено"),
                ),
                rx.hstack(
                    rx.dialog.close(controls.button_secondary("Закрити")),
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
        open=AutoGenerateEntrantsGroupState.picker_open,
        on_open_change=AutoGenerateEntrantsGroupState.set_picker_open,
    )


def _composition_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AutoGenerateEntrantsGroupState.current_group_title),
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Учасники групи:",
                        weight="bold",
                    ),
                    rx.spacer(),
                    controls.button_image_primary(
                        name_icon="plus",
                        on_click=AutoGenerateEntrantsGroupState.open_picker,
                    ),
                    width="100%",
                ),
                rx.cond(
                    AutoGenerateEntrantsGroupState.current_group_entrants.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                                rx.table.column_header_cell("Пріоритетна спеціальність", color=rx.color("accent", 2)),
                                rx.table.column_header_cell("Дії", color=rx.color("accent", 2)),
                            ),
                            background_color=rx.color("accent", 9),
                        ),
                        rx.table.body(
                            rx.foreach(AutoGenerateEntrantsGroupState.current_group_entrants, _composition_row),
                        ),
                        variant="surface",
                        width="100%",
                    ),
                    controls.empty_placeholder("Учасників ще немає"),
                ),
                rx.hstack(
                    rx.dialog.close(controls.button_secondary("Закрити")),
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                align="stretch",
                max_height="70vh",
                overflow_y="auto",
            ),
            max_width="40rem",
        ),
        open=AutoGenerateEntrantsGroupState.composition_open,
        on_open_change=AutoGenerateEntrantsGroupState.set_composition_open,
    )


def auto_generate_page_content() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.text("*Максимальний розмір групи:", weight="bold"),
                rx.hstack(
                    rx.input(
                        type="number",
                        value=AutoGenerateEntrantsGroupState.max_size.to_string(),
                        on_change=AutoGenerateEntrantsGroupState.set_max_size,
                        width="12rem",
                    ),
                    rx.checkbox(
                        "Враховувати наявні групи",
                        checked=AutoGenerateEntrantsGroupState.use_existing,
                        on_change=AutoGenerateEntrantsGroupState.set_use_existing,
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.text(
                    "Якщо увімкнено — абітурієнти спершу дозаповнюють наявні групи "
                    "тієї ж спеціальності до вказаного ліміту, а решта формує нові.",
                    size="1",
                    color="gray",
                ),
                controls.button_primary(
                    rx.cond(
                        AutoGenerateEntrantsGroupState.generating,
                        rx.spinner(size="3"),
                        rx.icon("wand-sparkles", size=18),
                    ),
                    "Застосувати",
                    on_click=AutoGenerateEntrantsGroupState.on_click_generate,
                    loading=AutoGenerateEntrantsGroupState.generating,
                ),
                spacing="3",
                align="stretch",
            ),
            padding="1rem",
            border_radius="0.6rem",
            background_color=rx.color("gray", 2),
            border=f"1px solid {rx.color('gray', 5)}",
            width="100%",
        ),
        rx.heading("Результат", size="5"),
        rx.cond(
            AutoGenerateEntrantsGroupState.generating,
            rx.center(
                rx.hstack(rx.spinner(size="3"), rx.text("Йде формування…")),
                padding="2rem",
                width="100%",
            ),
            rx.cond(
                AutoGenerateEntrantsGroupState.group_rows.length() > 0,
                _auto_results_table(),
                controls.empty_placeholder("Натисніть «Застосувати», щоб сформувати групи."),
            ),
        ),
        _composition_dialog(),
        _picker_dialog(),
        spacing="3",
        align="stretch",
        width="100%",
    )


@require_login
def auto_generate_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Автоформування груп",
            controls.button_image_secondary(name_icon="circle_x", on_click=AutoGenerateEntrantsGroupState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AutoGenerateEntrantsGroupState.on_save),
            left=controls.button_back(routes.ENTRANTS_GROUP_LIST),
            width="100%",
        ),
        rx.skeleton(auto_generate_page_content(), loading=AutoGenerateEntrantsGroupState.in_progress, height="100%"),
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_SHEETS),
                rx.fragment(
                    controls.button_secondary(
                        rx.icon("file-spreadsheet", size=18), "Відомість",
                        on_click=ViewEntrantsGroupState.on_click_sheet("vidomist"),
                        loading=ViewEntrantsGroupState.downloading,
                    ),
                    controls.button_secondary(
                        rx.icon("file-spreadsheet", size=18), "Викладачі",
                        on_click=ViewEntrantsGroupState.on_click_sheet("vykladacham"),
                        loading=ViewEntrantsGroupState.downloading,
                    ),
                    controls.button_secondary(
                        rx.icon("file-spreadsheet", size=18), "Телефони",
                        on_click=ViewEntrantsGroupState.on_click_sheet("telefony"),
                        loading=ViewEntrantsGroupState.downloading,
                    ),
                ),
            ),
            controls.button_image_secondary(name_icon="printer", on_click=ViewEntrantsGroupState.on_click_print),
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_DELETE),
                    controls.delete_with_confirm(on_confirm=ViewEntrantsGroupState.on_click_delete)),
            rx.cond(ViewEntrantsGroupState.get_user_actions.contains(Actions.ENTRANTS_GROUP_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntrantsGroupState.on_click_edit)),
            left=controls.button_back(routes.ENTRANTS_GROUP_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewEntrantsGroupState.in_process, height="100%"),
            audit_history_section("entrants_groups"),
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


# ============================================================
# Print page (DK-24 follow-up)
# ============================================================

def _print_styles() -> rx.Component:
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
            .print-group { page-break-after: always; }
            .print-group:last-child { page-break-after: auto; }
          }
        </style>
        """
    )


def _print_entrant_row(row: PrintEntrantRow) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(row.pib, align="left"),
    )


def _print_group_section(group: PrintGroup) -> rx.Component:
    return rx.box(
        rx.heading(group.title, size="5", margin_bottom="0.75rem"),
        rx.cond(
            group.entrants.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(rx.table.column_header_cell("ПІБ")),
                ),
                rx.table.body(rx.foreach(group.entrants, _print_entrant_row)),
                variant="surface",
                width="100%",
            ),
            rx.text("Учасників немає", color="gray"),
        ),
        margin_bottom="1.5rem",
        class_name="print-group",
    )


def print_page_content() -> rx.Component:
    return rx.box(
        _print_styles(),
        rx.hstack(
            controls.button_secondary("Назад", on_click=PrintEntrantsGroupState.on_click_back),
            rx.spacer(),
            controls.button_primary("Друк", on_click=PrintEntrantsGroupState.on_click_print),
            class_name="no-print",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.box(
            rx.cond(
                PrintEntrantsGroupState.groups.length() > 0,
                rx.vstack(
                    rx.foreach(PrintEntrantsGroupState.groups, _print_group_section),
                    spacing="4",
                    align="stretch",
                    width="100%",
                ),
                rx.text("Немає груп для друку.", color="gray"),
            ),
            id="print-area",
        ),
        width="100%",
    )


@require_login
def print_page() -> rx.Component:
    return page_wrapper(
        rx.box(),
        rx.skeleton(print_page_content(), loading=PrintEntrantsGroupState.in_progress, height="100%"),
    )
