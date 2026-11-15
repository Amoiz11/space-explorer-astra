from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.subresource_service import SubresourceService
from backend.app.schemas.subresources import ImageResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/rovers", tags=["Images"])

@router.get("/{rover_id}/images", response_model=PaginatedResponse[ImageResponse])
def get_rover_images(
    rover_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    camera: Optional[str] = Query(None, description="Camera filter (e.g. NAVCAM, MASTCAM)"),
    sol: Optional[int] = Query(None, ge=0, description="Sol filter (Mars solar day)"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = SubresourceService(db)
    return service.list_images(
        explorer_id=rover_id,
        start_date=start_date,
        end_date=end_date,
        camera=camera,
        sol=sol,
        limit=limit,
        offset=offset
    )
