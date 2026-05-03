import reflex as rx

from typing import Optional
from sqlmodel import Session, select

from Dekanat.models import AuthTokenModel

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
            return
        except Exception as e:
            print(f"[AuthTokenDao][add_one][ERROR] {e}")
            return None
        
    @staticmethod
    def delete(token: AuthTokenModel, session: Session):
        session.delete(token)
