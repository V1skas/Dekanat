import reflex as rx

from Dekanat.states.app import AppState
from Dekanat.declared.submenu import MAIN
from Dekanat.views.tamplates.layouts import header, sidebar


def app_shell_wrap(_stateful: bool) -> rx.Component:
    """Постоянный wrapper над <Outlet/>: содержит шапку и сайдбар, которые не пересоздаются при навигации."""
    chrome_visible = AppState.is_auth
    return rx.box(
        rx.box(
            header(),
            display=rx.cond(chrome_visible, "flex", "none"),
            grid_area="header",
            width="100%",
            height="100%",
        ),
        rx.box(
            sidebar(MAIN),
            display=rx.cond(chrome_visible, "flex", "none"),
            grid_area="sidebar",
            width="100%",
            height="100%",
        ),
        # Третий ребёнок (content_area_wrap) добавляется автоматически через app_wraps chain.

        display="grid",
        grid_template_areas='"header header" "sidebar content"',
        grid_template_columns=rx.cond(
            chrome_visible,
            rx.cond(AppState.sidebar_open, "15rem 1fr", "4.2rem 1fr"),
            "0 1fr",
        ),
        grid_template_rows=rx.cond(chrome_visible, "3.7rem 1fr", "0 1fr"),
        grid_gap="1vh 1vw",
        padding=rx.cond(chrome_visible, "1vh 1vw", "0"),
        height="100vh",
        width="100vw",
        overflow="hidden",
        transition="grid-template-columns 0.3s ease-in-out",
    )


def content_area_wrap(_stateful: bool) -> rx.Component:
    """Контейнер, в который React-Router помещает текущую страницу (через innermost AppWrap → {children})."""
    return rx.box(
        # Сюда appendится Overlay → ExtraOverlay → AppWrap({children}) = текущая страница.

        grid_area="content",
        overflow_y="auto",
        height="100%",
        width="100%",
    )
