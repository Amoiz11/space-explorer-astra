from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.repositories.subresource_repository import SubresourceRepository
from backend.app.repositories.location_repository import LocationRepository
from backend.app.repositories.explorer_repository import ExplorerRepository
from backend.app.schemas.subresources import (
    TrajectoryResponse,
    ImageResponse,
    MissionEventResponse,
    HealthReportResponse,
    MissionAnalyticsResponse,
    MissionTimelineResponse,
    TimelineItem,
)
from backend.app.schemas.common import PaginatedResponse

class SubresourceService:
    def __init__(self, db: Session):
        self.repository = SubresourceRepository(db)
        self.location_repo = LocationRepository(db)
        self.explorer_repo = ExplorerRepository(db)

    def get_trajectory(self, explorer_id: str) -> Optional[TrajectoryResponse]:
        traj = self.repository.get_trajectory(explorer_id)
        if not traj:
            return None
        res = TrajectoryResponse.model_validate(traj)
        # Rule: a placeholder can never return a label other than "Unknown"
        if res.is_placeholder:
            res.label = "Unknown"
        return res

    def list_images(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        camera: Optional[str] = None,
        sol: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[ImageResponse]:
        total = self.repository.count_images(
            explorer_id, start_date=start_date, end_date=end_date, camera=camera, sol=sol
        )
        images = self.repository.get_images(
            explorer_id,
            start_date=start_date,
            end_date=end_date,
            camera=camera,
            sol=sol,
            limit=limit,
            offset=offset,
        )
        items = [ImageResponse.model_validate(img) for img in images]
        # Rule: a placeholder can never return a label other than "Unknown"
        for item in items:
            if item.is_placeholder:
                item.label = "Unknown"
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def list_events(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[MissionEventResponse]:
        total = self.repository.count_events(
            explorer_id, start_date=start_date, end_date=end_date
        )
        events = self.repository.get_events(
            explorer_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        items = [MissionEventResponse.model_validate(ev) for ev in events]
        # Rule: a placeholder can never return a label other than "Unknown"
        for item in items:
            if item.is_placeholder:
                item.label = "Unknown"
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def get_health(self, explorer_id: str) -> HealthReportResponse:
        report = self.repository.get_latest_health_report(explorer_id)
        if not report:
            explorer = self.explorer_repo.get_by_id(explorer_id)
            current_status = explorer.current_status if explorer else "unknown"
            return HealthReportResponse(
                explorer_id=explorer_id,
                condition=current_status,
                evidence="No direct telemetry-based health assessment available in current catalog.",
                reported_at=None,
                source_id=None,
                label="Unknown",
                source_label="NASA Mission Documentation",
                is_placeholder=True,
            )
        res = HealthReportResponse.model_validate(report)
        # Rule: a placeholder can never return a label other than "Unknown"
        if res.is_placeholder:
            res.label = "Unknown"
        return res

    def get_analytics(self, explorer_id: str) -> MissionAnalyticsResponse:
        explorer = self.explorer_repo.get_by_id(explorer_id)
        duration_days = None
        if explorer and explorer.mission:
            mission = explorer.mission
            start = mission.landing_date or mission.launch_date
            end = mission.end_date or datetime.utcnow()
            if start and end:
                duration_days = round((end - start).total_seconds() / 86400.0, 1)

        traj = self.repository.get_trajectory(explorer_id)
        distance_km = None
        if traj and traj.path_coordinates:
            distance_km = round(len(traj.path_coordinates) * 0.05, 2)

        is_placeholder = True
        return MissionAnalyticsResponse(
            explorer_id=explorer_id,
            duration_days=duration_days,
            distance_km=distance_km,
            calculation_method="Calculated from documented mission start/landing dates and verified traversed waypoints",
            label="Unknown" if is_placeholder else "Estimated",
            source_label="NASA Mission Analysis Archive",
            is_placeholder=is_placeholder,
        )

    def get_timeline(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> MissionTimelineResponse:
        events = self.repository.get_events(
            explorer_id, start_date=start_date, end_date=end_date, limit=limit
        )
        images = self.repository.get_images(
            explorer_id, start_date=start_date, end_date=end_date, limit=limit
        )

        timeline_items: List[TimelineItem] = []
        for ev in events:
            is_ph = bool(ev.is_placeholder)
            timeline_items.append(
                TimelineItem(
                    item_type="event",
                    timestamp=ev.event_date,
                    title=f"Event: {ev.event_type}",
                    details={"description": ev.description},
                    label="Unknown" if is_ph else (getattr(ev, "label", "Verified") or "Verified"),
                    source_label="NASA Operations Log",
                    is_placeholder=is_ph,
                )
            )
        for img in images:
            is_ph = bool(img.is_placeholder)
            timeline_items.append(
                TimelineItem(
                    item_type="image",
                    timestamp=img.captured_at,
                    title=f"Image Capture ({img.camera or 'Camera'})",
                    details={"url": img.image_url},
                    label="Unknown" if is_ph else (getattr(img, "label", "Historical") or "Historical"),
                    source_label="NASA Image Archive",
                    is_placeholder=is_ph,
                )
            )

        timeline_items.sort(key=lambda x: x.timestamp)

        is_ph = True
        return MissionTimelineResponse(
            explorer_id=explorer_id,
            total_items=len(timeline_items),
            timeline=timeline_items[:limit],
            label="Unknown" if is_ph else "Historical",
            source_label="Space Explorer Correlated Timeline Engine",
            is_placeholder=is_ph,
        )
