from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import CelestialBody

class BodyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, limit: int = 50, offset: int = 0) -> List[CelestialBody]:
        return self.db.query(CelestialBody).offset(offset).limit(limit).all()

    def count(self) -> int:
        return self.db.query(CelestialBody).count()

    def get_by_id(self, body_id: str) -> Optional[CelestialBody]:
        return self.db.query(CelestialBody).filter(CelestialBody.id == body_id).first()
