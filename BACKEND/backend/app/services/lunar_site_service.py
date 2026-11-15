from typing import List, Optional, Dict, Any
import datetime
from sqlalchemy.orm import Session

from backend.app.repositories.lunar_site_repository import LunarSiteRepository
from backend.app.models.models import CandidateLandingSite, TerrainProduct, TerrainMetrics
from backend.app.schemas.lunar_site import (
    CandidateLandingSiteCreate,
    CandidateLandingSiteUpdate,
    CandidateLandingSiteResponse,
)
from backend.app.schemas.terrain_analysis import (
    TerrainAnalysisResponse,
    SlopeAnalysisResponse,
    ElevationStatsModel,
    SlopeStatsModel,
    HistogramModel,
    CriteriaResultModel,
)
from backend.app.services.slope_service import SlopeService, get_slope_service
from backend.app.services.dem_service import SiteCoverageError


DEFAULT_PRODUCT_ID = "lola-dem-75s-240m"
DEFAULT_FALLBACK_PRODUCT = {
    "id": DEFAULT_PRODUCT_ID,
    "resolution": "240 m/pixel (240.0 m/pix, true at south pole)",
    "vertical_reference": "Reference sphere radius: 1737.4 km (A_AXIS_RADIUS from label); OFFSET = 1737400.0 m; HEIGHT = DN * 0.5 (metres relative to reference sphere)",
    "no_data_value": None,
    "coverage": {
        "south_latitude": -90.0,
        "north_latitude": -75.0,
        "west_longitude": "not stated in label",
        "east_longitude": "not stated in label",
        "note": "Full 360 degrees azimuth; corners extend beyond -75 deg edge",
    },
    "coordinate_reference_note": "DSMAP_POLAR.CAT Polar Stereographic (center lat -90 deg, center lon 0 deg, sphere radius 1737.4 km). NOT EPSG:4326.",
}


class LunarSiteService:
    def __init__(self, db: Session, slope_service: Optional[SlopeService] = None):
        self.db = db
        self.repository = LunarSiteRepository(db)
        self.slope_service = slope_service or get_slope_service()

    def list_sites(self, body_id: Optional[str] = "moon") -> List[CandidateLandingSiteResponse]:
        sites = self.repository.get_all(body_id=body_id)
        return [CandidateLandingSiteResponse.model_validate(s) for s in sites]

    def get_site(self, site_id: str) -> Optional[CandidateLandingSiteResponse]:
        site = self.repository.get_by_id(site_id)
        if not site:
            return None
        return CandidateLandingSiteResponse.model_validate(site)

    def create_site(self, site_in: CandidateLandingSiteCreate) -> CandidateLandingSiteResponse:
        data = site_in.model_dump()
        site = self.repository.create(data)
        return CandidateLandingSiteResponse.model_validate(site)

    def update_site(self, site_id: str, site_in: CandidateLandingSiteUpdate) -> Optional[CandidateLandingSiteResponse]:
        data = site_in.model_dump(exclude_unset=True)
        if "coordinates" in data and data["coordinates"] is not None:
            data["coordinates"] = site_in.coordinates.model_dump()
        site = self.repository.update(site_id, data)
        if not site:
            return None
        return CandidateLandingSiteResponse.model_validate(site)

    def delete_site(self, site_id: str) -> bool:
        return self.repository.delete(site_id)

    def _get_product_info(self) -> Dict[str, Any]:
        """Fetch terrain product row from DB or use documented defaults."""
        tp = self.db.query(TerrainProduct).filter(TerrainProduct.id == DEFAULT_PRODUCT_ID).first()
        if tp:
            return {
                "id": tp.id,
                "resolution": tp.resolution,
                "vertical_reference": tp.vertical_reference or DEFAULT_FALLBACK_PRODUCT["vertical_reference"],
                "no_data_value": tp.no_data_value,
                "coverage": tp.coverage or DEFAULT_FALLBACK_PRODUCT["coverage"],
                "coordinate_reference_note": tp.coordinate_reference_note or DEFAULT_FALLBACK_PRODUCT["coordinate_reference_note"],
            }
        return DEFAULT_FALLBACK_PRODUCT

    def _persist_metrics(self, site_id: str, product_id: str, stats: Dict[str, Any], is_placeholder: bool) -> None:
        """Persist or update computed terrain metrics in terrain_metrics table."""
        try:
            metric = self.db.query(TerrainMetrics).filter(
                TerrainMetrics.site_id == site_id,
                TerrainMetrics.product_id == product_id,
            ).first()
            if not metric:
                metric = TerrainMetrics(
                    site_id=site_id,
                    product_id=product_id,
                    computed_at=datetime.datetime.utcnow(),
                    mean_slope=stats["slope"]["mean_deg"],
                    max_slope=stats["slope"]["max_deg"],
                    elevation_stats=stats["elevation"],
                    method=stats["slope"]["method"],
                    is_placeholder=is_placeholder,
                )
                self.db.add(metric)
            else:
                metric.computed_at = datetime.datetime.utcnow()
                metric.mean_slope = stats["slope"]["mean_deg"]
                metric.max_slope = stats["slope"]["max_deg"]
                metric.elevation_stats = stats["elevation"]
                metric.method = stats["slope"]["method"]
                metric.is_placeholder = is_placeholder
            self.db.commit()
        except Exception:
            self.db.rollback()

    def get_site_terrain(self, site_id: str) -> Optional[TerrainAnalysisResponse]:
        """
        Analyze elevation and roughness metrics for a candidate landing site (LL-06, LL-08, LL-09, LL-10).
        Raises SiteCoverageError if site is north of -75°S.
        Returns None if site_id is not found.
        """
        site = self.repository.get_by_id(site_id)
        if not site:
            return None

        coords = site.coordinates or {}
        values = coords.get("values", [])
        if len(values) < 2:
            raise ValueError(f"Site {site_id} coordinates missing [lat, lon] values: {coords}")

        lat, lon = float(values[0]), float(values[1])

        # Validate coverage and run analysis
        stats = self.slope_service.analyze_site(
            lat=lat,
            lon=lon,
            analysis_radius_m=site.analysis_radius_m or 1000.0,
            semi_major_m=site.semi_major_m,
            semi_minor_m=site.semi_minor_m,
            orientation_deg=site.orientation_deg,
            criteria=site.criteria,
        )

        prod_info = self._get_product_info()
        self._persist_metrics(site.id, prod_info["id"], stats, site.is_placeholder)

        return TerrainAnalysisResponse(
            site_id=site.id,
            site_name=site.name,
            is_placeholder=site.is_placeholder,
            label="Derived",
            product_id=prod_info["id"],
            resolution=prod_info["resolution"],
            coverage=prod_info["coverage"],
            vertical_reference=prod_info["vertical_reference"],
            no_data_value=prod_info["no_data_value"],
            coordinate_reference_note=prod_info["coordinate_reference_note"],
            method=stats["elevation"]["roughness_method"],
            units="m",
            pixel_count=stats["pixel_count"],
            elevation=ElevationStatsModel(**stats["elevation"]),
            criteria_result=CriteriaResultModel(**stats["criteria_result"]),
            scale_distortion_note=stats["scale_distortion_note"],
            disclaimer=stats["disclaimer"],
        )

    def get_site_slope(self, site_id: str) -> Optional[SlopeAnalysisResponse]:
        """
        Analyze slope metrics and distribution for a candidate landing site (LL-07, LL-08, LL-10).
        Raises SiteCoverageError if site is north of -75°S.
        Returns None if site_id is not found.
        """
        site = self.repository.get_by_id(site_id)
        if not site:
            return None

        coords = site.coordinates or {}
        values = coords.get("values", [])
        if len(values) < 2:
            raise ValueError(f"Site {site_id} coordinates missing [lat, lon] values: {coords}")

        lat, lon = float(values[0]), float(values[1])

        stats = self.slope_service.analyze_site(
            lat=lat,
            lon=lon,
            analysis_radius_m=site.analysis_radius_m or 1000.0,
            semi_major_m=site.semi_major_m,
            semi_minor_m=site.semi_minor_m,
            orientation_deg=site.orientation_deg,
            criteria=site.criteria,
        )

        prod_info = self._get_product_info()
        self._persist_metrics(site.id, prod_info["id"], stats, site.is_placeholder)

        hist_model = HistogramModel(
            counts=stats["slope"]["histogram"]["counts"],
            bin_edges_deg=stats["slope"]["histogram"]["bin_edges_deg"],
            total_pixels=stats["slope"]["histogram"]["total_pixels"],
        )
        slope_model = SlopeStatsModel(
            mean_deg=stats["slope"]["mean_deg"],
            max_deg=stats["slope"]["max_deg"],
            min_deg=stats["slope"]["min_deg"],
            p50_deg=stats["slope"]["p50_deg"],
            p90_deg=stats["slope"]["p90_deg"],
            p95_deg=stats["slope"]["p95_deg"],
            method=stats["slope"]["method"],
            pixel_spacing_m=stats["slope"]["pixel_spacing_m"],
            histogram=hist_model,
        )

        return SlopeAnalysisResponse(
            site_id=site.id,
            site_name=site.name,
            is_placeholder=site.is_placeholder,
            label="Derived",
            product_id=prod_info["id"],
            resolution=prod_info["resolution"],
            coverage=prod_info["coverage"],
            vertical_reference=prod_info["vertical_reference"],
            no_data_value=prod_info["no_data_value"],
            coordinate_reference_note=prod_info["coordinate_reference_note"],
            method=stats["slope"]["method"],
            units="deg",
            pixel_count=stats["pixel_count"],
            slope=slope_model,
            criteria_result=CriteriaResultModel(**stats["criteria_result"]),
            scale_distortion_note=stats["scale_distortion_note"],
            disclaimer=stats["disclaimer"],
        )
