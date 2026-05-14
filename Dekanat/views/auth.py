import reflex as rx

from Dekanat.states.app import AppState
from Dekanat.states.auth import AuthState
from Dekanat import routes

def login_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.center(
                rx.heading(
                    "Увійдіть у свій обліковий запис",

                    size="6",
                    as_="h2",
                    text_align="center",
                    width="100%",
                ),

                direction="column",
                spacing="5",
                width="100%",
            ),
            rx.vstack(
                rx.input(
                    rx.input.slot(rx.icon("user")),

                    value=AuthState.login,
                    on_change=AuthState.on_change_login,

                    placeholder="Логін",
                    size="3",
                    width="100%",
                ),
                rx.input(
                    rx.input.slot(rx.icon("lock")),

                    value=AuthState.password,
                    on_change=AuthState.on_change_password,

                    placeholder="Пароль",
                    type="password",
                    size="3",
                    width="100%",
                ),
                rx.button("Увійти", type="submit", size="3", width="100%", on_click=AuthState.on_auth),

                spacing="3",
                width="100%",
            ),
            rx.cond(AuthState.error_text.is_not_none(),
                    rx.callout(
                        AuthState.error_text,
                        
                        icon="triangle_alert",
                        role="alert",
                        color_scheme="red",
                        width="100%",
                    ),
            )
        ),

        max_width="28em",
        size="4",
        width="100%",
    )

def index() -> rx.Component:
    return rx.center(
            rx.heading("Деканат", as_="h1", size="9"),
            login_card(),

            height="100vh",
            direction="column",
            spacing="5",
    )

def require_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Decorator to require authentication before rendering a page.

    If the user is not authenticated, then redirect to the login page.

    Args:
        page: The page to wrap.

    Returns:
        The wrapped page component.
    """

    def protected_page():
        return rx.cond(
            AppState.is_auth,  # type: ignore
            page(),
            rx.center(
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Завантаження...", size="3", on_mount=AppState.require_auth),  # type: ignore
                ),
                height="100%",
                width="100%",
            ),
        )

    protected_page.__name__ = page.__name__
    return protected_page
