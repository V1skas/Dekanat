from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, delete

from Dekanat.models import AuthTokenModel
from Dekanat.utils.clock import now_local


class AuthTokenDao:
    @staticmethod
    def get_by_token(token: str, session: Session) -> Optional[AuthTokenModel]:
        try:
            statement = select(AuthTokenModel).where(AuthTokenModel.token == token)
            return session.exec(statement).one_or_none()
        except Exception as e:
            print(f"[AuthTokenDao][get_by_token][ERROR] {e}")
            return None

    @staticmethod
    def add_one(token: AuthTokenModel, session: Session):
        try:
            session.add(token)
        except Exception as e:
            print(f"[AuthTokenDao][add_one][ERROR] {e}")

    @staticmethod
    def delete(token: AuthTokenModel, session: Session):
        session.delete(token)

    @staticmethod
    def delete_expired(session: Session, now: Optional[datetime] = None) -> int:
        """Видаляє всі токени, у яких expires_at <= now. Повертає к-сть видалених."""
        try:
            current = now or now_local()
            result = session.exec(
                delete(AuthTokenModel).where(AuthTokenModel.expires_at <= current)
            )
            return getattr(result, "rowcount", 0) or 0
        except Exception as e:
            print(f"[AuthTokenDao][delete_expired][ERROR] {e}")
            return 0

    @staticmethod
    def touch(token: AuthTokenModel, new_expires_at: datetime, session: Session) -> AuthTokenModel:
        """Продовжує термін дії токена (ковзне вікно)."""
        token.last_activity_at = now_local()
        token.expires_at = new_expires_at
        session.add(token)
        return token
