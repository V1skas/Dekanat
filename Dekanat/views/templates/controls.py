import reflex as rx

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
