"""Блок «Історія змін» (DK-55/DK-56) — переиспользуемый компонент для сторінок
записів.

Право на сам блок і право на деталізацію — окремі й повністю незалежні:
`audit_history_section(view_action, detail_action)` гейтить видимість блоку
лише `view_action`; `detail_action` керує лише можливістю розгорнути рядок
(шеврон і клік з'являються тільки з цим правом). `audit_history_section_for_key`
— те саме для сторінок без `[id]` (рейтинг/звіт).
"""

import reflex as rx

from Dekanat.states.app import AppState
from Dekanat.states.audit import AuditHistoryState, AuditRow
from Dekanat.audit import FieldRow
from Dekanat.views.templates import controls


def _action_badge(row: AuditRow) -> rx.Component:
    color = rx.match(
        row.kind,
        ("create", "grass"),
        ("delete", "red"),
        ("generate", "blue"),
        ("assign", "iris"),
        "amber",  # update (за замовчуванням)
    )
    return rx.badge(row.action_label, color_scheme=color, variant="soft", size="1")


def _field_row(fr: FieldRow) -> rx.Component:
    """Рядок деталізації. Конвенція визначається наявністю old/new (без enum):
    лише `old`+`new` → diff (старе закреслене червоне → нове жирне зелене);
    лише `new` → значення «додано» (зелене); лише `old` → «видалено» (червоне,
    закреслене); порожній `label` → нейтральний текст-примітка."""
    return rx.cond(
        fr.label == "",
        rx.text(fr.text, size="2", color=rx.color("gray", 11)),
        rx.hstack(
            rx.text(fr.label + ":", size="2", weight="medium", color=rx.color("gray", 11), white_space="nowrap"),
            rx.cond(
                fr.old != "",
                rx.text(fr.old, size="2", color=rx.color("red", 11), text_decoration="line-through"),
            ),
            rx.cond(
                (fr.old != "") & (fr.new != ""),
                rx.icon("arrow-right", size=14, color=rx.color("gray", 9)),
            ),
            rx.cond(
                fr.new != "",
                rx.text(fr.new, size="2", weight="bold", color=rx.color("grass", 11)),
            ),
            spacing="2",
            wrap="wrap",
            align="center",
            width="100%",
        ),
    )


def _audit_row(row: AuditRow) -> rx.Component:
    is_expanded = AuditHistoryState.expanded_ids.contains(row.id)
    header = rx.hstack(
        _action_badge(row),
        rx.text(row.actor, weight="medium", size="2"),
        rx.spacer(),
        rx.text(row.when, size="1", color=rx.color("gray", 10)),
        rx.cond(
            AuditHistoryState.can_detail,
            rx.icon(
                rx.cond(is_expanded, "chevron-up", "chevron-down"),
                size=16,
                color=rx.color("gray", 9),
            ),
        ),
        align="center",
        width="100%",
    )
    return rx.box(
        header,
        rx.cond(
            is_expanded,
            rx.vstack(
                rx.foreach(row.details, _field_row),
                spacing="1",
                align="start",
                width="100%",
                margin_top="0.5rem",
                padding_top="0.5rem",
                border_top=f"1px dashed {rx.color('gray', 5)}",
            ),
            rx.fragment(),
        ),
        padding="0.6rem 0.75rem",
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="0.5rem",
        background_color=rx.color("gray", 1),
        width="100%",
        cursor=rx.cond(AuditHistoryState.can_detail, "pointer", "default"),
        on_click=AuditHistoryState.toggle_row(row.id),
    )


def _history_body() -> rx.Component:
    return rx.cond(
        AuditHistoryState.rows.length() > 0,
        rx.vstack(
            rx.foreach(AuditHistoryState.rows, _audit_row),
            spacing="2",
            width="100%",
        ),
        controls.empty_placeholder("Історія відсутня"),
    )


def _card() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("history", size=20, color=rx.color("accent", 9)),
            rx.heading("Історія змін", size="4"),
            align="center",
            spacing="2",
            margin_bottom="0.75rem",
        ),
        rx.skeleton(_history_body(), loading=AuditHistoryState.loading),
        width="100%",
        margin_top="1.5rem",
        padding_top="1rem",
        border_top=f"1px solid {rx.color('gray', 6)}",
    )


def audit_history_section(view_action: str, detail_action: str) -> rx.Component:
    """Блок історії для сторінок перегляду сутностей.

    Лише відображення — завантаження запускає `AuditHistoryState.load(...)`,
    доданий у `on_load` сторінки (`Dekanat/Dekanat.py`). Покладатись на `on_mount`
    компонента ненадійно: постійний layout не перемонтовує контент при навігації
    (див. DK-37).
    """
    return rx.cond(
        AppState.get_user_actions.contains(view_action),
        _card(),
        rx.fragment(),
    )


def audit_history_section_for_key(view_action: str, detail_action: str) -> rx.Component:
    """Те саме для сторінок без [id] (рейтинг/звіт): завантаження запускають
    обробники стейта через `AuditHistoryState.load_for_key(...)`."""
    return rx.cond(
        AppState.get_user_actions.contains(view_action),
        _card(),
        rx.fragment(),
    )
