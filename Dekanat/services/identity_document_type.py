import reflex as rx

from typing import Optional, List, Sequence

from Dekanat.dao.identity_document_type import IdentityDocumentTypeDao
from Dekanat.models import IdentityDocumentTypeModel

class IdentityDocumentTypeService:
    def get_list_items(self) -> Optional[Sequence[IdentityDocumentTypeModel]]:
        try:
            with rx.session() as session:
                items: Sequence[IdentityDocumentTypeModel] = IdentityDocumentTypeDao.get_all(session)
                return items if len(items) > 0 else None
        except Exception as e:
            print(f"[IdentityDocumentTypeService][get_list_items][ERROR] {e}")
            raise

    def get_by_id(self, id: int) -> Optional[IdentityDocumentTypeModel]:
        try:
            with rx.session() as session:
                return IdentityDocumentTypeDao.get_by_id(id, session)
        except Exception as e:
            print(f"[IdentityDocumentTypeService][get_by_id][ERROR] {e}")
            raise

    def add_one(self, item: IdentityDocumentTypeModel) -> IdentityDocumentTypeModel:
        try:
            with rx.session() as session:
                IdentityDocumentTypeDao.add_one(item, session)
                session.commit()
                session.refresh(item)
            return item

        except Exception as e:
            print(f"[IdentityDocumentTypeService][add_one][ERROR] {e}")
            raise

    def edit_one(self, item: IdentityDocumentTypeModel) -> IdentityDocumentTypeModel:
        try:
            with rx.session() as session:
                IdentityDocumentTypeDao.edit_one(item, session)
                session.commit()
                session.refresh(item)
            return item

        except Exception as e:
            print(f"[IdentityDocumentTypeService][edit_one][ERROR] {e}")
            raise

    def delete_one(self, item: IdentityDocumentTypeModel) -> bool:
        try:
            with rx.session() as session:
                item.is_deleted = True
                IdentityDocumentTypeDao.edit_one(item, session)
                session.commit()
            return True
        except Exception as e:
            print(f"[IdentityDocumentTypeService][delete_one][ERROR] {e}")
            return False

