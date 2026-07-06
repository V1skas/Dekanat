import reflex as rx

from typing import Dict

from Dekanat import routes
from Dekanat.actions import Actions
from Dekanat.states.entrant import (
    ListEntrantState,
    ViewEntrantState,
    EntrantFormState,
    CITIZENSHIP_OPTIONS,
    SEX_OPTIONS,
)
from Dekanat.models import (
    EntrantModel,
    IdentityDocumentModel,
    DocumentAboutEducationModel,
    MilitaryAccountingModel,
    MedicalReferenceModel,
    InformationAboutRelativesModel,
    SpecialConditionPersonModel,
    SpecialtieEntrantModel,
    ResultZnoModel,
)

from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates import controls
from Dekanat.views.auth import require_login


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
# List page
# ============================================================

def _list_table_row(item: EntrantModel) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.link(
                rx.cond(item.person, item.person.pib, "—"),
                href=f"{routes.ENTRANT_VIEW}{item.id}",
            ),
            align="left",
        ),
        rx.table.cell(
            rx.cond(item.created_at, item.created_at.to_string()[1:11], "—")
        ),
        rx.table.cell(rx.cond(item.person, item.person.phone_number, "—")),
        rx.table.cell(rx.cond(item.person, rx.cond(item.person.email, item.person.email, "—"), "—")),
        rx.table.cell(
            rx.cond(
                item.person,
                rx.cond(item.person.entry_base, item.person.entry_base.title, "—"),
                "—",
            )
        ),
        rx.table.cell(
            rx.cond(
                item.person,
                rx.cond(item.person.source_of_funding, item.person.source_of_funding.title, "—"),
                "—",
            )
        ),
        rx.table.cell(
            rx.cond(item.entrant_group, item.entrant_group.title, "—")
        ),
        rx.table.cell(
            rx.cond(
                item.specialties,
                rx.cond(
                    item.specialties[0],
                    f"{item.specialties[0].speciality.code} {item.specialties[0].speciality.title} ({item.specialties[0].speciality.tag})",
                    "—",
                ),
                "—",
            )
        ),
        rx.table.cell(
            rx.cond(item.application_status, item.application_status.title, "—")
        ),
    )


def _sortable_header(title: str, field: str) -> rx.Component:
    """Кликабельний заголовок столбця. Поруч із назвою — індикатор поточного
    сортування ( ↑ / ↓ / порожньо). Курсор pointer + hover-підсвітка."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(title, color=rx.color("accent", 2)),
            rx.text(
                ListEntrantState.sort_indicator[field],
                color=rx.color("accent", 2),
                weight="bold",
            ),
            spacing="1",
            align="center",
        ),
        color=rx.color("accent", 2),
        cursor="pointer",
        on_click=ListEntrantState.on_click_sort(field),
        _hover={"background_color": rx.color("accent", 10)},
    )


def _list_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                _sortable_header("ПІБ", "pib"),
                _sortable_header("Дата створення", "created_at"),
                _sortable_header("Номер телефону", "phone_number"),
                _sortable_header("Електронна пошта", "email"),
                _sortable_header("База вступу", "entry_base"),
                _sortable_header("Джерело фінансування", "source_of_funding"),
                _sortable_header("Група", "entrant_group"),
                _sortable_header("Спеціальність", "speciality"),
                _sortable_header("Статус заяви", "application_status"),
            ),
            background_color=rx.color("accent", 9),
        ),
        rx.table.body(
            rx.foreach(ListEntrantState.items, _list_table_row),
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
            ListEntrantState.items.is_not_none() & (ListEntrantState.items.length() > 0),
            _list_table(),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _filter_field(label: str, control: rx.Component) -> rx.Component:
    """Одна клітинка сітки фільтрів: підпис + контрол."""
    return rx.vstack(
        rx.text(label, weight="medium"),
        control,
        spacing="1",
        align="stretch",
        width="100%",
    )


def _list_filter_panel() -> rx.Component:
    # Контроли розкладені сіткою (1/2/3 колонки за шириною екрана), щоб картка
    # фільтрів займала менше місця по вертикалі.
    return controls.filter_panel(
        ListEntrantState.filter_open,
        rx.grid(
            _filter_field(
                "Вступна кампанія:",
                _select(
                    ListEntrantState.campaign_options,
                    ListEntrantState.filter_campaign_id_str,
                    ListEntrantState.set_filter_campaign_id,
                    placeholder="— Без фільтра —",
                    width="100%",
                ),
            ),
            _filter_field(
                "ПІБ містить:",
                rx.input(
                    value=ListEntrantState.filter_pib,
                    on_change=ListEntrantState.set_filter_pib,
                    placeholder="Пошук по ПІБ…",
                    width="100%",
                ),
            ),
            _filter_field(
                "Номер телефону містить:",
                rx.input(
                    value=ListEntrantState.filter_phone,
                    on_change=ListEntrantState.set_filter_phone,
                    placeholder="Пошук по телефону…",
                    width="100%",
                ),
            ),
            _filter_field(
                "Статус заяви:",
                _select(
                    ListEntrantState.application_status_options,
                    ListEntrantState.filter_status_id_str,
                    ListEntrantState.set_filter_status_id,
                    placeholder="Будь-який",
                    width="100%",
                ),
            ),
            _filter_field(
                "База вступу:",
                _select(
                    ListEntrantState.entry_base_options,
                    ListEntrantState.filter_entry_base_id_str,
                    ListEntrantState.set_filter_entry_base_id,
                    placeholder="Будь-яка",
                    width="100%",
                ),
            ),
            _filter_field(
                "Спеціальність у пріоритетах:",
                _select(
                    ListEntrantState.speciality_options,
                    ListEntrantState.filter_speciality_key,
                    ListEntrantState.set_filter_speciality_key,
                    placeholder="Будь-яка",
                    width="100%",
                ),
            ),
            _filter_field(
                "Пріоритетна спеціальність (№1):",
                _select(
                    ListEntrantState.speciality_options,
                    ListEntrantState.filter_top_speciality_key,
                    ListEntrantState.set_filter_top_speciality_key,
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
        on_clear=ListEntrantState.clear_filters,
    )


def _date_filter() -> rx.Component:
    """Фільтр по даті створення (DK-34): перемикач «день / період» + відповідні поля."""
    return rx.vstack(
        rx.text("Дата створення:", weight="medium"),
        rx.radio(
            ["День", "Період"],
            value=rx.cond(ListEntrantState.is_date_mode_period, "Період", "День"),
            on_change=ListEntrantState.set_filter_date_mode,
            direction="row",
            spacing="4",
        ),
        rx.cond(
            ListEntrantState.is_date_mode_period,
            rx.hstack(
                rx.vstack(
                    rx.text("З:", size="2"),
                    rx.input(
                        type="date",
                        value=ListEntrantState.filter_date_from,
                        on_change=ListEntrantState.set_filter_date_from,
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
                        value=ListEntrantState.filter_date_to,
                        on_change=ListEntrantState.set_filter_date_to,
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
                value=ListEntrantState.filter_date_day,
                on_change=ListEntrantState.set_filter_date_day,
                width="100%",
            ),
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


@require_login
def list_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Список",
            controls.button_filter_toggle(ListEntrantState.filter_open, on_click=ListEntrantState.toggle_filter),
            rx.cond(
                ListEntrantState.get_user_actions.contains(Actions.ENTRANT_ADD),
                controls.button_image_primary(name_icon="plus", on_click=ListEntrantState.on_click_add),
            ),
            width="100%",
        ),
        rx.skeleton(list_page_content(), loading=ListEntrantState.in_progress, height="100%"),
        filter_panel=_list_filter_panel(),
        on_mount=ListEntrantState.on_load,
    )


# ============================================================
# View page (read-only)
# ============================================================

def _v_kv(label: str, value) -> rx.Component:
    return rx.hstack(
        rx.text(label + ":", weight="bold"),
        rx.text(value),
        spacing="2",
        align="center",
    )


def _v_photo() -> rx.Component:
    return rx.cond(
        ViewEntrantState.has_photo,
        rx.el.a(
            rx.image(
                src=ViewEntrantState.photo_data_url,
                border=f"1px solid {rx.color('accent', 9)}",
                border_radius="5%",
                width="300px",
                height="400px",
                object_fit="cover",
            ),
            href=ViewEntrantState.photo_data_url,
            download=ViewEntrantState.photo_download_name,
            title="Завантажити фото",
            style={"cursor": "pointer", "display": "block"},
        ),
        rx.box(
            rx.text("Фото не завантажено", text_align="center"),
            border=f"1px solid {rx.color('accent', 9)}",
            border_radius="5%",
            width="300px",
            height="400px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def _v_iddoc_row(item: IdentityDocumentModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.cond(item.type, item.type.title, "—")),
        rx.table.cell(rx.cond(item.series, item.series, "—") + " " + item.number),
        rx.table.cell(rx.cond(item.code, item.code, "—")),
        rx.table.cell(rx.cond(item.unzr, item.unzr, "—")),
        rx.table.cell(item.issued_by),
        rx.table.cell(item.date_of_issue),
        rx.table.cell(rx.cond(item.date_of_expiry, item.date_of_expiry, "—")),
    )


def _v_iddoc_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.identity_document.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Тип", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Серія та номер", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Код", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("УНЗР", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Ким видано", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дата видачі", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дійсний до", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(
                rx.foreach(ViewEntrantState.item.person.identity_document, _v_iddoc_row),
            ),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_docedu_row(item: DocumentAboutEducationModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.title),
        rx.table.cell(rx.cond(item.number, item.number, "—")),
        rx.table.cell(rx.cond(item.series, item.series, "—")),
        rx.table.cell(rx.cond(item.issued_by, item.issued_by, "—")),
        rx.table.cell(rx.cond(item.date_of_issue, item.date_of_issue, "—")),
    )


def _v_docedu_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.document_about_education.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Номер", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Серія", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Ким видано", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дата видачі", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.document_about_education, _v_docedu_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_mil_row(item: MilitaryAccountingModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.series),
        rx.table.cell(item.number),
        rx.table.cell(rx.cond(item.issued_by, item.issued_by, "—")),
        rx.table.cell(item.date_of_issue),
    )


def _v_mil_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.military_accounting.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Серія", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Номер", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Ким видано", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дата видачі", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.military_accounting, _v_mil_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_med_row(item: MedicalReferenceModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.number),
        rx.table.cell(item.date_of_issue),
    )


def _v_med_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.medical_reference.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Номер", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дата видачі", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.medical_reference, _v_med_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_rel_row(item: InformationAboutRelativesModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.cond(item.kinship, item.kinship.title, "—")),
        rx.table.cell(item.pib),
        rx.table.cell(item.phone_number),
    )


def _v_rel_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.information_about_relatives.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Тип", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("ПІБ", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Телефон", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.information_about_relatives, _v_rel_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_scp_row(item: SpecialConditionPersonModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.id_special_condition),
        rx.table.cell(rx.cond(item.title, item.title, "—")),
        rx.table.cell(rx.cond(item.number, item.number, "—")),
        rx.table.cell(item.date_of_issue),
    )


def _v_scp_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.special_conditions.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Код", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Номер документа", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Дата видачі", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.special_conditions, _v_scp_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_sp_row(item: SpecialtieEntrantModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.priority),
        rx.table.cell(rx.cond(item.speciality, item.speciality.code, "—")),
        rx.table.cell(rx.cond(item.speciality, item.speciality.title, "—")),
        rx.table.cell(rx.cond(item.speciality, item.speciality.tag, "—")),
        rx.table.cell(rx.cond(item.form_of_study, item.form_of_study.title, "—")),
    )


def _v_sp_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.specialties.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Пріоритет", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Код", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Назва", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Тег", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Форма навчання", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.specialties, _v_sp_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def _v_rz_row(item: ResultZnoModel) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.cond(item.item_zno, item.item_zno.title, "—")),
        rx.table.cell(item.points),
    )


def _v_rz_table() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.person.results_zno.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Предмет", color=rx.color("accent", 2)),
                    rx.table.column_header_cell("Бали", color=rx.color("accent", 2)),
                ),
                background_color=rx.color("accent", 9),
            ),
            rx.table.body(rx.foreach(ViewEntrantState.item.person.results_zno, _v_rz_row)),
            variant="surface",
            width="100%",
            ),
        controls.empty_placeholder(),
    )


def view_page_content() -> rx.Component:
    return rx.cond(
        ViewEntrantState.item.is_not_none(),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Персональна інформація", value="tab1"),
                rx.tabs.trigger("Паспортні дані", value="tab2"),
                rx.tabs.trigger("Документи про освіту", value="tab3"),
                rx.tabs.trigger("Спеціальні умови", value="tab4"),
                rx.tabs.trigger("Контактні особи", value="tab5"),
                rx.tabs.trigger("Медичні довідки", value="tab6"),
                rx.tabs.trigger("Військовий облік", value="tab7"),
                rx.tabs.trigger("Спеціальності", value="tab8"),
                rx.tabs.trigger("Результати ЗНО", value="tab9"),
            ),
            rx.tabs.content(
                rx.hstack(
                    _v_photo(),
                    rx.vstack(
                        _v_kv("ПІБ", ViewEntrantState.item.person.pib),
                        _v_kv("ID особи в ЄДБО", rx.cond(ViewEntrantState.item.person.edbo, ViewEntrantState.item.person.edbo, "—")),
                        _v_kv("Громадянство", ViewEntrantState.item.person.citizenship),
                        _v_kv("Стать", ViewEntrantState.item.person.sex),
                        _v_kv("Дата народження", ViewEntrantState.item.person.date_of_birth),
                        _v_kv("Область, район, місто", rx.cond(ViewEntrantState.item.person.place_of_registration_city, ViewEntrantState.item.person.place_of_registration_city, "—")),
                        _v_kv("Адреса реєстрації", ViewEntrantState.item.person.place_of_registration),
                        _v_kv("ІПН", rx.cond(ViewEntrantState.item.person.mokpp, ViewEntrantState.item.person.mokpp, "—")),
                        _v_kv("Телефон", ViewEntrantState.item.person.phone_number),
                        _v_kv("E-mail", rx.cond(ViewEntrantState.item.person.email, ViewEntrantState.item.person.email, "—")),
                        _v_kv("Потреба в гуртожитку", rx.cond(ViewEntrantState.item.person.the_need_for_a_dormitory, "Так", "Ні")),
                        _v_kv("Джерело фінансування", rx.cond(ViewEntrantState.item.person.source_of_funding, ViewEntrantState.item.person.source_of_funding.title, "—")),
                        _v_kv("База вступу", rx.cond(ViewEntrantState.item.person.entry_base, ViewEntrantState.item.person.entry_base.title, "—")),
                        _v_kv("Статус заяви", rx.cond(ViewEntrantState.item.application_status, ViewEntrantState.item.application_status.title, "—")),
                        _v_kv("Група ЗНО", rx.cond(ViewEntrantState.item.entrant_group, ViewEntrantState.item.entrant_group.title, "—")),
                        _v_kv("Коментар", rx.cond(ViewEntrantState.item.comment, ViewEntrantState.item.comment, "—")),
                        _v_kv("Дата створення особи", ViewEntrantState.person_created_at_display),
                        _v_kv("Дата додавання абітурієнта", ViewEntrantState.entrant_created_at_display),
                        _v_kv("Остання зміна статусу заяви", ViewEntrantState.status_changed_at_display),
                        spacing="2",
                        align="stretch",
                        width="100%",
                    ),
                    align="start",
                    spacing="4",
                    width="100%",
                ),
                value="tab1",
                padding_top="1em",
            ),
            rx.tabs.content(_v_iddoc_table(), value="tab2", padding_top="1em"),
            rx.tabs.content(_v_docedu_table(), value="tab3", padding_top="1em"),
            rx.tabs.content(_v_scp_table(), value="tab4", padding_top="1em"),
            rx.tabs.content(_v_rel_table(), value="tab5", padding_top="1em"),
            rx.tabs.content(_v_med_table(), value="tab6", padding_top="1em"),
            rx.tabs.content(_v_mil_table(), value="tab7", padding_top="1em"),
            rx.tabs.content(_v_sp_table(), value="tab8", padding_top="1em"),
            rx.tabs.content(_v_rz_table(), value="tab9", padding_top="1em"),
            default_value="tab1",
            width="100%",
        ),
        controls.empty_placeholder(),
    )


@require_login
def view_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Перегляд",
            rx.cond(
                ViewEntrantState.get_user_actions.contains(Actions.ENTRANT_DELETE),
                controls.delete_with_confirm(on_confirm=ViewEntrantState.on_click_delete),
            ),
            rx.cond(
                ViewEntrantState.get_user_actions.contains(Actions.ENTRANT_EDIT),
                controls.button_image_primary(name_icon="pencil_line", on_click=ViewEntrantState.on_click_edit),
            ),
            # «Назад» веде у список заявок, якщо картку відкрито звідти (DK-35), інакше — у список абітурієнтів.
            left=controls.button_back(ViewEntrantState.back_route),
            width="100%",
        ),
        rx.skeleton(view_page_content(), loading=ViewEntrantState.in_process, height="100%"),
    )


# ============================================================
# Form (Add / Edit) shared content
# ============================================================

def _photo_block() -> rx.Component:
    return rx.vstack(
        rx.upload(
            rx.cond(
                EntrantFormState.has_photo,
                rx.image(
                    src=EntrantFormState.photo_data_url,
                    border=f"1px solid {rx.color('accent', 9)}",
                    border_radius="5%",
                    width="100%",
                    height="100%",
                    object_fit="cover",
                ),
                rx.box(
                    rx.text("Перетягніть файл сюди або натисніть для вибору", text_align="center"),
                    border=f"1px solid {rx.color('accent', 9)}",
                    border_radius="5%",
                    width="100%",
                    height="100%",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
            ),
            id="entrant_photo_upload",
            border="None",
            padding="0",
            spacing="0",
            accept={".png": ["image/png"], ".jpg": ["image/jpeg"], ".jpeg": ["image/jpeg"]},
            max_files=1,
            width="300px",
            height="400px",
            on_drop=EntrantFormState.handle_photo_upload(rx.upload_files(upload_id="entrant_photo_upload")),
        ),
        rx.button("Видалити фото", on_click=EntrantFormState.clear_photo, color_scheme="red", width="300px"),
        spacing="2",
        align="center",
    )


def _personal_fields() -> rx.Component:
    return rx.vstack(
        rx.text("ID особи в ЄДБО:"),
        rx.input(
            value=EntrantFormState.edbo,
            on_change=EntrantFormState.set_edbo,
            disabled=~EntrantFormState.get_user_actions.contains(Actions.ENTRANT_EDIT_EDBO),
            width="100%",
        ),
        rx.cond(
            ~EntrantFormState.get_user_actions.contains(Actions.ENTRANT_EDIT_EDBO),
            rx.text(
                "Редагування ЄДБО недоступне — потрібне право «Редагування коду ЄДБО».",
                size="1",
                color="gray",
            ),
        ),
        rx.text("*ПІБ:"),
        rx.input(required=True, value=EntrantFormState.pib, on_change=EntrantFormState.set_pib, width="100%"),
        rx.text("Громадянство:"),
        rx.radio(CITIZENSHIP_OPTIONS, value=EntrantFormState.citizenship, on_change=EntrantFormState.set_citizenship, direction="row"),
        rx.text("*Стать:"),
        rx.radio(SEX_OPTIONS, value=EntrantFormState.sex, on_change=EntrantFormState.set_sex, direction="row"),
        rx.text("*Дата народження:"),
        rx.input(type="date", required=True, value=EntrantFormState.date_of_birth, on_change=EntrantFormState.set_date_of_birth, min="1900-01-01", max=EntrantFormState.max_birth_date, width="100%"),
        rx.text("Область, район, місто:"),
        rx.input(value=EntrantFormState.place_of_registration_city, on_change=EntrantFormState.set_place_of_registration_city, width="100%"),
        rx.text("*Адреса:"),
        rx.input(required=True, value=EntrantFormState.place_of_registration, on_change=EntrantFormState.set_place_of_registration, width="100%"),
        rx.text("ІПН:"),
        rx.input(
            value=EntrantFormState.mokpp,
            on_change=EntrantFormState.set_mokpp,
            max_length=10,
            input_mode="numeric",
            pattern=r"\d*",
            placeholder="10 цифр",
            width="100%",
        ),
        rx.text("E-mail:"),
        rx.input(type="email", value=EntrantFormState.email, on_change=EntrantFormState.set_email, width="100%"),
        rx.text("*Номер телефону:"),
        rx.input(required=True, value=EntrantFormState.phone_number, on_change=EntrantFormState.set_phone_number, width="100%"),
        rx.hstack(
            rx.text("Потреба в гуртожитку:"),
            rx.switch(checked=EntrantFormState.the_need_for_a_dormitory, on_change=EntrantFormState.set_the_need_for_a_dormitory),
        ),
        rx.text("*Джерело фінансування:"),
        _select(EntrantFormState.source_of_funding_options, EntrantFormState.id_source_of_funding_str, EntrantFormState.set_id_source_of_funding, width="100%"),
        rx.text("*База вступу:"),
        _select(EntrantFormState.entry_base_options, EntrantFormState.id_entry_base_str, EntrantFormState.set_id_entry_base, width="100%"),
        rx.text("*Статус заяви:"),
        _select(
            EntrantFormState.application_status_options,
            EntrantFormState.id_application_status_str,
            EntrantFormState.set_id_application_status,
            disabled=~EntrantFormState.get_user_actions.contains(Actions.ENTRANT_EDIT_STATUS),
            width="100%",
        ),
        rx.cond(
            ~EntrantFormState.get_user_actions.contains(Actions.ENTRANT_EDIT_STATUS),
            rx.text(
                "Зміна статусу недоступна — потрібне право «Зміна статусу картки абітурієнта».",
                size="1",
                color="gray",
            ),
        ),
        rx.text("Коментар:"),
        rx.text_area(value=EntrantFormState.comment, on_change=EntrantFormState.set_comment, resize="vertical", width="100%"),
        spacing="2",
        align="stretch",
        width="100%",
    )


# --- sub-entity tables (inside form) ---

def _sub_table_header(*titles: str) -> rx.Component:
    return rx.table.header(
        rx.table.row(*[rx.table.column_header_cell(t, color=rx.color("accent", 2)) for t in titles]),
        background_color=rx.color("accent", 9),
    )


def _action_cell(on_edit, on_delete) -> rx.Component:
    return rx.table.cell(
        rx.hstack(
            controls.button_image_primary(name_icon="pencil_line", on_click=on_edit),
            controls.delete_with_confirm(
                on_confirm=on_delete,
                description="Видалити цей запис зі списку?",
            ),
            spacing="2",
        )
    )


def _f_iddoc_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(EntrantFormState.identity_document_type_titles[item.id_type.to_string()]),
        rx.table.cell(rx.cond(item.series, item.series, "—") + " " + item.number),
        rx.table.cell(rx.cond(item.code, item.code, "—")),
        rx.table.cell(rx.cond(item.unzr, item.unzr, "—")),
        rx.table.cell(item.issued_by),
        rx.table.cell(item.date_of_issue),
        rx.table.cell(rx.cond(item.date_of_expiry, item.date_of_expiry, "—")),
        _action_cell(
            EntrantFormState.open_iddoc_edit(idx),
            EntrantFormState.delete_iddoc(idx),
        ),
    )


def _f_iddoc_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Документи підтвердження особи", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_iddoc_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.identity_documents.length() > 0,
            rx.table.root(
                _sub_table_header("Тип", "Серія/номер", "Код", "УНЗР", "Ким видано", "Дата видачі", "Дійсний до", "Дії"),
                rx.table.body(
                    rx.foreach(EntrantFormState.identity_documents, _f_iddoc_row),
                ),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_docedu_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.title),
        rx.table.cell(rx.cond(item.number, item.number, "—")),
        rx.table.cell(rx.cond(item.series, item.series, "—")),
        rx.table.cell(rx.cond(item.issued_by, item.issued_by, "—")),
        rx.table.cell(rx.cond(item.date_of_issue, item.date_of_issue, "—")),
        _action_cell(
            EntrantFormState.open_docedu_edit(idx),
            EntrantFormState.delete_docedu(idx),
        ),
    )


def _f_docedu_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Документи про освіту", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_docedu_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.documents_about_education.length() > 0,
            rx.table.root(
                _sub_table_header("Назва", "Номер", "Серія", "Ким видано", "Дата видачі", "Дії"),
                rx.table.body(
                    rx.foreach(EntrantFormState.documents_about_education, _f_docedu_row),
                ),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_mil_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.series),
        rx.table.cell(item.number),
        rx.table.cell(rx.cond(item.issued_by, item.issued_by, "—")),
        rx.table.cell(item.date_of_issue),
        _action_cell(
            EntrantFormState.open_mil_edit(idx),
            EntrantFormState.delete_mil(idx),
        ),
    )


def _f_mil_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Військовий облік", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_mil_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.military_accountings.length() > 0,
            rx.table.root(
                _sub_table_header("Серія", "Номер", "Ким видано", "Дата видачі", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.military_accountings, _f_mil_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_med_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.number),
        rx.table.cell(item.date_of_issue),
        _action_cell(
            EntrantFormState.open_med_edit(idx),
            EntrantFormState.delete_med(idx),
        ),
    )


def _f_med_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Медичні довідки", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_med_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.medical_references.length() > 0,
            rx.table.root(
                _sub_table_header("Номер", "Дата видачі", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.medical_references, _f_med_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_rel_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(EntrantFormState.kinship_titles[item.id_kinship.to_string()]),
        rx.table.cell(item.pib),
        rx.table.cell(item.phone_number),
        _action_cell(
            EntrantFormState.open_rel_edit(idx),
            EntrantFormState.delete_rel(idx),
        ),
    )


def _f_rel_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Контактні особи", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_rel_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.information_about_relatives.length() > 0,
            rx.table.root(
                _sub_table_header("Тип", "ПІБ", "Телефон", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.information_about_relatives, _f_rel_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_scp_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(EntrantFormState.special_condition_titles[item.id_special_condition]),
        rx.table.cell(rx.cond(item.title, item.title, "—")),
        rx.table.cell(rx.cond(item.number, item.number, "—")),
        rx.table.cell(item.date_of_issue),
        _action_cell(
            EntrantFormState.open_scp_edit(idx),
            EntrantFormState.delete_scp(idx),
        ),
    )


def _f_scp_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Спеціальні умови", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_scp_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.special_conditions_person.length() > 0,
            rx.table.root(
                _sub_table_header("Умова", "Назва", "Номер", "Дата видачі", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.special_conditions_person, _f_scp_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


def _f_sp_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.priority),
        rx.table.cell(EntrantFormState.speciality_labels[item.id_speciality.to_string()]),
        rx.table.cell(EntrantFormState.form_labels[item.id_form_of_study.to_string()]),
        _action_cell(
            EntrantFormState.open_sp_edit(idx),
            EntrantFormState.delete_sp(idx),
        ),
    )


def _f_group_block() -> rx.Component:
    """Вибір екзаменаційної групи ЗНО — під таблицею спеціальностей (DK-48).

    Кнопка «Визначити автоматично» зʼявляється, коли додано хоча б одну
    спеціальність. Ручний вибір групи лишається доступним завжди."""
    return rx.vstack(
        rx.heading("Група ЗНО", size="3", margin_top="0.5rem"),
        rx.hstack(
            _select(
                EntrantFormState.entrant_group_options,
                EntrantFormState.id_entrant_group_str,
                EntrantFormState.set_id_entrant_group,
                width="100%",
            ),
            rx.cond(
                EntrantFormState.specialties.length() > 0,
                controls.button_secondary(
                    rx.icon("wand-sparkles", size=18),
                    "Визначити автоматично",
                    on_click=EntrantFormState.on_click_autodetect_group,
                ),
            ),
            align="center",
            spacing="2",
            width="100%",
        ),
        rx.cond(
            EntrantFormState.pending_group_note != "",
            rx.text(EntrantFormState.pending_group_note, size="2", color=rx.color("accent", 11), weight="medium"),
        ),
        rx.cond(
            EntrantFormState.group_limit_warning != "",
            rx.text(EntrantFormState.group_limit_warning, size="2", color=rx.color("tomato", 11), weight="medium"),
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )


def _f_sp_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Спеціальності (пріоритетний список)", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_sp_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.specialties.length() > 0,
            rx.table.root(
                _sub_table_header("Пріоритет", "Спеціальність", "Форма навчання", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.specialties, _f_sp_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        _f_group_block(),
        width="100%",
    )


def _f_rz_row(item, idx: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(EntrantFormState.item_zno_titles[item.id_items_zno.to_string()]),
        rx.table.cell(item.points),
        _action_cell(
            EntrantFormState.open_rz_edit(idx),
            EntrantFormState.delete_rz(idx),
        ),
    )


def _f_rz_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Результати ЗНО", size="3"),
            rx.spacer(),
            controls.button_image_primary(name_icon="plus", on_click=EntrantFormState.open_rz_add),
            width="100%",
        ),
        rx.cond(
            EntrantFormState.results_zno.length() > 0,
            rx.table.root(
                _sub_table_header("Предмет", "Бали", "Дії"),
                rx.table.body(rx.foreach(EntrantFormState.results_zno, _f_rz_row)),
                variant="surface",
                width="100%",
            ),
            controls.empty_placeholder(),
        ),
        width="100%",
    )


# --- dialogs ---

def _dialog_buttons(on_save, on_cancel) -> rx.Component:
    return rx.hstack(
        rx.dialog.close(controls.button_secondary("Скасувати", on_click=on_cancel)),
        controls.button_primary("Зберегти", on_click=on_save),
        justify="end",
        spacing="2",
        width="100%",
    )


def _dlg_iddoc() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Документ підтвердження особи"),
            rx.vstack(
                rx.text("*Тип документа:"),
                _select(EntrantFormState.identity_document_type_options, EntrantFormState.iddoc_id_type_str, EntrantFormState.set_iddoc_id_type, width="100%"),
                rx.text("*Номер:"),
                rx.input(value=EntrantFormState.iddoc_number, on_change=EntrantFormState.set_iddoc_number, width="100%"),
                rx.text("Серія:"),
                rx.input(value=EntrantFormState.iddoc_series, on_change=EntrantFormState.set_iddoc_series, width="100%"),
                rx.text("Код:"),
                rx.input(value=EntrantFormState.iddoc_code, on_change=EntrantFormState.set_iddoc_code, width="100%"),
                rx.text("УНЗР:"),
                rx.input(value=EntrantFormState.iddoc_unzr, on_change=EntrantFormState.set_iddoc_unzr, width="100%"),
                rx.text("*Ким видано:"),
                rx.input(value=EntrantFormState.iddoc_issued_by, on_change=EntrantFormState.set_iddoc_issued_by, width="100%"),
                rx.hstack(
                    rx.vstack(
                        rx.text("*Дата видачі:"),
                        rx.input(type="date", value=EntrantFormState.iddoc_date_of_issue, on_change=EntrantFormState.set_iddoc_date_of_issue, key="iddoc_doi_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                        spacing="1",
                        align="stretch",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Дійсний до:"),
                        rx.input(type="date", value=EntrantFormState.iddoc_date_of_expiry, on_change=EntrantFormState.set_iddoc_date_of_expiry, key="iddoc_doe_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                        spacing="1",
                        align="stretch",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                _dialog_buttons(EntrantFormState.save_iddoc, EntrantFormState.close_iddoc),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.iddoc_open,
        on_open_change=EntrantFormState.set_iddoc_open,
    )


def _dlg_docedu() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Документ про освіту"),
            rx.vstack(
                rx.text("*Назва:"),
                rx.input(value=EntrantFormState.docedu_title, on_change=EntrantFormState.set_docedu_title, width="100%"),
                rx.text("Номер:"),
                rx.input(value=EntrantFormState.docedu_number, on_change=EntrantFormState.set_docedu_number, width="100%"),
                rx.text("Серія:"),
                rx.input(value=EntrantFormState.docedu_series, on_change=EntrantFormState.set_docedu_series, width="100%"),
                rx.text("Ким видано:"),
                rx.input(value=EntrantFormState.docedu_issued_by, on_change=EntrantFormState.set_docedu_issued_by, width="100%"),
                rx.text("Дата видачі:"),
                rx.input(type="date", value=EntrantFormState.docedu_date_of_issue, on_change=EntrantFormState.set_docedu_date_of_issue, key="docedu_doi_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                _dialog_buttons(EntrantFormState.save_docedu, EntrantFormState.close_docedu),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.docedu_open,
        on_open_change=EntrantFormState.set_docedu_open,
    )


def _dlg_mil() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Військовий облік"),
            rx.vstack(
                rx.text("*Серія:"),
                rx.input(value=EntrantFormState.mil_series, on_change=EntrantFormState.set_mil_series, width="100%"),
                rx.text("*Номер:"),
                rx.input(value=EntrantFormState.mil_number, on_change=EntrantFormState.set_mil_number, width="100%"),
                rx.text("Ким видано:"),
                rx.input(value=EntrantFormState.mil_issued_by, on_change=EntrantFormState.set_mil_issued_by, width="100%"),
                rx.text("*Дата видачі:"),
                rx.input(type="date", value=EntrantFormState.mil_date_of_issue, on_change=EntrantFormState.set_mil_date_of_issue, key="mil_doi_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                _dialog_buttons(EntrantFormState.save_mil, EntrantFormState.close_mil),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.mil_open,
        on_open_change=EntrantFormState.set_mil_open,
    )


def _dlg_med() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Медична довідка"),
            rx.vstack(
                rx.text("*Номер:"),
                rx.input(value=EntrantFormState.med_number, on_change=EntrantFormState.set_med_number, width="100%"),
                rx.text("*Дата видачі:"),
                rx.input(type="date", value=EntrantFormState.med_date_of_issue, on_change=EntrantFormState.set_med_date_of_issue, key="med_doi_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                _dialog_buttons(EntrantFormState.save_med, EntrantFormState.close_med),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.med_open,
        on_open_change=EntrantFormState.set_med_open,
    )


def _dlg_rel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Контактна особа"),
            rx.vstack(
                rx.text("*Тип родинного зв'язку:"),
                _select(EntrantFormState.kinship_options, EntrantFormState.rel_id_kinship_str, EntrantFormState.set_rel_id_kinship, width="100%"),
                rx.text("*ПІБ:"),
                rx.input(value=EntrantFormState.rel_pib, on_change=EntrantFormState.set_rel_pib, width="100%"),
                rx.text("*Телефон:"),
                rx.input(value=EntrantFormState.rel_phone_number, on_change=EntrantFormState.set_rel_phone_number, width="100%"),
                _dialog_buttons(EntrantFormState.save_rel, EntrantFormState.close_rel),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.rel_open,
        on_open_change=EntrantFormState.set_rel_open,
    )


def _dlg_scp() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Спеціальна умова"),
            rx.vstack(
                rx.text("*Спеціальна умова:"),
                _select(EntrantFormState.special_condition_options, EntrantFormState.scp_id_special_condition, EntrantFormState.set_scp_id_special_condition, width="100%"),
                rx.text("Назва документа:"),
                rx.input(value=EntrantFormState.scp_title, on_change=EntrantFormState.set_scp_title, width="100%"),
                rx.text("Номер документа:"),
                rx.input(value=EntrantFormState.scp_number, on_change=EntrantFormState.set_scp_number, width="100%"),
                rx.text("Опис:"),
                rx.text_area(value=EntrantFormState.scp_description, on_change=EntrantFormState.set_scp_description, width="100%"),
                rx.text("*Дата видачі:"),
                rx.input(type="date", value=EntrantFormState.scp_date_of_issue, on_change=EntrantFormState.set_scp_date_of_issue, key="scp_doi_" + EntrantFormState.date_nonce.to_string(), width="100%"),
                _dialog_buttons(EntrantFormState.save_scp, EntrantFormState.close_scp),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.scp_open,
        on_open_change=EntrantFormState.set_scp_open,
    )


def _dlg_sp() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Спеціальність (пріоритет)"),
            rx.vstack(
                rx.text("*Форма навчання:"),
                _select(
                    EntrantFormState.sp_form_options,
                    EntrantFormState.sp_id_form_of_study_str,
                    EntrantFormState.set_sp_id_form_of_study,
                    placeholder="Спочатку оберіть базу вступу",
                    disabled=EntrantFormState.id_entry_base == 0,
                    width="100%",
                ),
                rx.text("*Спеціальність:"),
                _select(
                    EntrantFormState.sp_speciality_options,
                    EntrantFormState.sp_combined,
                    EntrantFormState.set_sp_combined,
                    placeholder="Спочатку оберіть форму навчання",
                    disabled=EntrantFormState.sp_id_form_of_study == 0,
                    width="100%",
                ),
                rx.text("*Пріоритет:"),
                rx.input(type="number", value=EntrantFormState.sp_priority.to_string(), on_change=EntrantFormState.set_sp_priority, width="100%"),
                _dialog_buttons(EntrantFormState.save_sp, EntrantFormState.close_sp),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.sp_open,
        on_open_change=EntrantFormState.set_sp_open,
    )


def _rz_calc_panel() -> rx.Component:
    """Калькулятор комплексного балу (DK-47): середнє/сума введених компонентів."""
    return rx.box(
        rx.vstack(
            rx.text("Калькулятор комплексного балу", weight="bold", size="2"),
            rx.text(
                "Введіть компоненти через пробіл або кому (напр. бали предметів НМТ).",
                size="1", color="gray",
            ),
            rx.input(
                placeholder="150 160 170 180",
                value=EntrantFormState.rz_calc_components,
                on_change=EntrantFormState.set_rz_calc_components,
                width="100%",
            ),
            rx.hstack(
                rx.cond(
                    EntrantFormState.is_rz_calc_avg,
                    controls.button_primary("Середнє", on_click=EntrantFormState.set_rz_calc_mode("avg")),
                    controls.button_secondary("Середнє", on_click=EntrantFormState.set_rz_calc_mode("avg")),
                ),
                rx.cond(
                    EntrantFormState.is_rz_calc_avg,
                    controls.button_secondary("Сума", on_click=EntrantFormState.set_rz_calc_mode("sum")),
                    controls.button_primary("Сума", on_click=EntrantFormState.set_rz_calc_mode("sum")),
                ),
                spacing="2",
            ),
            rx.hstack(
                rx.text("Результат:", weight="bold"),
                rx.text(EntrantFormState.rz_calc_result_str),
                rx.spacer(),
                controls.button_secondary("Застосувати", on_click=EntrantFormState.rz_calc_apply),
                align="center",
                width="100%",
            ),
            spacing="2",
            align="stretch",
        ),
        padding="0.75em",
        border=f"1px solid {rx.color('accent', 6)}",
        border_radius="0.5em",
        width="100%",
    )


def _dlg_rz() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Результат ЗНО"),
            rx.vstack(
                rx.text("*Предмет:"),
                _select(EntrantFormState.item_zno_options, EntrantFormState.rz_id_items_zno_str, EntrantFormState.set_rz_id_items_zno, width="100%"),
                rx.hstack(
                    rx.text("*Бали:"),
                    rx.spacer(),
                    controls.button_image_secondary(name_icon="calculator", on_click=EntrantFormState.toggle_rz_calc),
                    align="center",
                    width="100%",
                ),
                rx.input(type="number", step="any", value=EntrantFormState.rz_points_input, on_change=EntrantFormState.set_rz_points_input, width="100%"),
                rx.text(EntrantFormState.rz_coefficient_hint, size="2", color="gray"),
                rx.cond(EntrantFormState.rz_calc_open, _rz_calc_panel()),
                _dialog_buttons(EntrantFormState.save_rz, EntrantFormState.close_rz),
                spacing="2",
                align="stretch",
            ),
        ),
        open=EntrantFormState.rz_open,
        on_open_change=EntrantFormState.set_rz_open,
    )


def _form_content() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("Персональна інформація", value="tab1"),
            rx.tabs.trigger("Паспортні дані", value="tab2"),
            rx.tabs.trigger("Документи про освіту", value="tab3"),
            rx.tabs.trigger("Спеціальні умови", value="tab4"),
            rx.tabs.trigger("Контактні особи", value="tab5"),
            rx.tabs.trigger("Медичні довідки", value="tab6"),
            rx.tabs.trigger("Військовий облік", value="tab7"),
            rx.tabs.trigger("Спеціальності", value="tab8"),
            rx.tabs.trigger("Результати ЗНО", value="tab9"),
        ),
        rx.tabs.content(
            rx.hstack(_photo_block(), _personal_fields(), align="start", spacing="4", width="100%"),
            value="tab1",
            padding_top="1em",
        ),
        rx.tabs.content(_f_iddoc_section(), value="tab2", padding_top="1em"),
        rx.tabs.content(_f_docedu_section(), value="tab3", padding_top="1em"),
        rx.tabs.content(_f_scp_section(), value="tab4", padding_top="1em"),
        rx.tabs.content(_f_rel_section(), value="tab5", padding_top="1em"),
        rx.tabs.content(_f_med_section(), value="tab6", padding_top="1em"),
        rx.tabs.content(_f_mil_section(), value="tab7", padding_top="1em"),
        rx.tabs.content(_f_sp_section(), value="tab8", padding_top="1em"),
        rx.tabs.content(_f_rz_section(), value="tab9", padding_top="1em"),
        default_value="tab1",
        width="100%",
    )


def _form_page() -> rx.Component:
    return rx.vstack(
        _form_content(),
        _dlg_iddoc(),
        _dlg_docedu(),
        _dlg_mil(),
        _dlg_med(),
        _dlg_rel(),
        _dlg_scp(),
        _dlg_sp(),
        _dlg_rz(),
        width="100%",
        spacing="3",
    )


# ============================================================
# Add / Edit pages
# ============================================================

@require_login
def add_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Додавання",
            controls.button_image_secondary(name_icon="circle_x", on_click=EntrantFormState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EntrantFormState.on_save),
            width="100%",
        ),
        rx.skeleton(_form_page(), loading=EntrantFormState.in_process, height="100%"),
    )


@require_login
def edit_page() -> rx.Component:
    return page_wrapper(
        header_subpage(
            "Редагування",
            controls.button_image_secondary(name_icon="circle_x", on_click=EntrantFormState.on_cancel),
            controls.button_image_primary(name_icon="save", on_click=EntrantFormState.on_save),
            width="100%",
        ),
        rx.skeleton(_form_page(), loading=EntrantFormState.in_process, height="100%"),
    )
