from typing import List

from Dekanat.feedback.base import FeedbackChannel, FeedbackMessage
from Dekanat.feedback.telegram import TelegramFeedbackChannel
from Dekanat.utils.clock import now_local


class FeedbackService:
    """Розсилає повідомлення по всіх налаштованих каналах (DK-32). Додати новий
    спосіб доставки (пошта тощо) — дописати клас-нащадок `FeedbackChannel` і
    додати його екземпляр сюди, у `_CHANNELS`."""

    _CHANNELS: List[FeedbackChannel] = [TelegramFeedbackChannel()]

    @staticmethod
    def dispatch(text: str, sender_pib: str, sender_login: str) -> None:
        """Чиста функція (лише примітиви на вході) — придатна для offload'у у
        фоновий потік через `run_blocking` (DK-41), бо не мутує стан Reflex.

        Кидає виняток, якщо жоден налаштований канал не доставив повідомлення —
        виклик (state) вирішує, що показати користувачу."""
        message = FeedbackMessage(
            text=text,
            sender_pib=sender_pib,
            sender_login=sender_login,
            created_at=now_local(),
        )

        configured = [c for c in FeedbackService._CHANNELS if c.is_configured()]
        if not configured:
            raise RuntimeError("Жоден канал доставки фідбека не налаштований.")

        delivered = False
        for channel in configured:
            try:
                channel.send(message)
                delivered = True
            except Exception as e:
                print(f"[FeedbackService][dispatch][{channel.name}][ERROR] {e}")

        if not delivered:
            raise RuntimeError("Не вдалося доставити фідбек жодним із каналів.")
