from typing import List, Tuple

import reflex as rx

from Dekanat.states.app import AppState

def header(title: str) -> rx.Component:
    return rx.hstack(
        # ... (Вся левая часть, отступы и профиль остаются без изменений) ...
        rx.link(
            rx.hstack(
                rx.icon("graduation-cap", size=32, color="white"),
                rx.heading("Деканат", size="5", weight="bold", color="white"),
                align_items="center",
                spacing="3",
            ),
            href="/", 
            underline="none",
        ),
        
        rx.spacer(),
        rx.heading(title, size="7", weight="bold", color="white"),
        rx.spacer(),
        
        rx.hstack(
            rx.text("Іванов І.І.", size="4", weight="medium", color="white"),
            rx.avatar(fallback="ІІ", size="2", color_scheme="gray", variant="solid", radius="full"),
            align_items="center",
            spacing="3",
            cursor="pointer",
        ),

        # Габариты (твои)
        width="98vw",
        height="3.7rem",
        margin_top="1vh",
        margin_bottom="1vh", 
        margin_left="auto",
        margin_right="auto",
        padding_left="1vw",
        padding_right="1vw",
        align_items="center", 

        # --- ДИЗАЙН (Добавляем глубину) ---
        # 1. Легкий градиент (от 8-го к 10-му оттенку акцентного цвета)
        background_image=f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)", 
        border_radius="1.2rem",                         
        
        # 2. Многослойная тень: первая для объема, вторая для мягкого рассеивания
        box_shadow="inset 0 0 0 0.1rem rgba(255, 255, 255, 0.4), 0.2rem 0.2rem 0.4rem 0 rgba(0, 0, 0, 0.25)",
        
        # 3. Эффект блика на верхнем и левом крае (свет падает сверху-слева)
        #border_top="1px solid rgba(255, 255, 255, 0.2)",
        #border_left="1px solid rgba(255, 255, 255, 0.1)",
    )

def sidebar_item(text: str, icon_name: str, url: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            # Иконка теперь белая
            rx.icon(icon_name, size=24, color="white", flex_shrink="0"),
            rx.cond(
                AppState.sidebar_open,
                # Текст теперь тоже белый
                rx.text(text, size="3", weight="medium", color="white", white_space="nowrap"),
                #   rx.fragment()
            ),
            width="100%",
            padding_y="0.7rem",
            padding_x="0.75rem",
            align_items="center",
            spacing="3",
            border_radius="1.2rem",
            
            transition="all 0.2s ease",
            
            # НОВЫЙ ХОВЕР: Так как фон темный, мы используем полупрозрачный белый цвет
            # для эффекта выделения при наведении
            _hover={
                "background_color": "rgba(255, 255, 255, 0.15)", 
            },
        ),
        href=url,
        width="100%",
        underline="none",
        #padding_x="10px",
    )

def sidebar(menu: List[Tuple[str, str, str]]) -> rx.Component:
    return rx.vstack(
        # ... (Содержимое меню остается твоим) ...
        rx.hstack(
            rx.icon("menu", size=28, color="white", cursor="pointer", flex_shrink="0"),
            rx.cond(
                AppState.sidebar_open,
                rx.heading("Головна", size="5", weight="bold", color="white"),
                rx.fragment()
            ),
            align_items="center",
            spacing="3",
            padding_y="0.7rem",
            padding_x="0.7rem",
            width="100%",
            on_click=AppState.toggle_sidebar
        ),
        
        rx.vstack(
            rx.foreach(menu, lambda item: sidebar_item(item[0], item[1], item[2])),
            spacing="0",

            width="100%",
            height="100%"
        ),
        
        spacing="3",
        
        # --- ДИЗАЙН (Добавляем глубину) ---
        # 1. Тот же градиент для единообразия
        background_image=f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)",
        border_radius="1.2rem",                         
        
        # 2. Тень уходит чуть больше вправо и вниз (5px по оси X)
        box_shadow="inset 0 0 0rem 0.1rem rgba(255, 255, 255, 0.4), 0.2rem 0.2rem 0.4rem 0 rgba(0, 0, 0, 0.25)",
        
        # 3. Блик света на гранях
        #border_top="1px solid rgba(255, 255, 255, 0.2)",
        #border_left="1px solid rgba(255, 255, 255, 0.1)",
        #border_right="1px solid rgba(0, 0, 0, 0.05)", # Легкое затемнение правого края
        
        # Габариты (твои)
        margin="10px", 
        margin_left="1vw",
        margin_top="1vh",
        margin_bottom="1vh", 
        padding_top="15px", # Исправил опечатку paddind_top
        padding_bottom="15px",
        padding_left="8px",
        padding_right="8px",
        height="96%",
        width=rx.cond(AppState.sidebar_open, "15rem", "4.2rem"),
        transition="width 0.3s ease-in-out",
        flex_shrink="0",
        overflow_x="hidden",
        overflow_y="auto",
    )

def base_layout(page_header: rx.Component, page_content: rx.Component, global_title: str, sidebar_menu: List[Tuple[str, str, str]]) -> rx.Component:
    """Главный каркас приложения (Desktop Style)"""
    
    return rx.vstack(
        # --- СТРОКА 1: Шапка ---
        header(global_title),
        
        # --- СТРОКА 2: Рабочая область (Меню + Контент) ---
        rx.hstack(
            # --- КОНТЕЙНЕР ДЛЯ КОНТЕНТА СТРАНИЦЫ ---
            sidebar(sidebar_menu),
            rx.vstack(
                page_header,
                rx.box(
                    page_content,

                    flex="1", # 5. Забирает всю оставшуюся ширину
                    height="100%", # Забирает всю доступную высоту
                    width="100%",
                    overflow_y="auto", # 5. ГЛАВНАЯ МАГИЯ: Скроллбар появляется ТОЛЬКО здесь!
                    #padding="30px",
                    #background_color="#ffffff",
                ),

                margin_right="1vw",
                margin_top="1vh",
                margin_bottom="1vh", 
                padding="0.7rem",

                width="100%",
                height="100%"
            ),
            
            width="100%",
            flex="1", # Рабочая область забирает всю высоту, оставшуюся от шапки
            overflow="hidden", # Прячем лишнее, чтобы hstack не сломал верстку
            spacing="0",
        ),
        
        # --- НАСТРОЙКИ САМОГО ГЛАВНОГО ОКНА ---
        width="100vw",
        height="100vh", # 6. Жестко привязываем к размеру экрана
        overflow="hidden", # 7. ЗАПРЕЩАЕМ появление глобального скроллбара в браузере
        spacing="0",
    )

def header_subpage(*args, **prop) -> rx.Component:
    return rx.hstack(
        rx.heading("Tittle page", size="8", weight="bold", background_image=f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)", background_clip="text", color="transparent"),
        rx.spacer(),
        *args,
        **prop,

        position="relative",
        padding_bottom="0.5rem",

        style={
            "&::after": {
                "content": '""', # Создаем пустой элемент
                "position": "absolute",
                "left": "0",
                "bottom": "0",
                "width": "100%", # Линия на всю ширину
                "height": "0.2rem", # Толщина линии
                # Твой новый градиент для линии
                "background": f"linear-gradient(135deg, {rx.color('accent', 11)} 20%, {rx.color('accent', 9)} 65%)",
                "border_radius": "2px",
            }
        },
    )
