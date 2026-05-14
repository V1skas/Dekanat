import reflex as rx

from typing import Sequence, Set

from Dekanat.models import ActionModel
from Dekanat.services.action import ActionService


class ActionSelectorState(rx.State):
    items: Sequence[ActionModel] = []
    selected_items: Set[int] = set()
    in_process = True

    def _reload_items(self):
        service = ActionService()
        self.items = service.get_list_items()

    @rx.event
    def on_load(self, selected_items: Set[int]):
        try:
            self.in_process = True
            self.selected_items = selected_items
            self._reload_items()
            self.in_process = False
        except:
            yield rx.toast.error("Під час завантаження даних виникла помилка, спробуйте ще раз.")
        return

# TODO: Остановился на придумывании выбора разрешений для роли/пользователя
