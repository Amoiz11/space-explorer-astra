from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.explorer_service import ExplorerService
from backend.app.schemas.explorer import ExplorerResponse, ExplorerDetailResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/rovers", tags=["Rovers / Explorers"])

@router.get("", response_model=PaginatedResponse[ExplorerResponse])
@router.get("/", response_model=PaginatedResponse[ExplorerResponse], include_in_schema=False)
def list_rovers(
    mission_id: Optional[str] = Query(None, description="Filter by mission ID"),
    explorer_type: Optional[str] = Query(None, description="Filter by explorer type: rover, lander, orbiter, probe"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by explorer status"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = ExplorerService(db)
    return service.list_explorers(
        mission_id=mission_id,
        explorer_type=explorer_type,
        status=status_filter,
        limit=limit,
        offset=offset
    )

@router.get("/{rover_id}", response_model=ExplorerDetailResponse)
def get_rover(
    rover_id: str,
    db: Session = Depends(get_db)
):
    service = ExplorerService(db)
    rover = service.get_explorer(rover_id)
    if not rover:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rover / Explorer '{rover_id}' not found"
        )
    return rover
