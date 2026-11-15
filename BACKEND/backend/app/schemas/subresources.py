from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel

class TrajectoryResponse(BaseModel):
    id: int
    explorer_id: str
    path_coordinates: Optional[List[Any]] = None
    method: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    product_id: Optional[str] = None
    label: str = "Verified"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA PDS Trajectory Archive"
    is_placeholder: bool = True

    class Config:
        from_attributes = True

class ImageResponse(BaseModel):
    id: str
    explorer_id: str
    captured_at: datetime
    sol: Optional[int] = None
    image_url: str
    camera: Optional[str] = None
    product_id: Optional[str] = None
    label: str = "Historical"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA Planetary Data System Image Archive"
    is_placeholder: bool = True

    class Config:
        from_attributes = True

class MissionEventResponse(BaseModel):
    id: int
    explorer_id: str
    event_date: datetime
    event_type: str
    description: str
    source_id: Optional[str] = None
    label: str = "Verified"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA Mission Operations Log"
    is_placeholder: bool = True

    class Config:
        from_attributes = True

class HealthReportResponse(BaseModel):
    explorer_id: str
    condition: str
    evidence: str
    reported_at: Optional[datetime] = None
    source_id: Optional[str] = None
    label: str = "Historical"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA Mission Technical Reports"
    is_placeholder: bool = True

    class Config:
        from_attributes = True

class MissionAnalyticsResponse(BaseModel):
    explorer_id: str
    duration_days: Optional[float] = None
    distance_km: Optional[float] = None
    calculation_method: str = "Documented start/end dates and validated waypoints"
    label: str = "Estimated"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA Mission Analysis Archive"
    is_placeholder: bool = True

class TimelineItem(BaseModel):
    item_type: str  # event, location, image
    timestamp: datetime
    title: str
    details: Optional[dict] = None
    label: str = "Historical"  # Verified, Historical, Estimated, Unknown
    source_label: str
    is_placeholder: bool = True

class MissionTimelineResponse(BaseModel):
    explorer_id: str
    total_items: int
    timeline: List[TimelineItem]
    label: str = "Historical"  # Verified, Historical, Estimated, Unknown
    source_label: str = "Space Explorer Correlated Timeline Engine"
    is_placeholder: bool = True
