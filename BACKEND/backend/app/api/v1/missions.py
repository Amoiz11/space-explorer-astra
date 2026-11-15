from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.mission_service import MissionService
from backend.app.schemas.mission import MissionResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/missions", tags=["Missions"])

@router.get("", response_model=PaginatedResponse[MissionResponse])
@router.get("/", response_model=PaginatedResponse[MissionResponse], include_in_schema=False)
def list_missions(
    body_id: Optional[str] = Query(None, description="Filter by celestial body ID (e.g. mars, moon)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by mission status"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = MissionService(db)
    return service.list_missions(body_id=body_id, status=status_filter, limit=limit, offset=offset)

@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    service = MissionService(db)
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found"
        )
    return mission
