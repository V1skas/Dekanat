import reflex as rx

from Dekanat.states.app import AppState
from Dekanat.feedback import FeedbackService
from Dekanat.utils.background import run_blocking


class FeedbackState(AppState):
    """Діалог зворотного зв'язку (DK-32). Доступно будь-якому автентифікованому
    користувачу — окремого права не потребує."""

    feedback_open: bool = False
    feedback_text: str = ""
    feedback_sending: bool = False

    @rx.event
    def set_feedback_open(self, value: bool):
        self.feedback_open = value

    @rx.event
    def set_feedback_text(self, value: str):
        self.feedback_text = value

    @rx.event
    def open_feedback(self):
        self.feedback_text = ""
        self.feedback_open = True

    @rx.event
    async def on_submit(self):
        """Блокуючий HTTP-запит у Telegram винесено у фоновий потік (`run_blocking`,
        DK-41), щоб не заморожувати event loop для інших користувачів на час
        надсилання. Помилку доставки показуємо тостом — успіх не мовчазний."""
        text = self.feedback_text.strip()
        if not text:
            yield rx.toast.warning("Введіть текст повідомлення.")
            return
        if self.worker is None:
            return

        pib = self.worker.pib
        login = self.worker.login

        self.feedback_sending = True
        yield
        try:
            await run_blocking(FeedbackService.dispatch, text, pib, login)
            self.feedback_text = ""
            self.feedback_open = False
            yield rx.toast.success("Повідомлення надіслано. Дякуємо за зворотний зв'язок!")
        except Exception as e:
            print(f"[FeedbackState][on_submit][ERROR] {e}")
            yield rx.toast.error("Під час надсилання сталася помилка. Спробуйте пізніше.")
        finally:
            self.feedback_sending = False
