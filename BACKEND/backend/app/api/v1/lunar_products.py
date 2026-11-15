from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.models import TerrainProduct, DataProduct, DataSource
from backend.app.schemas.lunar_product import TerrainProductResponse

router = APIRouter(prefix="/lunar/products", tags=["Lunar Terrain Products"])

DISCLAIMER_TEXT = (
    "DEM resolution cannot detect small rocks, boulders, or micro-hazards. "
    "This product is for regional planning support and does not certify landing safety."
)


@router.get("/{id}", response_model=TerrainProductResponse)
def get_lunar_product(
    id: str,
    db: Session = Depends(get_db)
):
    product = db.query(TerrainProduct).filter(TerrainProduct.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lunar terrain product '{id}' not found"
        )

    # Fetch provenance through DataProduct and DataSource
    data_prod = db.query(DataProduct).filter(DataProduct.id == product.source_product_id).first()
    source_name = None
    source_url = None
    checksum = None
    retrieved_at = None
    label = "Verified"
    is_placeholder = False

    if data_prod:
        checksum = data_prod.checksum
        retrieved_at = data_prod.retrieved_at
        label = data_prod.label
        is_placeholder = data_prod.is_placeholder
        if data_prod.source:
            source_name = data_prod.source.name
            source_url = data_prod.source.source_url

    return TerrainProductResponse(
        id=product.id,
        source_product_id=product.source_product_id,
        resolution=product.resolution,
        vertical_reference=product.vertical_reference,
        coverage=product.coverage,
        version=product.version,
        no_data_value=product.no_data_value,
        coordinate_reference_note=product.coordinate_reference_note,
        created_at=product.created_at,
        source_name=source_name,
        source_url=source_url,
        checksum=checksum,
        retrieved_at=retrieved_at,
        label=label,
        is_placeholder=is_placeholder,
        disclaimer=DISCLAIMER_TEXT,
    )
