from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.body_service import BodyService
from backend.app.schemas.body import CelestialBodyResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/bodies", tags=["Celestial Bodies"])

@router.get("", response_model=PaginatedResponse[CelestialBodyResponse])
@router.get("/", response_model=PaginatedResponse[CelestialBodyResponse], include_in_schema=False)
def list_bodies(
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    service = BodyService(db)
    return service.list_bodies(limit=limit, offset=offset)

@router.get("/{body_id}", response_model=CelestialBodyResponse)
def get_body(
    body_id: str,
    db: Session = Depends(get_db)
):
    service = BodyService(db)
    body = service.get_body(body_id)
    if not body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Celestial body '{body_id}' not found"
        )
    return body
