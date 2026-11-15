import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import DataSource, DataProduct, Image, Explorer


class ImagesLoader:
    """
    Idempotent loader for Mars rover raw camera images and provenance.
    Registers DataSources and DataProducts, loads Image records with Verified label.
    """

    def __init__(self, db: Session):
        self.db = db

    def ensure_data_source(self, rover_id: str) -> str:
        """Ensure the official NASA raw images DataSource exists."""
        if rover_id in ("perseverance", "mars-2020"):
            src_id = "src-nasa-mars2020-raw"
            name = "NASA Mars 2020 Perseverance Raw Images Archive"
            url = "https://mars.nasa.gov/mars2020/multimedia/raw-images/"
        else:
            src_id = "src-nasa-msl-raw"
            name = "NASA MSL Curiosity Raw Images Archive"
            url = "https://mars.nasa.gov/msl/multimedia/raw-images/"

        source = self.db.query(DataSource).filter(DataSource.id == src_id).first()
        if not source:
            source = DataSource(
                id=src_id,
                name=name,
                source_url=url,
                organization="NASA / JPL-Caltech",
                is_placeholder=False,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return src_id

    def load_images(self, records: List[Dict[str, Any]], rover_id: str = "perseverance") -> Dict[str, Any]:
        """
        Loads validated image records into database with provenance.
        Skips duplicates idempotently.
        """
        source_id = self.ensure_data_source(rover_id)
        explorer = self.db.query(Explorer).filter(Explorer.id == rover_id).first()
        if not explorer:
            # Fallback if rover_id alias used
            if rover_id == "mars-2020":
                explorer = self.db.query(Explorer).filter(Explorer.id == "perseverance").first()
                if explorer:
                    rover_id = "perseverance"

        loaded_count = 0
        skipped_duplicates = 0
        cameras_seen = set()
        sols_seen = []

        prefix = "m2020" if rover_id == "perseverance" else "msl"

        for rec in records:
            raw_id = rec["id"]
            img_db_id = f"img-{prefix}-{raw_id}"
            prod_id = f"urn:nasa:pds:{prefix}_raw_images:{raw_id}"

            # Check duplicate by image id or product id
            existing = self.db.query(Image).filter(
                (Image.id == img_db_id) | (Image.product_id == prod_id)
            ).first()

            if existing:
                skipped_duplicates += 1
                continue

            # Ensure DataProduct exists
            data_product = self.db.query(DataProduct).filter(DataProduct.id == prod_id).first()
            if not data_product:
                data_product = DataProduct(
                    id=prod_id,
                    source_id=source_id,
                    product_identifier=raw_id,
                    version="1.0",
                    observation_time=rec["captured_at"],
                    retrieved_at=datetime.datetime.utcnow(),
                    coordinate_frame="NASA Planetary Coordinate Reference",
                    units="counts/DN",
                    processing_method="NASA Raw Instrument EDR Browse",
                    label="Verified",
                    is_placeholder=False,
                )
                self.db.add(data_product)
                self.db.flush()

            # Insert Image
            image = Image(
                id=img_db_id,
                explorer_id=rover_id,
                captured_at=rec["captured_at"],
                sol=rec.get("sol"),
                image_url=rec["image_url"],
                camera=rec["camera"],
                product_id=prod_id,
                label="Verified",
                is_placeholder=False,
            )
            self.db.add(image)
            loaded_count += 1
            if rec.get("camera"):
                cameras_seen.add(rec["camera"])
            if rec.get("sol") is not None:
                sols_seen.append(rec["sol"])

        self.db.commit()

        return {
            "loaded": loaded_count,
            "duplicates_skipped": skipped_duplicates,
            "cameras_found": sorted(list(cameras_seen)),
            "sol_min": min(sols_seen) if sols_seen else None,
            "sol_max": max(sols_seen) if sols_seen else None,
        }
