"""Зворотний зв'язок користувач → розробник (DK-32).

Доставка розв'язана через `FeedbackChannel` (Strategy): сервіс `FeedbackService`
знає лише про абстракцію каналу, а деталі конкретного способу доставки (Telegram,
у майбутньому — пошта тощо) живуть у своєму модулі-нащадку. Додати новий канал —
дописати клас-нащадок `FeedbackChannel` і додати його екземпляр у реєстр
`FeedbackService._CHANNELS`.
"""

from Dekanat.feedback.base import FeedbackMessage, FeedbackChannel
from Dekanat.feedback.service import FeedbackService

__all__ = ["FeedbackMessage", "FeedbackChannel", "FeedbackService"]
