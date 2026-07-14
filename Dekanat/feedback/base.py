"""Базові класи каналів доставки фідбека (DK-32).

`FeedbackChannel` — абстракція каналу доставки (Strategy): `FeedbackService` знає
лише про цей інтерфейс і не знає, як саме повідомлення потрапляє до отримувача.
`send` кидає виняток при невдачі — сервіс сам вирішує, як на це реагувати."""

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class FeedbackMessage(BaseModel):
    text: str
    sender_pib: str
    sender_login: str
    created_at: datetime


class FeedbackChannel(ABC):
    name: str = ""

    def is_configured(self) -> bool:
        """За замовчуванням канал завжди готовий; канали із зовнішньою конфігурацією
        (токени, адреси) перевизначають це, щоб деградувати м'яко без падіння."""
        return True

    @abstractmethod
    def send(self, message: FeedbackMessage) -> None:
        """Надіслати повідомлення. При невдачі — кинути виняток."""
        raise NotImplementedError

    def _format(self, message: FeedbackMessage) -> str:
        return (
            f"Логін: {message.sender_login}\n"
            f"ПІБ: {message.sender_pib}\n\n"
            f"{message.text}"
        )
