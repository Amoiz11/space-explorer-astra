from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class LayerMetadataResponse(BaseModel):
    id: str
    name: str
    type: str  # "point", "linestring", "vector", "raster"
    description: str
    geojson_url: Optional[str] = None
    url: Optional[str] = None
    label: str  # "Estimated", "Verified", "Unknown", "Derived", "Modelled"
    source: str
    source_product_id: Optional[str] = None
    is_placeholder: bool
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)
