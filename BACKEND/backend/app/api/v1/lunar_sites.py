import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.lunar_site import (
    CandidateLandingSiteCreate,
    CandidateLandingSiteUpdate,
    CandidateLandingSiteResponse,
)
from backend.app.schemas.terrain_analysis import (
    TerrainAnalysisResponse,
    SlopeAnalysisResponse,
)
from backend.app.schemas.lunar_geometry import SiteGeometryResponse
from backend.app.schemas.lunar_horizon import (
    HorizonProfileResponse,
    HorizonSummaryModel,
    HorizonPointModel,
)
from backend.app.schemas.lunar_illumination import SiteIlluminationResponse
from backend.app.schemas.lunar_earth_visibility import SiteEarthVisibilityResponse
from backend.app.schemas.lunar_solar_power import SolarEstimateRequest, SolarEstimateResponse
from backend.app.services.lunar_site_service import LunarSiteService
from backend.app.services.dem_service import SiteCoverageError, get_dem_service
from backend.app.services.lunar_geometry_service import (
    KernelManager,
    get_lunar_geometry_service,
    safe_str2et,
)
from backend.app.services.horizon_service import HorizonService, get_horizon_service
from backend.app.services.illumination_service import get_illumination_service
from backend.app.services.earth_visibility_service import get_earth_visibility_service
from backend.app.services.solar_power_service import get_solar_power_service
from backend.app.core import bootstrap_state

router = APIRouter(prefix="/lunar/sites", tags=["Candidate Landing Sites"])

def verify_bootstrap_ready():
    """While background bootstrap is running, data endpoints return 503 warming up."""
    if bootstrap_state.is_running():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is warming up: SPICE kernels and DEM data are initializing. Please retry in a few moments."
        )
    return True

def verify_admin_key(x_admin_key: Optional[str] = Header(None, alias="x-admin-key")):
    """Optional write protection: requires x-admin-key header matching ADMIN_KEY env var when configured."""
    admin_key = os.getenv("ADMIN_KEY", "").strip()
    if admin_key:
        if not x_admin_key or x_admin_key.strip() != admin_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: invalid or missing x-admin-key header"
            )
    return True

@router.get("", response_model=List[CandidateLandingSiteResponse])
@router.get("/", response_model=List[CandidateLandingSiteResponse], include_in_schema=False)
def get_candidate_sites(
    body_id: Optional[str] = "moon",
    db: Session = Depends(get_db)
):
    service = LunarSiteService(db)
    return service.list_sites(body_id=body_id)

@router.get("/{site_id}", response_model=CandidateLandingSiteResponse)
def get_candidate_site(
    site_id: str,
    db: Session = Depends(get_db)
):
    service = LunarSiteService(db)
    site = service.get_site(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )
    return site

@router.post("", response_model=CandidateLandingSiteResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CandidateLandingSiteResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_candidate_site(
    site_in: CandidateLandingSiteCreate,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_key),
):
    service = LunarSiteService(db)
    # Check if exists
    existing = service.get_site(site_in.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Candidate landing site '{site_in.id}' already exists"
        )
    return service.create_site(site_in)

@router.put("/{site_id}", response_model=CandidateLandingSiteResponse)
def update_candidate_site(
    site_id: str,
    site_in: CandidateLandingSiteUpdate,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_key),
):
    service = LunarSiteService(db)
    updated = service.update_site(site_id, site_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )
    return updated

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_site(
    site_id: str,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_admin_key),
):
    service = LunarSiteService(db)
    deleted = service.delete_site(site_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )
    return None

@router.get("/{site_id}/terrain", response_model=TerrainAnalysisResponse)
def get_site_terrain(
    site_id: str,
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    service = LunarSiteService(db)
    try:
        result = service.get_site_terrain(site_id)
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )
    return result


@router.get("/{site_id}/slope", response_model=SlopeAnalysisResponse)
def get_site_slope(
    site_id: str,
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    service = LunarSiteService(db)
    try:
        result = service.get_site_slope(site_id)
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )
    return result


@router.get("/{site_id}/geometry", response_model=SiteGeometryResponse)
def get_site_geometry(
    site_id: str,
    start: str = Query(..., description="UTC start date/time (e.g. YYYY-MM-DD or ISO 8601)"),
    days: int = Query(30, ge=1, le=60, description="Number of days to simulate (1 to 60)"),
    step_minutes: int = Query(30, ge=5, description="Time step in minutes (minimum 5)"),
    include_horizon: bool = Query(False, description="Whether to include local terrain horizon elevation at Sun and Earth azimuths per step"),
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    site_service = LunarSiteService(db)
    site = site_service.repository.get_by_id(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )

    # Check SPICE kernels
    if not KernelManager.are_kernels_available():
        missing = KernelManager.check_kernels()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SPICE kernels missing on server: {missing}. Run scripts/download_kernels.py."
        )

    KernelManager.load_kernels()

    # Parse and validate start date
    try:
        safe_str2et(start)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid start date '{start}': must be a valid UTC ISO 8601 date string (e.g. 2026-12-01)."
        )

    coords = site.coordinates or {}
    values = coords.get("values", [])
    if len(values) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' coordinates missing [latitude, longitude] values."
        )
    lat, lon = float(values[0]), float(values[1])

    dem_service = get_dem_service()
    elev_m = 0.0
    try:
        elev_m = dem_service.get_site_elevation(lat, lon)
    except SiteCoverageError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' is outside DEM coverage bounds (north of 75°S)."
        )
    except Exception:
        elev_m = 0.0

    geom_service = get_lunar_geometry_service()
    calc = geom_service.calculate_geometry(
        lat_deg=lat,
        lon_deg=lon,
        elevation_m=elev_m,
        start_utc=start,
        days=days,
        step_minutes=step_minutes,
    )

    if include_horizon:
        horizon_service = get_horizon_service()
        try:
            h_res = horizon_service.compute_site_horizon(
                site_lat=lat,
                site_lon=lon,
                azimuth_step_deg=1.0,
                max_distance_km=100.0,
                observer_height_m=0.0,
            )
            for pt in calc["series"]:
                pt["horizon_elevation_at_sun_azimuth"] = horizon_service.interpolate_horizon_elevation(
                    h_res["profile"], pt["sun_azimuth_deg"]
                )
                pt["horizon_elevation_at_earth_azimuth"] = horizon_service.interpolate_horizon_elevation(
                    h_res["profile"], pt["earth_azimuth_deg"]
                )
        except Exception:
            pass

    return SiteGeometryResponse(
        site_id=site.id,
        site_name=site.name,
        is_placeholder=site.is_placeholder,
        label="Modelled",
        frame=calc["frame"],
        method=calc["method"],
        observer_elevation_m=calc["observer_elevation_m"],
        reference_sphere_radius_km=calc["reference_sphere_radius_km"],
        kernels_used=calc["kernels_used"],
        series=calc["series"],
        windows=calc["windows"],
        totals=calc["totals"],
        disclaimers=calc["disclaimers"],
    )


@router.get("/{site_id}/horizon", response_model=HorizonProfileResponse)
def get_site_horizon(
    site_id: str,
    azimuth_step: float = Query(1.0, ge=0.01, le=45.0, description="Azimuth resolution in degrees"),
    max_distance_km: float = Query(100.0, ge=0.1, le=500.0, description="Maximum ray distance in km"),
    observer_height_m: float = Query(0.0, ge=0.0, description="Additional observer mast/instrument height in metres"),
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    site_service = LunarSiteService(db)
    site = site_service.repository.get_by_id(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )

    coords = site.coordinates or {}
    values = coords.get("values", [])
    if len(values) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' coordinates missing [latitude, longitude] values."
        )
    lat, lon = float(values[0]), float(values[1])

    horizon_service = get_horizon_service()
    try:
        result = horizon_service.compute_site_horizon(
            site_lat=lat,
            site_lon=lon,
            azimuth_step_deg=azimuth_step,
            max_distance_km=max_distance_km,
            observer_height_m=observer_height_m,
        )
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    summary_model = HorizonSummaryModel(**result["summary"])
    profile_models = [HorizonPointModel(**p) for p in result["profile"]]

    return HorizonProfileResponse(
        site_id=site.id,
        site_name=site.name,
        is_placeholder=site.is_placeholder,
        label="Derived",
        product_id=HorizonService.DEFAULT_PRODUCT_ID,
        resolution=HorizonService.DEFAULT_RESOLUTION,
        method=result["method"],
        observer_height_dem_m=result["observer_height_dem_m"],
        observer_height_m=result["observer_height_m"],
        total_observer_height_m=result["total_observer_height_m"],
        summary=summary_model,
        cut_azimuths=result["cut_azimuths"],
        profile=profile_models,
        disclaimers=result["disclaimers"],
    )


@router.get("/{site_id}/illumination", response_model=SiteIlluminationResponse)
def get_site_illumination(
    site_id: str,
    start: str = Query(..., description="UTC start date/time (e.g. YYYY-MM-DD or ISO 8601)"),
    days: int = Query(30, ge=1, le=60, description="Simulation duration in days (1 to 60)"),
    step_minutes: int = Query(30, ge=5, description="Time step in minutes (minimum 5)"),
    observer_height_m: float = Query(0.0, ge=0.0, description="Observer instrument height above DEM surface in metres"),
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    """
    Terrain-aware solar illumination timeline and visibility windows (LL-14 to LL-16).
    """
    if not KernelManager.are_kernels_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SPICE ephemeris kernels are not available. Please run download_kernels.py."
        )

    site_service = LunarSiteService(db)
    site = site_service.repository.get_by_id(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )

    coords = site.coordinates or {}
    values = coords.get("values", [])
    if len(values) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' coordinates missing [latitude, longitude] values."
        )

    KernelManager.load_kernels()

    # Validate start date parsing with SPICE
    try:
        safe_str2et(start)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid start date '{start}': must be a valid UTC ISO 8601 date string."
        )

    illum_service = get_illumination_service(db)
    try:
        result = illum_service.calculate_site_illumination(
            site=site,
            start_utc=start,
            days=days,
            step_minutes=step_minutes,
            observer_height_m=observer_height_m,
        )
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    return SiteIlluminationResponse(**result)


@router.get("/{site_id}/earth-visibility", response_model=SiteEarthVisibilityResponse)
def get_site_earth_visibility(
    site_id: str,
    start: str = Query(..., description="UTC start date/time (e.g. YYYY-MM-DD or ISO 8601)"),
    days: int = Query(30, ge=1, le=60, description="Simulation duration in days (1 to 60)"),
    step_minutes: int = Query(30, ge=5, description="Time step in minutes (minimum 5)"),
    observer_height_m: float = Query(0.0, ge=0.0, description="Observer instrument height above DEM surface in metres"),
    earth_disk: str = Query("center", description="Earth disk criterion: 'center' or 'upper_limb'"),
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    """
    Terrain-aware direct-to-Earth line-of-sight visibility timeline and windows (LL-19 to LL-22).
    """
    if earth_disk not in ("center", "upper_limb"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid earth_disk option: '{earth_disk}'. Must be 'center' or 'upper_limb'."
        )

    if not KernelManager.are_kernels_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SPICE ephemeris kernels are not available. Please run download_kernels.py."
        )

    site_service = LunarSiteService(db)
    site = site_service.repository.get_by_id(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )

    coords = site.coordinates or {}
    values = coords.get("values", [])
    if len(values) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' coordinates missing [latitude, longitude] values."
        )

    KernelManager.load_kernels()

    # Validate start date parsing with SPICE
    try:
        safe_str2et(start)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid start date '{start}': must be a valid UTC ISO 8601 date string."
        )

    vis_service = get_earth_visibility_service(db)
    try:
        result = vis_service.calculate_site_earth_visibility(
            site=site,
            start_utc=start,
            days=days,
            step_minutes=step_minutes,
            observer_height_m=observer_height_m,
            earth_disk=earth_disk,
        )
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    return SiteEarthVisibilityResponse(**result)


@router.post("/{site_id}/solar-estimate", response_model=SolarEstimateResponse)
def estimate_site_solar_power(
    site_id: str,
    payload: SolarEstimateRequest,
    db: Session = Depends(get_db),
    _ready: bool = Depends(verify_bootstrap_ready),
):
    """
    Solar power generation opportunity and energy estimate for candidate landing sites (LL-23 to LL-26).
    """
    if not KernelManager.are_kernels_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SPICE ephemeris kernels are not available. Please run download_kernels.py."
        )

    KernelManager.load_kernels()

    site_service = LunarSiteService(db)
    site = site_service.repository.get_by_id(site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate landing site '{site_id}' not found"
        )

    coords = site.coordinates or {}
    values = coords.get("values", [])
    if len(values) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Site '{site_id}' coordinates missing [latitude, longitude] values."
        )

    # Validate start date parsing with SPICE
    try:
        safe_str2et(payload.start)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid start date '{payload.start}': must be a valid UTC ISO 8601 date string."
        )

    power_service = get_solar_power_service(db)
    try:
        result = power_service.estimate_solar_power(
            site=site,
            start_utc=payload.start,
            days=payload.days,
            step_minutes=payload.step_minutes,
            observer_height_m=payload.observer_height_m,
            solar_constant_w_m2=payload.solar_constant_w_m2,
            panel=payload.panel,
        )
    except SiteCoverageError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    return SolarEstimateResponse(**result)







