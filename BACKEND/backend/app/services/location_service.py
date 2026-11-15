from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.repositories.location_repository import LocationRepository
from backend.app.schemas.location import LocationResponse, CoordinateValues
from backend.app.schemas.common import PaginatedResponse

class LocationService:
    def __init__(self, db: Session):
        self.repository = LocationRepository(db)

    def _to_response(self, loc) -> LocationResponse:
        coords = None
        sol = None
        sclk = None
        original_fields = None

        if loc.original_coordinates and isinstance(loc.original_coordinates, dict):
            coords = CoordinateValues(
                values=loc.original_coordinates.get("values", []),
                units=loc.original_coordinates.get("units", "unknown"),
                coordinate_frame=loc.coordinate_frame or "unknown",
            )
            raw_sol = loc.original_coordinates.get("sol")
            if isinstance(raw_sol, dict):
                sol = raw_sol.get("value")
            elif raw_sol is not None:
                try:
                    sol = int(raw_sol)
                except (ValueError, TypeError):
                    sol = None

            raw_sclk = loc.original_coordinates.get("sclk")
            if isinstance(raw_sclk, dict):
                sclk = str(raw_sclk.get("value")) if raw_sclk.get("value") is not None else None
            elif raw_sclk is not None:
                sclk = str(raw_sclk)

            # Build original_fields dictionary exposing fields with units
            target_keys = [
                "site", "drive", "pose", "sol", "sclk",
                "landing_x", "landing_y", "landing_z",
                "planetocentric_latitude", "planetodetic_latitude",
                "longitude", "elevation", "northing", "easting", "areoid", "radius", "frame", "attitude"
            ]
            fields_dict = {k: loc.original_coordinates[k] for k in target_keys if k in loc.original_coordinates}
            if fields_dict:
                original_fields = fields_dict

        is_placeholder = bool(loc.is_placeholder)
        # Rule: a placeholder can never return a label other than "Unknown"
        label = "Unknown" if is_placeholder else (getattr(loc, "label", "Verified") or "Verified")

        return LocationResponse(
            explorer_id=loc.explorer_id,
            position_status=loc.position_status or "unknown",
            label=label,
            observed_at=loc.observed_at,
            sol=sol,
            sclk=sclk,
            coordinates=coords,
            original_fields=original_fields,
            uncertainty=loc.uncertainty,
            position_method=loc.position_method or "localized",
            source_product_id=loc.product_id,
            retrieved_at=loc.retrieved_at,
            source_label="NASA PDS PLACES Localization Product",
            is_placeholder=is_placeholder,
        )

    def list_locations(
        self,
        explorer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> PaginatedResponse[LocationResponse]:
        total = self.repository.count_locations(explorer_id, start_date=start_date, end_date=end_date)
        records = self.repository.get_locations(
            explorer_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        items = [self._to_response(r) for r in records]
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    def get_latest_location(self, explorer_id: str) -> Optional[LocationResponse]:
        record = self.repository.get_latest_location(explorer_id)
        if not record:
            return LocationResponse(
                explorer_id=explorer_id,
                position_status="unknown",
                label="Unknown",
                observed_at=None,
                sol=None,
                sclk=None,
                coordinates=None,
                original_fields=None,
                uncertainty=None,
                position_method="unknown",
                source_product_id=None,
                retrieved_at=None,
                source_label="NASA PDS PLACES Localization Product",
                is_placeholder=True,
            )
        return self._to_response(record)
