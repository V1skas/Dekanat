import reflex as rx

from Dekanat.states.app import AppState
from Dekanat.services.worker import WorkerService


class AccountSettingsState(AppState):
    """Налаштування власного облікового запису (DK-32). Доступно будь-якому
    автентифікованому користувачу — працює лише з `self.worker`, окремого
    права не потребує."""

    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    saving: bool = False

    @rx.event
    def on_load(self):
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""

    @rx.event
    def set_current_password(self, value: str):
        self.current_password = value

    @rx.event
    def set_new_password(self, value: str):
        self.new_password = value

    @rx.event
    def set_confirm_password(self, value: str):
        self.confirm_password = value

    @rx.event
    def on_save(self):
        if not self.current_password or not self.new_password or not self.confirm_password:
            yield rx.toast.warning("Заповніть усі поля.")
            return
        if self.new_password != self.confirm_password:
            yield rx.toast.warning("Новий пароль і підтвердження не збігаються.")
            return
        if self.worker is None:
            return

        self.saving = True
        yield
        try:
            ok = WorkerService().change_password(
                self.worker.id, self.current_password, self.new_password
            )
            if not ok:
                yield rx.toast.error("Поточний пароль неправильний.")
                return
            self.current_password = ""
            self.new_password = ""
            self.confirm_password = ""
            yield rx.toast.success("Пароль змінено.")
        except Exception:
            yield rx.toast.error("Під час зміни пароля сталася помилка. Спробуйте ще раз.")
        finally:
            self.saving = False
