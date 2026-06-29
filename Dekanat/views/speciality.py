import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.speciality import (
    ListSpecialityState,
    AddSpecialityState,
    EditSpecialityState,
    ViewSpecialityState,
)
from Dekanat.models import SpecialityModel

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


def table_row(item: SpecialityModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.code, align="center"),
        rx.table.row_header_cell(
            rx.link(
                item.title,
                href=f"{routes.SPECIALITY_VIEW}{item.id_department}/{item.code}",
            ),
            align="left"
        ),
        rx.table.cell(
            rx.cond(
                item.department,
                rx.text(item.department.title),
                rx.text("—"),
            ),
            align="left"
        ),
        rx.table.cell(rx.text(item.tag), align="left"),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Код", min_width="30px", width="30px", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Відділення", color=rx.color("accent", 2)),
                rx.table.column_header_cell("Тег", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListSpecialityState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond((ListSpecialityState.items.is_not_none() & (ListSpecialityState.items.length() > 0)),
                table(),
                controls.empty_placeholder()
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewSpecialityState.title, size="6"),
        rx.text("Код: " + ViewSpecialityState.entity_code, color="gray"),
        rx.text("Відділення: " + ViewSpecialityState.department_title, color="gray"),
        rx.text("Тег: " + ViewSpecialityState.tag, color="gray"),
        rx.cond(
            ViewSpecialityState.program,
            rx.vstack(
                rx.text("Освітньо-професійна програма:", weight="bold"),
                rx.text(ViewSpecialityState.program),
                spacing="1",
                align="stretch",
            ),
        ),

        spacing="3",
        align="stretch",
        height="100%",
        width="100%"
    )


def _department_select_item(opt: Dict[str, str]) -> rx.Component:
    return rx.select.item(opt["label"], value=opt["value"])

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Код:"),
        rx.input(
            required=True,
            value=AddSpecialityState.entity_code,
            on_change=AddSpecialityState.set_code,
        ),
        rx.text("*Відділення:"),
        rx.select.root(
            rx.select.trigger(placeholder="Оберіть відділення"),
            rx.select.content(
                rx.foreach(AddSpecialityState.department_options, _department_select_item),
            ),
            value=AddSpecialityState.id_department_str,
            on_change=AddSpecialityState.set_id_department,
        ),
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=AddSpecialityState.title,
            on_change=AddSpecialityState.set_title,
        ),
        rx.text("*Тег:"),
        rx.input(
            required=True,
            value=AddSpecialityState.tag,
            on_change=AddSpecialityState.set_tag,
        ),
        rx.text("Освітньо-професійна програма:"),
        rx.text_area(
            value=AddSpecialityState.program,
            on_change=AddSpecialityState.set_program,
        ),

        align="stretch",
        spacing="3",
        width="100%"
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("Код:"),
        rx.input(value=EditSpecialityState.entity_code, disabled=True),
        rx.text("Відділення:"),
        rx.input(value=EditSpecialityState.department_title, disabled=True),
        rx.text("*Назва:"),
        rx.input(
            required=True,
            value=EditSpecialityState.title,
            on_change=EditSpecialityState.set_title,
        ),
        rx.text("*Тег:"),
        rx.input(
            required=True,
            value=EditSpecialityState.tag,
            on_change=EditSpecialityState.set_tag,
        ),
        rx.text("Освітньо-професійна програма:"),
        rx.text_area(
            value=EditSpecialityState.program,
            on_change=EditSpecialityState.set_program,
        ),

        align="stretch",
        spacing="3",
        width="100%"
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(
                ListSpecialityState.get_user_actions.contains(Actions.SPECIALITY_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListSpecialityState.on_click_add),
            ),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListSpecialityState.in_progress, height="100%"),
        on_mount=ListSpecialityState.on_load,
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewSpecialityState.get_user_actions.contains(Actions.SPECIALITY_DELETE),
                controls.delete_with_confirm(on_confirm=ViewSpecialityState.on_click_delete),
            ),
            rx.cond(
                ViewSpecialityState.get_user_actions.contains(Actions.SPECIALITY_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewSpecialityState.on_click_edit),
            ),
            left=controls.button_back(routes.SPECIALITY_LIST),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewSpecialityState.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=AddSpecialityState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=AddSpecialityState.on_save),
            width="100%"
        ),
        rx.skeleton(add_page_content(), loading=AddSpecialityState.in_process, height="100%")
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EditSpecialityState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EditSpecialityState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditSpecialityState.in_process, height="100%")
    )
