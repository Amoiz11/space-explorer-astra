from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.models import Location

class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_locations(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Location]:
        query = self.db.query(Location).filter(Location.explorer_id == explorer_id)
        if start_date:
            query = query.filter(Location.observed_at >= start_date)
        if end_date:
            query = query.filter(Location.observed_at <= end_date)
        return query.order_by(Location.observed_at.asc()).offset(offset).limit(limit).all()

    def count_locations(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        query = self.db.query(Location).filter(Location.explorer_id == explorer_id)
        if start_date:
            query = query.filter(Location.observed_at >= start_date)
        if end_date:
            query = query.filter(Location.observed_at <= end_date)
        return query.count()

    def get_latest_location(self, explorer_id: str) -> Optional[Location]:
        return (
            self.db.query(Location)
            .filter(Location.explorer_id == explorer_id)
            .order_by(Location.observed_at.desc())
            .first()
        )
