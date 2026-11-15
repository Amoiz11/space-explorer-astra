from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.location_service import LocationService
from backend.app.schemas.location import LocationResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/rovers", tags=["Locations"])

@router.get("/{rover_id}/locations", response_model=PaginatedResponse[LocationResponse])
def get_rover_locations(
    rover_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = LocationService(db)
    return service.list_locations(
        explorer_id=rover_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

@router.get("/{rover_id}/latest-location", response_model=LocationResponse)
def get_rover_latest_location(
    rover_id: str,
    db: Session = Depends(get_db)
):
    service = LocationService(db)
    return service.get_latest_location(explorer_id=rover_id)
