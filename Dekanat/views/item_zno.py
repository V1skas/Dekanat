import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.item_zno import ListItemZnoState, AddItemZnoState, EditItemZnoState, ViewItemZnoState
from Dekanat.models import ItemZnoModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.templates.audit import audit_history_section
from Dekanat.views.auth import require_login


def table_row(item: ItemZnoModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.ITEM_ZNO_VIEW}{item.id}"),
            align="left"
        ),
        rx.table.cell(item.coefficient),
        rx.table.cell(rx.cond(item.is_counted_in_rating, "Так", "Ні")),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Коефіцієнт", color=rx.color("accent", 2)),
                rx.table.column_header_cell("У рейтингу", color=rx.color("accent", 2)),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListItemZnoState.items, table_row),
            height="100%",
            width="100%"
        ),
        variant="surface",
        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListItemZnoState.items.is_not_none() & (ListItemZnoState.items.length() > 0)),
                table(),
                controls.empty_placeholder()),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewItemZnoState.title),
        rx.hstack(
            rx.text("Коефіцієнт:", weight="bold"),
            rx.text(ViewItemZnoState.coefficient_str),
            spacing="2",
        ),
        rx.hstack(
            rx.text("Враховується у рейтингу:", weight="bold"),
            rx.text(rx.cond(ViewItemZnoState.is_counted_in_rating, "Так", "Ні")),
            spacing="2",
        ),
        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=AddItemZnoState.title, on_change=AddItemZnoState.set_title, width="100%"),
        rx.text("*Коефіцієнт"),
        rx.input(type="number", step="any", value=AddItemZnoState.coefficient_str, on_change=AddItemZnoState.set_coefficient, width="100%"),
        rx.text("Бал, введений оператором, буде домножено на цей коефіцієнт.", size="2", color="gray"),
        rx.checkbox(
            "Враховувати у рейтингу",
            checked=AddItemZnoState.is_counted_in_rating,
            on_change=AddItemZnoState.set_is_counted_in_rating,
        ),
        rx.text("Якщо вимкнено — оцінка цього предмета не входить у суму балів рейтингу та не показується колонкою в документі.", size="2", color="gray"),
        align="stretch",
        spacing="3",
        width="100%",
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=EditItemZnoState.title, on_change=EditItemZnoState.set_title, width="100%"),
        rx.text("*Коефіцієнт"),
        rx.input(type="number", step="any", value=EditItemZnoState.coefficient_str, on_change=EditItemZnoState.set_coefficient, width="100%"),
        rx.text("Бал, введений оператором, буде домножено на цей коефіцієнт.", size="2", color="gray"),
        rx.checkbox(
            "Враховувати у рейтингу",
            checked=EditItemZnoState.is_counted_in_rating,
            on_change=EditItemZnoState.set_is_counted_in_rating,
        ),
        rx.text("Якщо вимкнено — оцінка цього предмета не входить у суму балів рейтингу та не показується колонкою в документі.", size="2", color="gray"),
        align="stretch",
        spacing="3",
        width="100%",
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_ADD),
                    controls.button_image_primary(name_icon="plus", on_click=ListItemZnoState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListItemZnoState.in_progress, height="100%"),
        on_mount=ListItemZnoState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_DELETE),
                    controls.delete_with_confirm(on_confirm=ViewItemZnoState.on_click_delete)),
            rx.cond(ViewItemZnoState.get_user_actions.contains(Actions.ITEM_ZNO_EDIT),
                    controls.button_image_primary(name_icon="pencil_line", on_click=ViewItemZnoState.on_click_edit)),
            left=controls.button_back(routes.ITEM_ZNO_LIST),
            width="100%"
        ),
        rx.vstack(
            rx.skeleton(view_page_content(), loading=ViewItemZnoState.in_process, height="100%"),
            audit_history_section(Actions.ITEM_ZNO_HISTORY_VIEW.value, Actions.ITEM_ZNO_HISTORY_DETAIL.value),
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
            controls.button_image_secondary(name_icon="circle_x", on_click=AddItemZnoState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddItemZnoState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditItemZnoState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditItemZnoState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditItemZnoState.in_process, height="100%")
    )
