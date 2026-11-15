import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.map_service import MapService
from backend.app.schemas.map_layer import LayerMetadataResponse

router = APIRouter(prefix="/map", tags=["Map Layers & MMGIS"])


@router.get(
    "/layers/{mission_id}",
    response_model=List[LayerMetadataResponse],
    summary="Get mission map layer metadata",
    description="Returns available geospatial layers for the given planetary mission (MMGIS integration).",
)
def get_mission_layers(
    mission_id: str,
    db: Session = Depends(get_db),
):
    service = MapService(db)
    layers = service.get_layers_for_mission(mission_id)
    if layers is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found.",
        )
    return layers


@router.get(
    "/layers/{mission_id}/{layer_id}.png",
    summary="Get lunar raster layer preview PNG",
    description="Returns downsampled preview PNG for lunar raster layers (DEM, Slope).",
)
def get_layer_png(
    mission_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
):
    service = MapService(db)
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found.",
        )
    png_path = service.get_raster_png(mission_id, layer_id)
    if not png_path or not os.path.exists(png_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raster layer '{layer_id}' not found for mission '{mission_id}'.",
        )
    return FileResponse(png_path, media_type="image/png")


@router.get(
    "/layers/{mission_id}/{layer_id}.json",
    summary="Get lunar raster layer sidecar JSON",
    description="Returns JSON sidecar giving projection, bounds, pixel size, colour scale, and units.",
)
def get_layer_json(
    mission_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
):
    service = MapService(db)
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found.",
        )
    sidecar = service.get_raster_sidecar(mission_id, layer_id)
    if not sidecar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer sidecar '{layer_id}' not found for mission '{mission_id}'.",
        )
    return JSONResponse(
        content=sidecar,
        media_type="application/json",
    )


@router.get(
    "/layers/{mission_id}/{layer_id}.geojson",
    summary="Get layer as GeoJSON FeatureCollection",
    description="Returns RFC 7946 GeoJSON FeatureCollection in planetary coordinates (never EPSG:4326).",
)
def get_layer_geojson(
    mission_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
):
    service = MapService(db)
    geojson_data = service.get_geojson_layer(mission_id, layer_id)
    if geojson_data is None:
        # Check if mission was missing vs layer missing
        mission = service.get_mission(mission_id)
        if not mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission '{mission_id}' not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer '{layer_id}' not found for mission '{mission_id}'.",
        )

    return JSONResponse(
        content=geojson_data,
        media_type="application/geo+json",
    )


@router.get(
    "/layers/{mission_id}/{layer_id}",
    include_in_schema=False,
)
def get_layer_geojson_fallback(
    mission_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
):
    if layer_id.lower().endswith(".png"):
        clean_id = layer_id[:-4]
        return get_layer_png(mission_id=mission_id, layer_id=clean_id, db=db)
    if layer_id.lower().endswith(".json"):
        clean_id = layer_id[:-5]
        return get_layer_json(mission_id=mission_id, layer_id=clean_id, db=db)
    return get_layer_geojson(mission_id=mission_id, layer_id=layer_id, db=db)
