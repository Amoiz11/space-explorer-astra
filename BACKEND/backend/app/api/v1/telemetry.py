from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.subresource_service import SubresourceService
from backend.app.schemas.subresources import (
    MissionEventResponse,
    HealthReportResponse,
)
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/rovers", tags=["Mission Events & Health"])

@router.get("/{rover_id}/events", response_model=PaginatedResponse[MissionEventResponse])
def get_rover_events(
    rover_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    return service.list_events(
        explorer_id=rover_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

@router.get("/{rover_id}/health", response_model=HealthReportResponse)
def get_rover_health(
    rover_id: str,
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    return service.get_health(explorer_id=rover_id)
