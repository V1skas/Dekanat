import reflex as rx


def button_back(href: str, **prop):
    """Кнопка повернення на сторінку списку (іконка стрілки вліво, secondary стиль)."""
    return button_image_secondary(
        name_icon="arrow_left",
        on_click=rx.redirect(href),
        **prop,
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
