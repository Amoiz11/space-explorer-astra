from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.models import (
    Trajectory,
    Image,
    MissionEvent,
    HealthReport,
    Telemetry,
)

class SubresourceRepository:
    def __init__(self, db: Session):
        self.db = db

    # Trajectory
    def get_trajectory(self, explorer_id: str) -> Optional[Trajectory]:
        return (
            self.db.query(Trajectory)
            .filter(Trajectory.explorer_id == explorer_id)
            .order_by(Trajectory.id.desc())
            .first()
        )

    # Images
    def get_images(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        camera: Optional[str] = None,
        sol: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Image]:
        query = self.db.query(Image).filter(Image.explorer_id == explorer_id)
        if start_date:
            query = query.filter(Image.captured_at >= start_date)
        if end_date:
            query = query.filter(Image.captured_at <= end_date)
        if camera:
            query = query.filter(Image.camera == camera)
        if sol is not None:
            query = query.filter(Image.sol == sol)
        return query.order_by(Image.captured_at.desc()).offset(offset).limit(limit).all()

    def count_images(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        camera: Optional[str] = None,
        sol: Optional[int] = None,
    ) -> int:
        query = self.db.query(Image).filter(Image.explorer_id == explorer_id)
        if start_date:
            query = query.filter(Image.captured_at >= start_date)
        if end_date:
            query = query.filter(Image.captured_at <= end_date)
        if camera:
            query = query.filter(Image.camera == camera)
        if sol is not None:
            query = query.filter(Image.sol == sol)
        return query.count()

    # Events
    def get_events(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MissionEvent]:
        query = self.db.query(MissionEvent).filter(MissionEvent.explorer_id == explorer_id)
        if start_date:
            query = query.filter(MissionEvent.event_date >= start_date)
        if end_date:
            query = query.filter(MissionEvent.event_date <= end_date)
        return query.order_by(MissionEvent.event_date.asc()).offset(offset).limit(limit).all()

    def count_events(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        query = self.db.query(MissionEvent).filter(MissionEvent.explorer_id == explorer_id)
        if start_date:
            query = query.filter(MissionEvent.event_date >= start_date)
        if end_date:
            query = query.filter(MissionEvent.event_date <= end_date)
        return query.count()

    # Health Report
    def get_latest_health_report(self, explorer_id: str) -> Optional[HealthReport]:
        return (
            self.db.query(HealthReport)
            .filter(HealthReport.explorer_id == explorer_id)
            .order_by(HealthReport.reported_at.desc())
            .first()
        )
