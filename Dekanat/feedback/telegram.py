import os

import httpx

from Dekanat.feedback.base import FeedbackChannel, FeedbackMessage


class TelegramFeedbackChannel(FeedbackChannel):
    """Доставка фідбека в Telegram-чат через Bot API (DK-32). Конфігурація —
    змінні оточення `FEEDBACK_TELEGRAM_BOT_TOKEN`/`FEEDBACK_TELEGRAM_CHAT_ID`
    (як `DB_URL`/`API_URL` у `rxconfig.py`) — секрет не потрапляє в БД/UI."""

    name = "telegram"

    def is_configured(self) -> bool:
        return bool(os.environ.get("FEEDBACK_TELEGRAM_BOT_TOKEN")) and bool(
            os.environ.get("FEEDBACK_TELEGRAM_CHAT_ID")
        )

    def send(self, message: FeedbackMessage) -> None:
        token = os.environ["FEEDBACK_TELEGRAM_BOT_TOKEN"]
        chat_id = os.environ["FEEDBACK_TELEGRAM_CHAT_ID"]
        # Без parse_mode — plain text, щоб не вимагати HTML/MarkdownV2-екранування
        # довільного введеного користувачем тексту.
        response = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": self._format(message)},
            timeout=10,
        )
        response.raise_for_status()
