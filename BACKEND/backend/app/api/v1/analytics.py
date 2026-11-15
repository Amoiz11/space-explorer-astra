from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.subresource_service import SubresourceService
from backend.app.schemas.subresources import (
    MissionAnalyticsResponse,
    MissionTimelineResponse,
)

router = APIRouter(prefix="/rovers", tags=["Analytics & Timeline"])

@router.get("/{rover_id}/analytics", response_model=MissionAnalyticsResponse)
def get_rover_analytics(
    rover_id: str,
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    return service.get_analytics(explorer_id=rover_id)

@router.get("/{rover_id}/timeline", response_model=MissionTimelineResponse)
def get_rover_timeline(
    rover_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    limit: int = Query(100, ge=1, le=500, description="Max timeline entries"),
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    return service.get_timeline(
        explorer_id=rover_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
