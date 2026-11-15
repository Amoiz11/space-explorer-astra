"""
Lunar landing site comparison endpoints (B3a LL-18, B5a LL-27 to LL-30).

GET  /api/v1/lunar/compare          — existing flat-horizon geometry comparison (B3a, unchanged)
POST /api/v1/lunar/compare          — multi-site, multi-window terrain-aware comparison (B5a)
GET  /api/v1/lunar/compare/{id}/export — export stored comparison as JSON or CSV
"""

import csv
import io
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.models import CandidateLandingSite, LandingSiteComparison
from backend.app.schemas.lunar_geometry import (
    SiteComparisonResponse,
    SiteComparisonItemModel,
    TotalsModel,
)
from backend.app.schemas.lunar_comparison import (
    CompareRequest,
    CompareResponse,
    BestBy,
)
from backend.app.services.lunar_site_service import LunarSiteService
from backend.app.services.lunar_geometry_service import (
    KernelManager,
    get_lunar_geometry_service,
    DISCLAIMERS,
    FRAME_NAME,
    REQUIRED_KERNELS,
    safe_str2et,
)
from backend.app.services.dem_service import get_dem_service, SiteCoverageError
from backend.app.services.landing_window_service import (
    LandingWindowService,
    DISCLAIMERS as CMP_DISCLAIMERS,
    METHOD_TEXT,
)

router = APIRouter(prefix="/lunar/compare", tags=["Lunar Site Comparison"])


# ---------------------------------------------------------------------------
# EXISTING endpoint — do not change behaviour or response shape
# ---------------------------------------------------------------------------

@router.get("", response_model=SiteComparisonResponse)
@router.get("/", response_model=SiteComparisonResponse, include_in_schema=False)
def compare_lunar_sites(
    site_ids: str = Query(..., description="Comma-separated site IDs (e.g. site-shackleton-01,site-connecting-ridge-02)"),
    start: str = Query(..., description="UTC start date/time (e.g. YYYY-MM-DD or ISO 8601)"),
    days: int = Query(30, ge=1, le=60, description="Simulation duration in days (1 to 60)"),
    step_minutes: int = Query(30, ge=5, description="Time step in minutes (minimum 5)"),
    db: Session = Depends(get_db),
):
    if not KernelManager.are_kernels_available():
        missing = KernelManager.check_kernels()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SPICE kernels missing on server: {missing}. Run scripts/download_kernels.py."
        )

    KernelManager.load_kernels()

    try:
        safe_str2et(start)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid start date '{start}': must be a valid UTC ISO 8601 date string."
        )

    ids = [sid.strip() for sid in site_ids.split(",") if sid.strip()]
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parameter 'site_ids' must contain at least one valid site identifier."
        )

    site_service = LunarSiteService(db)
    dem_service = get_dem_service()
    geom_service = get_lunar_geometry_service()

    comparison_items = []
    for sid in ids:
        site = site_service.repository.get_by_id(sid)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate landing site '{sid}' not found"
            )

        coords = site.coordinates or {}
        values = coords.get("values", [])
        if len(values) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Site '{sid}' coordinates missing [latitude, longitude] values."
            )
        lat, lon = float(values[0]), float(values[1])

        elev_m = 0.0
        try:
            elev_m = dem_service.get_site_elevation(lat, lon)
        except Exception:
            elev_m = 0.0

        calc = geom_service.calculate_geometry(
            lat_deg=lat,
            lon_deg=lon,
            elevation_m=elev_m,
            start_utc=start,
            days=days,
            step_minutes=step_minutes,
        )

        comparison_items.append(
            SiteComparisonItemModel(
                site_id=site.id,
                site_name=site.name,
                is_placeholder=site.is_placeholder,
                coordinates=[lat, lon],
                elevation_m=round(elev_m, 2),
                totals=TotalsModel(**calc["totals"]),
            )
        )

    return SiteComparisonResponse(
        label="Modelled",
        frame=FRAME_NAME,
        method="SPICE geometric, flat horizon",
        start_utc=start,
        days=days,
        step_minutes=step_minutes,
        kernels_used=REQUIRED_KERNELS,
        sites=comparison_items,
        disclaimers=DISCLAIMERS,
    )


# ---------------------------------------------------------------------------
# NEW endpoints — B5a
# ---------------------------------------------------------------------------

def _serialize_rows(rows: List[Any]) -> List[Dict[str, Any]]:
    """Convert ComparisonRow objects to plain dicts for JSON storage."""
    out = []
    for r in rows:
        out.append({
            "site_id": r.site_id,
            "site_name": r.site_name,
            "is_placeholder": r.is_placeholder,
            "window_start": r.window_start,
            "window_days": r.window_days,
            "observer_elevation_m": r.observer_elevation_m,
            "illumination": r.illumination.model_dump(),
            "earth": r.earth.model_dump(),
            "slope": r.slope.model_dump(),
            "elevation": r.elevation.model_dump(),
            "hours_both_up": r.hours_both_up,
            "energy_kwh": r.energy_kwh,
            "criteria_results": [c.model_dump() for c in r.criteria_results],
            "data_quality": r.data_quality.model_dump(),
        })
    return out


@router.post("", response_model=CompareResponse)
def landing_window_compare(
    payload: CompareRequest,
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/lunar/compare — B5a terrain-aware multi-site, multi-window comparison.

    Computes per-(site, window) metrics: slope, elevation, illumination, Earth visibility,
    hours both up, optional solar energy. Evaluates optional user-supplied criteria
    (labelled 'example threshold, not an official safety criterion').
    Reports best_by for each metric. Never computes a combined score or labels any site safe.
    Stores the comparison in landing_site_comparisons and returns its id for export.
    """
    if not KernelManager.are_kernels_available():
        missing = KernelManager.check_kernels()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SPICE kernels missing on server: {missing}. Run scripts/download_kernels.py."
        )

    # Load kernels before any SPICE calls
    KernelManager.load_kernels()

    # Resolve all sites first (fail fast on unknown or out-of-coverage)
    site_service = LunarSiteService(db)
    dem_service = get_dem_service()
    sites: List[CandidateLandingSite] = []

    for sid in payload.site_ids:
        site = site_service.repository.get_by_id(sid)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate landing site '{sid}' not found."
            )

    # Validate all window start dates (after kernels loaded)
    try:
        for w in payload.windows:
            safe_str2et(w.start)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid window start date: {exc}"
        )

    # Re-resolve sites into the list (second loop so we keep the 404 check above clean)
    for sid in payload.site_ids:
        site = site_service.repository.get_by_id(sid)
        coords = site.coordinates or {}
        values = coords.get("values", [])
        if len(values) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Site '{sid}' coordinates missing [latitude, longitude] values."
            )
        lat = float(values[0])
        try:
            dem_service.validate_coverage(lat)
        except SiteCoverageError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        sites.append(site)

    svc = LandingWindowService(db=db)

    try:
        result = svc.compute_comparison(sites=sites, request=payload)
    except SiteCoverageError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    rows = result["rows"]
    best_by: BestBy = result["best_by"]
    criteria_list = result["criteria"]

    # Persist to DB
    settings_dict = {
        "site_ids": payload.site_ids,
        "windows": [w.model_dump() for w in payload.windows],
        "step_minutes": payload.step_minutes,
        "observer_height_m": payload.observer_height_m,
        "panel": payload.panel.model_dump() if payload.panel else None,
    }
    thresholds_dict = {c.metric: c.threshold for c in criteria_list} if criteria_list else {}
    criteria_dicts = [c.model_dump() for c in criteria_list] if criteria_list else []

    result_metadata = {
        "settings": settings_dict,
        "rows": _serialize_rows(rows),
        "best_by": best_by.model_dump(),
        "disclaimers": CMP_DISCLAIMERS,
        "kernels_used": list(REQUIRED_KERNELS),
        "method": METHOD_TEXT,
        "elapsed_seconds": result.get("elapsed_seconds"),
    }

    comparison_rec = LandingSiteComparison(
        criteria=criteria_dicts,
        thresholds=thresholds_dict,
        result_metadata=result_metadata,
    )
    db.add(comparison_rec)
    db.commit()
    db.refresh(comparison_rec)

    return CompareResponse(
        id=comparison_rec.id,
        label="Modelled",
        method=METHOD_TEXT,
        kernels_used=list(REQUIRED_KERNELS),
        settings=settings_dict,
        rows=rows,
        best_by=best_by,
        criteria=criteria_list,
        disclaimers=CMP_DISCLAIMERS,
    )


@router.get("/{comparison_id}/export")
def export_comparison(
    comparison_id: int,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: 'json' or 'csv'"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/lunar/compare/{id}/export?format=json|csv

    Returns the criteria, thresholds, settings and results of a stored comparison.
    """
    rec = db.query(LandingSiteComparison).filter(LandingSiteComparison.id == comparison_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison id={comparison_id} not found."
        )

    meta = rec.result_metadata or {}
    export_payload = {
        "id": rec.id,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "criteria": rec.criteria,
        "thresholds": rec.thresholds,
        "settings": meta.get("settings", {}),
        "best_by": meta.get("best_by", {}),
        "disclaimers": meta.get("disclaimers", []),
        "method": meta.get("method", ""),
        "kernels_used": meta.get("kernels_used", []),
        "rows": meta.get("rows", []),
    }

    if format == "json":
        return Response(
            content=json.dumps(export_payload, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=comparison_{comparison_id}.json"},
        )

    # CSV
    rows_data = meta.get("rows", [])
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "site_id", "site_name", "is_placeholder",
        "window_start", "window_days",
        "observer_elevation_m",
        "hours_any_part_lit", "hours_fully_lit", "hours_shadow",
        "longest_shadow_hours", "number_of_lit_windows",
        "hours_earth_visible", "hours_earth_blocked", "number_of_earth_windows",
        "hours_both_up",
        "mean_slope_deg", "max_slope_deg", "p90_slope_deg",
        "mean_elevation_m", "relief_m",
        "energy_kwh",
    ])
    for r in rows_data:
        illum = r.get("illumination", {})
        earth = r.get("earth", {})
        slope = r.get("slope", {})
        elev = r.get("elevation", {})
        writer.writerow([
            r.get("site_id"), r.get("site_name"), r.get("is_placeholder"),
            r.get("window_start"), r.get("window_days"),
            r.get("observer_elevation_m"),
            illum.get("hours_any_part_lit"), illum.get("hours_fully_lit"),
            illum.get("hours_shadow"), illum.get("longest_shadow_hours"),
            illum.get("number_of_lit_windows"),
            earth.get("hours_earth_visible"), earth.get("hours_earth_blocked"),
            earth.get("number_of_earth_windows"),
            r.get("hours_both_up"),
            slope.get("mean_slope_deg"), slope.get("max_slope_deg"),
            slope.get("p90_slope_deg"),
            elev.get("mean_elevation_m"), elev.get("relief_m"),
            r.get("energy_kwh"),
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=comparison_{comparison_id}.csv"},
    )

