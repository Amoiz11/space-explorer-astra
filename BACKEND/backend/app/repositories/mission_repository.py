from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import Mission

class MissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        body_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Mission]:
        query = self.db.query(Mission)
        if body_id:
            query = query.filter(Mission.body_id == body_id)
        if status:
            query = query.filter(Mission.status == status)
        return query.offset(offset).limit(limit).all()

    def count(self, body_id: Optional[str] = None, status: Optional[str] = None) -> int:
        query = self.db.query(Mission)
        if body_id:
            query = query.filter(Mission.body_id == body_id)
        if status:
            query = query.filter(Mission.status == status)
        return query.count()

    def get_by_id(self, mission_id: str) -> Optional[Mission]:
        return self.db.query(Mission).filter(Mission.id == mission_id).first()
