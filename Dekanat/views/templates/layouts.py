from typing import List, Optional

import reflex as rx

from Dekanat import routes
from Dekanat.states.app import AppState
from Dekanat.declared.submenu import MenuItem


def _menu_visibility(items: List[MenuItem]):
    """OR over children's required_action. Returns None if any child is always-visible."""
    actions = [c.required_action for c in items]
    if not actions or any(a is None for a in actions):
        return None
    cond = AppState.get_user_actions.contains(actions[0])
    for a in actions[1:]:
        cond = cond | AppState.get_user_actions.contains(a)
    return cond


_ACCENT_GRADIENT = f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)"
_PANEL_SHADOW = "inset 0 0 0 0.1rem rgba(255, 255, 255, 0.4), 0.2rem 0.2rem 0.4rem 0 rgba(0, 0, 0, 0.25)"


def _user_popover() -> rx.Component:
    return rx.popover.root(
        rx.popover.trigger(
            rx.hstack(
                rx.text(AppState.worker_pib, size="4", weight="medium", color="white"),
                rx.avatar(fallback="ІІ", size="2", color_scheme="gray", variant="solid", radius="full"),
                align="center",
                spacing="3",
                cursor="pointer",
            ),
        ),
        rx.popover.content(
            rx.hstack(
                rx.icon("log-out", size=18, color="white"),
                rx.text("Вийти", size="3", weight="medium", color="white", white_space="nowrap"),
                align="center",
                spacing="2",
                padding_y="0.5rem",
                padding_x="0.75rem",
                border_radius="0.8rem",
                cursor="pointer",
                transition="background-color 0.2s ease",
                _hover={"background_color": "rgba(255, 255, 255, 0.15)"},
                on_click=AppState.logout,
            ),

            side="bottom",
            align="end",
            side_offset=20,

            padding="0.5rem",
            background_image=_ACCENT_GRADIENT,
            background_color="transparent",
            border="none",
            border_radius="1.2rem",
            box_shadow=_PANEL_SHADOW,
        ),
        open=AppState.user_menu_open,
        on_open_change=AppState.set_user_menu_open,
    )


def header() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.hstack(
                rx.icon("graduation-cap", size=32, color="white"),
                rx.heading("Деканат", size="5", weight="bold", color="white"),
                align="center",
                spacing="3",
            ),
            # Завжди веде на головний dashboard, незалежно від поточного розділу.
            href=routes.DASHBOARD,
            underline="none",
        ),

        rx.box(
            rx.heading(
                AppState.section_title,
                size="6",
                weight="bold",
                color="white",
                white_space="nowrap",
                overflow="hidden",
                text_overflow="ellipsis",
            ),
            flex="1",
            text_align="center",
            padding_left="1rem",
            padding_right="1rem",
            min_width="0",
        ),

        _user_popover(),

        width="100%",
        height="3.7rem",
        padding_left="1.2rem",
        padding_right="1.2rem",
        align="center",

        background_image=_ACCENT_GRADIENT,
        border_radius="1.2rem",
        box_shadow=_PANEL_SHADOW,
    )

def sidebar_item(item: MenuItem, indent: bool = False) -> rx.Component:
    # Пункти з прапором dashboard_only живуть лише на dashboard-сторінці розділу.
    if item.dashboard_only:
        return rx.fragment()
    rendered = rx.link(
        rx.hstack(
            rx.icon(item.icon, size=24, color="white", flex_shrink="0"),
            rx.cond(
                AppState.sidebar_open,
                rx.text(
                    item.label,
                    size="3",
                    weight="medium",
                    color="white",
                    flex="1",
                    min_width="0",
                    style={"overflow_wrap": "anywhere", "word_break": "break-word"},
                ),
            ),
            width="100%",
            # Фіксована внутрішня ширина дорівнює ширині розгорнутої панелі — щоб під час
            # анімації grid-треку текст усередині не перекомпоновувався (відкривається з-під overflow:hidden).
            min_width="14rem",
            padding_y="0.7rem",
            padding_x="0.75rem",
            padding_left=("2rem" if indent else "0.75rem"),
            align="center",
            spacing="3",
            border_radius="1.2rem",
            overflow="hidden",
            transition="all 0.2s ease",
            _hover={
                "background_color": "rgba(255, 255, 255, 0.15)",
            },
        ),
        href=item.url or "#",
        width="100%",
        underline="none",
    )
    if item.required_action is None:
        return rendered
    return rx.cond(
        AppState.get_user_actions.contains(item.required_action),
        rendered,
        rx.fragment(),
    )

def sidebar_group(item: MenuItem) -> rx.Component:
    expanded = AppState.expanded_groups.contains(item.label)

    # Внутрішня частина head — однакова для обох режимів.
    head_inner = rx.hstack(
        rx.icon(item.icon, size=24, color="white", flex_shrink="0"),
        rx.cond(
            AppState.sidebar_open,
            rx.hstack(
                rx.text(
                    item.label,
                    size="3",
                    weight="medium",
                    color="white",
                    flex="1",
                    min_width="0",
                    style={"overflow_wrap": "anywhere", "word_break": "break-word"},
                ),
                rx.icon(
                    "chevron-right",
                    size=18, color="white", flex_shrink="0",
                    transform=rx.cond(expanded, "rotate(90deg)", "rotate(0deg)"),
                    transition="transform 0.2s ease",
                ),
                width="100%",
                align="center",
                spacing="2",
            ),
        ),
        width="100%",
        # Фіксована внутрішня ширина дорівнює ширині розгорнутої панелі — щоб під час
        # анімації grid-треку текст усередині не перекомпоновувався.
        min_width="14rem",
        padding_y="0.7rem",
        padding_x="0.75rem",
        align="center",
        spacing="3",
        border_radius="1.2rem",
        cursor="pointer",
        overflow="hidden",
        transition="all 0.2s ease",
        _hover={"background_color": "rgba(255, 255, 255, 0.15)"},
    )

    # Розгорнутий sidebar — клік по голові тогглить розкриття дітей.
    head_toggle = rx.box(head_inner, on_click=AppState.toggle_group(item.label), width="100%")
    # Згорнутий sidebar — діти все одно сховані; клік по групі веде на її dashboard.
    head_link = rx.link(head_inner, href=item.url or "#", underline="none", width="100%")
    head = rx.cond(AppState.sidebar_open, head_toggle, head_link)

    children_visible = expanded & AppState.sidebar_open
    children_open = rx.box(
        rx.vstack(
            *[sidebar_item(c, indent=True) for c in item.children],
            spacing="0",
            width="100%",
        ),
        max_height=rx.cond(children_visible, "500px", "0px"),
        opacity=rx.cond(children_visible, "1", "0"),
        overflow="hidden",
        transition="max-height 0.3s ease, opacity 0.2s ease",
        width="100%",
    )

    rendered = rx.vstack(head, children_open, spacing="0", width="100%")
    visibility = _menu_visibility(item.children)
    if visibility is None:
        return rendered
    return rx.cond(visibility, rendered, rx.fragment())

def render_menu_item(item: MenuItem) -> rx.Component:
    if item.children:
        return sidebar_group(item)
    return sidebar_item(item)

def sidebar(menu: List[MenuItem]) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("menu", size=28, color="white", cursor="pointer", flex_shrink="0"),
            rx.cond(
                AppState.sidebar_open,
                rx.heading("Меню", size="5", weight="bold", color="white"),
                rx.fragment()
            ),
            align="center",
            spacing="3",
            padding_y="0.7rem",
            padding_x="0.7rem",
            width="100%",
            flex_shrink="0",
            on_click=AppState.toggle_sidebar
        ),

        rx.vstack(
            *[render_menu_item(item) for item in menu],
            spacing="0",
            width="100%",
            flex="1",
            min_height="0",
            overflow_y="auto",
            overflow_x="hidden",
            style={
                "scrollbar_width": "thin",
                "scrollbar_color": "rgba(255, 255, 255, 0.35) transparent",
                "&::-webkit-scrollbar": {
                    "width": "6px",
                },
                "&::-webkit-scrollbar-track": {
                    "background": "transparent",
                },
                "&::-webkit-scrollbar-thumb": {
                    "background_color": "rgba(255, 255, 255, 0.35)",
                    "border_radius": "3px",
                },
                "&::-webkit-scrollbar-thumb:hover": {
                    "background_color": "rgba(255, 255, 255, 0.6)",
                },
            },
        ),

        spacing="3",

        background_image=f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)",
        border_radius="1.2rem",
        box_shadow="inset 0 0 0rem 0.1rem rgba(255, 255, 255, 0.4), 0.2rem 0.2rem 0.4rem 0 rgba(0, 0, 0, 0.25)",

        padding_top="15px",
        padding_bottom="15px",
        padding_left="8px",
        padding_right="8px",
        height="100%",
        width="100%",
        min_height="0",
        overflow="hidden",
    )

def page_wrapper(
    page_header: rx.Component,
    page_content: rx.Component,
    filter_panel: Optional[rx.Component] = None,
) -> rx.Component:
    """Каркас отдельной страницы.

    Внешний chrome (шапка/сайдбар) приходит из app_wraps и не пересоздаётся при навигации.
    Если передан `filter_panel`, он рендерится между шапкой и контентом — собственную видимость
    (`rx.cond` на state.<filter_open>`) панель должна обеспечить сама.
    """
    children: List[rx.Component] = [page_header]
    if filter_panel is not None:
        children.append(filter_panel)
    children.append(
        rx.box(
            page_content,
            flex="1",
            height="100%",
            width="100%",
            overflow_y="auto",
        )
    )
    return rx.vstack(
        *children,
        flex="1",
        width="100%",
        height="100%",
        spacing="3",
    )

def header_subpage(title: str, *args, left: Optional[rx.Component] = None, **prop) -> rx.Component:
    """Шапка підсторінки. `left=` додає елемент ліворуч від заголовку (наприклад, кнопку «назад»)."""
    heading = rx.heading(
        title,
        size="8",
        weight="bold",
        background_image=_ACCENT_GRADIENT,
        background_clip="text",
        color="transparent",
        white_space="nowrap",
    )

    children: List[rx.Component] = []
    if left is not None:
        children.append(left)
    children.append(heading)
    children.append(rx.spacer())
    children.extend(args)

    return rx.hstack(
        *children,
        align="center",
        position="relative",
        padding_bottom="0.5rem",
        style={
            "&::after": {
                "content": '""',
                "position": "absolute",
                "left": "0",
                "bottom": "0",
                "width": "100%",
                "height": "0.2rem",
                "background": _ACCENT_GRADIENT,
                "border_radius": "2px",
            }
        },
        **prop,
    )
