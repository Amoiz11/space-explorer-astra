from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class TerrainProductResponse(BaseModel):
    id: str
    source_product_id: str
    resolution: str
    vertical_reference: Optional[str] = None
    coverage: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    no_data_value: Optional[str] = None
    coordinate_reference_note: Optional[str] = None
    created_at: Optional[datetime] = None

    # Provenance fields
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    checksum: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    label: str = "Verified"
    is_placeholder: bool = False
    disclaimer: str = (
        "DEM resolution cannot detect small rocks, boulders, or micro-hazards. "
        "This product is for regional planning support and does not certify landing safety."
    )

    model_config = ConfigDict(from_attributes=True)
