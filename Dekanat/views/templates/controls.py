import reflex as rx


def button_back(href: str, **prop):
    """Кнопка повернення на сторінку списку (іконка стрілки вліво, secondary стиль)."""
    return button_image_secondary(
        name_icon="arrow_left",
        on_click=rx.redirect(href),
        **prop,
    )


def button_filter_toggle(is_open, on_click, **prop):
    """Кнопка-перемикач панелі фільтрів. Підсвічується (primary) коли панель відкрита."""
    return rx.cond(
        is_open,
        button_image_primary(name_icon="funnel", on_click=on_click, **prop),
        button_image_secondary(name_icon="funnel", on_click=on_click, **prop),
    )


def filter_panel(is_open, *fields, on_clear=None) -> rx.Component:
    """Контейнер панелі фільтрів. Завжди присутній у DOM, видимість анімується через
    `max-height` та `opacity` від `is_open` (Var[bool])."""
    actions = rx.fragment()
    if on_clear is not None:
        actions = rx.hstack(
            rx.spacer(),
            button_secondary("Очистити", on_click=on_clear),
            width="100%",
        )
    return rx.box(
        rx.box(
            rx.vstack(
                *fields,
                actions,
                spacing="3",
                align="stretch",
                width="100%",
            ),
            padding="1rem",
            border_radius="0.6rem",
            background_color=rx.color("gray", 2),
            border=f"1px solid {rx.color('gray', 5)}",
            width="100%",
        ),
        # max-height як проксі для анімації висоти: 0 → велике значення.
        max_height=rx.cond(is_open, "60rem", "0"),
        opacity=rx.cond(is_open, "1", "0"),
        margin_top=rx.cond(is_open, "0", "-0.75rem"),
        overflow="hidden",
        transition="max-height 0.3s ease, opacity 0.25s ease, margin-top 0.3s ease",
        width="100%",
    )


def empty_placeholder(message: str = "Записи відсутні") -> rx.Component:
    """Заглушка для порожньої таблиці/списку. Стилізована під картку з пунктирною межею."""
    return rx.box(
        rx.text(message, color="gray", size="3", text_align="center"),
        padding="1.5rem",
        border=f"1px dashed {rx.color('gray', 7)}",
        border_radius="0.5rem",
        width="100%",
    )


def delete_with_confirm(
    on_confirm,
    title: str = "Підтвердження видалення",
    description: str = "Ви впевнені, що бажаєте видалити цей запис? Цю дію не можна буде скасувати.",
    trigger: rx.Component | None = None,
):
    """Кнопка видалення з підтвердженням через rx.alert_dialog.

    За замовчуванням trigger — це secondary-іконка зі смітником.
    `on_confirm` — обробник, який викликається лише після підтвердження користувачем.
    """
    if trigger is None:
        trigger = button_image_secondary(name_icon="trash_2")
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.flex(
                rx.alert_dialog.cancel(button_secondary("Скасувати")),
                rx.alert_dialog.action(button_primary("Видалити", color_scheme="red", on_click=on_confirm)),
                spacing="3",
                justify="end",
                margin_top="1rem",
            ),
            max_width="32rem",
        ),
    )


def button_primary(*args, **prop):
    return rx.button(
        *args,
        **prop,

        color="white",
        background_image=f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)"
    )

def button_secondary(*args, **prop):
    return rx.button(
        *args,
        **prop,

        variant="outline",
    )

def button_image_primary(name_icon: str="graduation-cap", icon_size: int=20, *args, **prop):
    return button_primary(
        rx.icon(name_icon, size=icon_size),
        *args,
        padding="0",
        width="2rem",
        height="2rem",
        **prop
    )

def button_image_secondary(name_icon: str="graduation-cap", icon_size: int=20, *args, **prop):
    return button_secondary(
        rx.icon(name_icon, size=icon_size),
        *args,
        padding="0",
        width="2rem",
        height="2rem",
        **prop
    ) 
