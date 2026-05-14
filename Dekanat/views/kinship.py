import reflex as rx

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.kinship import ListKinshipState, AddKinshipState, EditKinshipState, ViewKinshipSate
from Dekanat.models import KinshipModel

from Dekanat.views.tamplates.layouts import page_wrapper, header_subpage
from Dekanat.views.tamplates import controlls
from Dekanat.views.auth import require_login


def table_row(item: KinshipModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(item.title, href=f"{routes.KINSHIP_VIEW}{item.id}"),
            align="left"
        ),
    )

def table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
            ),

            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListKinshipState.items, table_row),
            height="100%",
            width="100%"
        ),

        variant="surface",

        height="100%",
        width="100%"
    )

def list_page_content() -> rx.Component:
    return rx.vstack(
        rx.cond(ListKinshipState.items.is_not_none(),
                table(),
                rx.text("Дані відсутні")
                ),
    )

def view_page_content() -> rx.Component:
    return rx.vstack(
        rx.heading(ViewKinshipSate.title),
        rx.button("Редагувати", on_click=ViewKinshipSate.on_click_edit),

        height="100%",
        width="100%"
    )

def add_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=AddKinshipState.title, on_change=AddKinshipState.set_title),
    )

def edit_page_content() -> rx.Component:
    return rx.vstack(
        rx.text("*Назва"),
        rx.input(id="title", required=True, value=EditKinshipState.title, on_change=EditKinshipState.set_title),
    )

@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            rx.cond(ListKinshipState.get_user_actions.contains(Actions.KINSHIP_ADD), controlls.button_image_primery(name_icon="plus", on_click=ListKinshipState.on_click_add)),
            width="100%"
        ),
        rx.skeleton(list_page_content(), loading=ListKinshipState.in_progress, height="100%")
    )

@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(ViewKinshipSate.get_user_actions.contains(Actions.KINSHIP_DELETE), controlls.button_image_secondary(name_icon="trash_2", on_click=ViewKinshipSate.on_click_delete)),
            rx.cond(ViewKinshipSate.get_user_actions.contains(Actions.KINSHIP_EDIT), controlls.button_image_primery(name_icon="pencil_line", on_click=ViewKinshipSate.on_click_edit)),
            width="100%"
        ),
        rx.skeleton(view_page_content(), loading=ViewKinshipSate.in_process, height="100%")
    )

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controlls.button_image_secondary(name_icon="circle_x", on_click=AddKinshipState.on_cancel),
            controlls.button_image_primery(name_icon="save", on_click=AddKinshipState.on_save),
            width="100%"
        ),
        add_page_content()
    )

@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controlls.button_image_secondary(name_icon="circle_x", on_click=EditKinshipState.on_cancel),
            controlls.button_image_primery(name_icon="save", on_click=EditKinshipState.on_save),
            width="100%"
        ),
        rx.skeleton(edit_page_content(), loading=EditKinshipState.in_process, height="100%")
    )
