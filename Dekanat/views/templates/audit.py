"""Блок «Історія змін» (DK-55) — переиспользуемый компонент для сторінок записів.

Гейтиться правом `audit:view`. `audit_history_section` бере record_id з path-
параметра маршруту (сторінки перегляду сутностей). `audit_history_section_for_key`
приймає record_id явно (сторінки без [id] — рейтинг/звіт/налаштування).
"""

import reflex as rx

from Dekanat.actions import Actions
from Dekanat.states.app import AppState
from Dekanat.states.audit import AuditHistoryState, AuditRow
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


def _audit_row(row: AuditRow) -> rx.Component:
    # Наразі показуємо лише факт дії (без деталізації полів) — DK-55.
    return rx.box(
        rx.hstack(
            _action_badge(row),
            rx.text(row.actor, weight="medium", size="2"),
            rx.spacer(),
            rx.text(row.when, size="1", color=rx.color("gray", 10)),
            align="center",
            width="100%",
        ),
        padding="0.6rem 0.75rem",
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="0.5rem",
        background_color=rx.color("gray", 1),
        width="100%",
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


def audit_history_section(table_name: str = "", id_param: str = "id") -> rx.Component:
    """Блок історії для сторінок перегляду сутностей.

    Лише відображення — завантаження запускає `AuditHistoryState.load(...)`,
    доданий у `on_load` сторінки (`Dekanat/Dekanat.py`). Покладатись на `on_mount`
    компонента ненадійно: постійний layout не перемонтовує контент при навігації
    (див. DK-37). `table_name`/`id_param` лишаються в сигнатурі для сумісності.
    """
    return rx.cond(
        AppState.get_user_actions.contains(Actions.AUDIT_VIEW),
        _card(),
        rx.fragment(),
    )


def audit_history_section_for_key(table_name: str = "", record_id=None) -> rx.Component:
    """Те саме для сторінок без [id] (рейтинг/звіт): завантаження запускають
    обробники стейта через `AuditHistoryState.load_for_key(...)`."""
    return rx.cond(
        AppState.get_user_actions.contains(Actions.AUDIT_VIEW),
        _card(),
        rx.fragment(),
    )
