from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.source_service import SourceService
from backend.app.schemas.source import SourceProvenanceResponse

router = APIRouter(prefix="/sources", tags=["Data Sources & Provenance"])

@router.get("/{product_id:path}", response_model=SourceProvenanceResponse)
def get_source_product_provenance(
    product_id: str,
    db: Session = Depends(get_db)
):
    service = SourceService(db)
    provenance = service.get_provenance(product_id)
    if not provenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source data product '{product_id}' not found"
        )
    return provenance
