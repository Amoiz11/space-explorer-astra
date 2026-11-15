from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import Explorer

class ExplorerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        mission_id: Optional[str] = None,
        explorer_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Explorer]:
        query = self.db.query(Explorer)
        if mission_id:
            query = query.filter(Explorer.mission_id == mission_id)
        if explorer_type:
            query = query.filter(Explorer.explorer_type == explorer_type)
        if status:
            query = query.filter(Explorer.current_status == status)
        return query.offset(offset).limit(limit).all()

    def count(
        self,
        mission_id: Optional[str] = None,
        explorer_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        query = self.db.query(Explorer)
        if mission_id:
            query = query.filter(Explorer.mission_id == mission_id)
        if explorer_type:
            query = query.filter(Explorer.explorer_type == explorer_type)
        if status:
            query = query.filter(Explorer.current_status == status)
        return query.count()

    def get_by_id(self, explorer_id: str) -> Optional[Explorer]:
        return self.db.query(Explorer).filter(Explorer.id == explorer_id).first()
