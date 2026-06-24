import reflex as rx

from typing import List

from Dekanat import routes
from Dekanat.declared.submenu import MAIN, MenuItem, find_group_by_url
from Dekanat.states.app import AppState
from Dekanat.views.templates.layouts import page_wrapper, header_subpage, _menu_visibility
from Dekanat.views.auth import require_login


# Градієнт акценту — той самий, що у шапці/сайдбарі (див. layouts.py).
_ACCENT_GRADIENT = f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)"


def _card(item: MenuItem) -> rx.Component:
    """Карточка пункту меню: іконка + назва, сама — як посилання."""
    return rx.link(
        rx.vstack(
            rx.icon(item.icon, size=48, color="white"),
            rx.text(
                item.label,
                size="4",
                weight="bold",
                color="white",
                text_align="center",
                style={"overflow_wrap": "anywhere", "word_break": "break-word"},
            ),
            spacing="3",
            align="center",
            justify="center",
            padding="1.5rem",
            width="12rem",
            height="10rem",
            border_radius="1.2rem",
            background_image=_ACCENT_GRADIENT,
            box_shadow="0.2rem 0.2rem 0.4rem 0 rgba(0, 0, 0, 0.25)",
            transition="transform 0.15s ease, box-shadow 0.15s ease",
            _hover={
                "transform": "translateY(-0.2rem)",
                "box_shadow": "0.3rem 0.3rem 0.6rem 0 rgba(0, 0, 0, 0.35)",
            },
        ),
        href=item.url or "#",
        underline="none",
    )


def _card_with_permission(item: MenuItem) -> rx.Component:
    """Обгортка картки під перевірку прав:
    * лист із власним `required_action` — показуємо за наявності цього права;
    * група (без власного права, але з дітьми) — показуємо, лише якщо доступне
      хоча б одне дитя (OR по їх `required_action`), як у боковому меню;
    * інакше (немає ні права, ні дітей) — показуємо завжди."""
    if item.required_action is not None:
        return rx.cond(
            AppState.get_user_actions.contains(item.required_action),
            _card(item),
            rx.fragment(),
        )
    if item.children:
        visibility = _menu_visibility(item.children)
        if visibility is not None:
            return rx.cond(visibility, _card(item), rx.fragment())
    return _card(item)


def _cards_grid(items: List[MenuItem]) -> rx.Component:
    return rx.flex(
        *[_card_with_permission(it) for it in items],
        wrap="wrap",
        spacing="4",
        justify="center",
        width="100%",
    )


# ============================================================
# Головний dashboard (приветствие + картки розділів)
# ============================================================

def main_dashboard_content() -> rx.Component:
    return rx.vstack(
        rx.heading("Вітаю в системі Деканат!", size="8", text_align="center"),
        rx.text(
            "Оберіть розділ нижче або скористайтесь боковим меню.",
            size="3",
            color="gray",
            text_align="center",
        ),
        rx.box(height="1rem"),
        _cards_grid(MAIN),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
        height="100%",
    )


@require_login
def dashboard_page() -> rx.Component:
    return page_wrapper(
        rx.box(),
        main_dashboard_content(),
    )


# ============================================================
# Section dashboard'и (одна сторінка на розділ верхнього рівня)
# ============================================================

def _section_dashboard_content(group_url: str) -> rx.Component:
    group = find_group_by_url(group_url)
    if group is None:
        return rx.text("Розділ не знайдено.")
    return rx.vstack(
        header_subpage(group.label, width="100%"),
        rx.box(
            _cards_grid(group.children),
            flex="1",
            width="100%",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        spacing="3",
        align="center",
        width="100%",
        height="100%",
    )


def _section_page(group_url: str) -> rx.Component:
    return page_wrapper(
        rx.box(),
        _section_dashboard_content(group_url),
    )


@require_login
def base_dashboard_page() -> rx.Component:
    return _section_page(routes.DASHBOARD_BASE)


@require_login
def contingent_dashboard_page() -> rx.Component:
    return _section_page(routes.DASHBOARD_CONTINGENT)


@require_login
def admission_commission_dashboard_page() -> rx.Component:
    return _section_page(routes.DASHBOARD_ADMISSION_COMMISSION)


@require_login
def admin_dashboard_page() -> rx.Component:
    return _section_page(routes.DASHBOARD_ADMIN)


@require_login
def reporting_dashboard_page() -> rx.Component:
    return _section_page(routes.DASHBOARD_REPORTING)
