import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from backend.app.models.models import DataSource, DataProduct, Location, Explorer

SOURCE_ID = "src-pds-places"
SOURCE_NAME = "NASA Planetary Data System (PDS) Geosciences Node"
SOURCE_URL = "https://pds-geosciences.wustl.edu/missions/mars2020/places.htm"
ORGANIZATION = "NASA / JPL / Washington University in St. Louis"

class PlacesLoader:
    def __init__(self, db: Session):
        self.db = db

    def register_source(self) -> DataSource:
        """Register or update the PDS PLACES data source."""
        source = self.db.query(DataSource).filter(DataSource.id == SOURCE_ID).first()
        if not source:
            source = DataSource(
                id=SOURCE_ID,
                name=SOURCE_NAME,
                source_url=SOURCE_URL,
                organization=ORGANIZATION,
                is_placeholder=False,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        else:
            if source.is_placeholder:
                source.is_placeholder = False
                self.db.commit()
                self.db.refresh(source)
        return source

    def register_product(
        self,
        product_id: str,
        version: str,
        checksum: str,
        coordinate_frame: str,
        units: str,
        processing_method: str = "Rover localization and traverse mesh reconstruction (PLACES best_interp)",
        label: str = "Estimated",
    ) -> Tuple[DataProduct, bool]:
        """
        Register a DataProduct.
        Detects duplicates by product_id + checksum.
        Returns (DataProduct, is_duplicate).
        """
        self.register_source()

        existing = self.db.query(DataProduct).filter(DataProduct.id == product_id).first()
        if existing:
            if existing.checksum == checksum:
                return existing, True
            else:
                existing.version = version
                existing.checksum = checksum
                existing.retrieved_at = datetime.datetime.now(datetime.timezone.utc)
                existing.coordinate_frame = coordinate_frame
                existing.units = units
                existing.processing_method = processing_method
                existing.label = label
                existing.is_placeholder = False
                self.db.commit()
                self.db.refresh(existing)
                return existing, False

        new_product = DataProduct(
            id=product_id,
            source_id=SOURCE_ID,
            product_identifier=product_id,
            version=version,
            checksum=checksum,
            retrieved_at=datetime.datetime.now(datetime.timezone.utc),
            coordinate_frame=coordinate_frame,
            units=units,
            processing_method=processing_method,
            label=label,
            is_placeholder=False,
        )
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        return new_product, False

    def delete_imported_places_locations(self, product_id: str) -> int:
        """
        Delete only previously imported PLACES rows (is_placeholder=False).
        Existing placeholder rows are preserved.
        """
        deleted = (
            self.db.query(Location)
            .filter(
                Location.is_placeholder == False,
                Location.product_id == product_id,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted

    def load_locations(
        self,
        locations_data: List[Dict[str, Any]],
    ) -> Tuple[int, int]:
        """
        Idempotently load locations.
        Returns (loaded_count, duplicates_skipped).
        Existing placeholder locations are kept untouched.
        """
        explorer = self.db.query(Explorer).filter(Explorer.id == "perseverance").first()
        if not explorer:
            raise ValueError("Explorer 'perseverance' not found in database.")

        loaded_count = 0
        duplicates_skipped = 0

        def _val(f):
            if isinstance(f, dict):
                return f.get("value")
            return f

        product_ids = {loc["product_id"] for loc in locations_data if "product_id" in loc}
        existing_locs = (
            self.db.query(Location)
            .filter(Location.explorer_id == "perseverance", Location.product_id.in_(product_ids))
            .all()
        )

        existing_signatures = set()
        for el in existing_locs:
            oc = el.original_coordinates or {}
            sig = (
                _val(oc.get("site")),
                _val(oc.get("drive")),
                _val(oc.get("pose")),
                str(_val(oc.get("sclk")) or ""),
            )
            existing_signatures.add(sig)

        new_objects = []
        for loc in locations_data:
            oc = loc.get("original_coordinates", {})
            sig = (
                _val(oc.get("site")),
                _val(oc.get("drive")),
                _val(oc.get("pose")),
                str(_val(oc.get("sclk")) or ""),
            )
            if sig in existing_signatures:
                duplicates_skipped += 1
                continue

            existing_signatures.add(sig)
            new_loc = Location(
                explorer_id=loc["explorer_id"],
                observed_at=loc.get("observed_at"),
                original_coordinates=loc["original_coordinates"],
                coordinate_frame=loc["coordinate_frame"],
                uncertainty=loc.get("uncertainty"),
                product_id=loc.get("product_id"),
                position_method=loc.get("position_method", "interpolated"),
                position_status=loc.get("position_status", "estimated"),
                label=loc.get("label", "Estimated"),
                retrieved_at=datetime.datetime.now(datetime.timezone.utc),
                is_placeholder=loc.get("is_placeholder", False),
            )
            new_objects.append(new_loc)
            loaded_count += 1

        if new_objects:
            self.db.add_all(new_objects)
            self.db.commit()

        return loaded_count, duplicates_skipped
