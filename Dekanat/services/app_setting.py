import reflex as rx

from typing import Optional, List, Sequence, Dict

from Dekanat.dao.app_setting import AppSettingDao
from Dekanat.models import AppSettingModel


# Категории и ключи настроек
CATEGORY_AUTH = "auth"
CATEGORY_RATING = "rating"

KEY_SESSION_TIMEOUT_MINUTES = "session_timeout_minutes"
KEY_MAX_TOTAL_POINTS = "max_total_points"

# Дефолтні значення (використовуються, якщо запис у БД відсутній)
DEFAULTS: Dict[str, Dict[str, str]] = {
    KEY_SESSION_TIMEOUT_MINUTES: {
        "category": CATEGORY_AUTH,
        "title": "Час сесії, хв",
        "description": "Час бездіяльності користувача, після якого сесія завершується. Ковзне вікно: продовжується при кожній активній дії.",
        "value": "60",
        "value_type": "int",
    },
    KEY_MAX_TOTAL_POINTS: {
        "category": CATEGORY_RATING,
        "title": "Максимальна сума балів",
        "description": "Верхня межа суми балів абітурієнта при формуванні рейтингу. Якщо сума перевищує це значення — вона обрізається до нього. Квоти від спеціальних умов не змінюються.",
        "value": "200",
        "value_type": "int",
    },
}


class AppSettingService:
    def get_list_items(self) -> Sequence[AppSettingModel]:
        try:
            with rx.session() as session:
                return list(AppSettingDao.get_all(session))
        except Exception as e:
            print(f"[AppSettingService][get_list_items][ERROR] {e}")
            raise

    def get_by_key(self, key: str) -> Optional[AppSettingModel]:
        """Read-only. Дефолти створюються окремо через ensure_defaults()/deploy.py —
        тут жодних INSERT'ів, бо метод викликається на hot path require_auth і блокування
        SQLite із паралельними сесіями (AuthService) неприпустиме."""
        try:
            with rx.session() as session:
                return AppSettingDao.get_by_key(key, session)
        except Exception as e:
            print(f"[AppSettingService][get_by_key][ERROR] {e}")
            return None

    def get_int(self, key: str, fallback: int) -> int:
        item = self.get_by_key(key)
        if item is None:
            return fallback
        try:
            return int(item.value)
        except (ValueError, TypeError):
            return fallback

    def save_all(self, items: List[AppSettingModel]) -> None:
        try:
            with rx.session() as session:
                for it in items:
                    AppSettingDao.upsert(it, session)
                session.commit()
        except Exception as e:
            print(f"[AppSettingService][save_all][ERROR] {e}")
            raise

    def ensure_defaults(self) -> None:
        """Створює відсутні записи на основі DEFAULTS. Викликається явно — з deploy.py
        або з on_load сторінки настройок, але НЕ з hot path авторизації."""
        try:
            with rx.session() as session:
                changed = False
                for key, spec in DEFAULTS.items():
                    existing = AppSettingDao.get_by_key(key, session)
                    if existing is not None:
                        continue
                    session.add(AppSettingModel(
                        key=key,
                        category=spec["category"],
                        title=spec["title"],
                        description=spec["description"],
                        value=spec["value"],
                        value_type=spec["value_type"],
                    ))
                    changed = True
                if changed:
                    session.commit()
        except Exception as e:
            print(f"[AppSettingService][ensure_defaults][ERROR] {e}")

    # ---- Зручні getter'и під типовані налаштування ----

    def get_session_timeout_minutes(self) -> int:
        return self.get_int(KEY_SESSION_TIMEOUT_MINUTES, fallback=60)

    def get_max_total_points(self) -> int:
        return self.get_int(KEY_MAX_TOTAL_POINTS, fallback=200)
