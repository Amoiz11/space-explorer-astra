import os
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from data_pipeline.collectors.lunar_pds_collector import LunarPDSCollector
from data_pipeline.parsers.lunar_metadata_parser import LunarMetadataParser
from backend.app.models.models import DataSource, DataProduct, TerrainProduct


BASE_GDR_URL = "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/"

# Available south-polar LDEM products discovered on NASA PDS Geosciences Node
AVAILABLE_SOUTH_POLAR_PRODUCTS = [
    {
        "filename": "ldem_75s_240m.img",
        "lbl_filename": "ldem_75s_240m.lbl",
        "xml_filename": "ldem_75s_240m.xml",
        "resolution": "240 m/pixel",
        "coverage": "75S to 90S",
        "size_bytes": 29062688,
        "size_mb": 27.72,
    },
    {
        "filename": "ldem_85s_40m.img",
        "lbl_filename": "ldem_85s_40m.lbl",
        "xml_filename": "ldem_85s_40m.xml",
        "resolution": "40 m/pixel",
        "coverage": "85S to 90S",
        "size_bytes": 115034112,
        "size_mb": 109.71,
    },
    {
        "filename": "ldem_875s_20m.img",
        "lbl_filename": "ldem_875s_20m.lbl",
        "xml_filename": "ldem_875s_20m.xml",
        "resolution": "20 m/pixel",
        "coverage": "87.5S to 90S",
        "size_bytes": 115034112,
        "size_mb": 109.71,
    },
    {
        "filename": "ldem_75s_120m.img",
        "lbl_filename": "ldem_75s_120m.lbl",
        "xml_filename": "ldem_75s_120m.xml",
        "resolution": "120 m/pixel",
        "coverage": "75S to 90S",
        "size_bytes": 116250752,
        "size_mb": 110.87,
    },
    {
        "filename": "ldem_60s_240m.img",
        "lbl_filename": "ldem_60s_240m.lbl",
        "xml_filename": "ldem_60s_240m.xml",
        "resolution": "240 m/pixel",
        "coverage": "60S to 90S",
        "size_bytes": 240870400,
        "size_mb": 229.71,
    },
    {
        "filename": "ldem_45s_400m.img",
        "lbl_filename": "ldem_45s_400m.lbl",
        "xml_filename": "ldem_45s_400m.xml",
        "resolution": "400 m/pixel",
        "coverage": "45S to 90S",
        "size_bytes": 207360000,
        "size_mb": 197.75,
    },
]


class LROLOLACollector:
    """
    Collector for Lunar Reconnaissance Orbiter (LRO) LOLA Gridded Data Records (GDR).
    Discovers, downloads, parses and registers Lunar south-polar DEM products.
    """

    def __init__(self, target_dir: str = "storage/raw/lunar"):
        self.collector = LunarPDSCollector(target_dir=target_dir)
        self.parser = LunarMetadataParser()

    def list_available_products(self) -> List[Dict[str, Any]]:
        """Return list of discovered south-polar DEM products with resolution and size."""
        return AVAILABLE_SOUTH_POLAR_PRODUCTS

    def get_smallest_product(self) -> Dict[str, Any]:
        """Select the smallest suitable south-polar DEM product."""
        sorted_prods = sorted(AVAILABLE_SOUTH_POLAR_PRODUCTS, key=lambda x: x["size_bytes"])
        return sorted_prods[0]

    def download_product(self, product_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Download chosen product image and label files from NASA PDS."""
        if not product_info:
            product_info = self.get_smallest_product()

        # Check safety threshold
        if product_info["size_bytes"] > 200 * 1024 * 1024:
            raise ValueError(
                f"Product size ({product_info['size_mb']} MB) exceeds safety threshold of ~200 MB. "
                "Manual user confirmation required."
            )

        img_url = BASE_GDR_URL + product_info["filename"]
        lbl_url = BASE_GDR_URL + product_info["lbl_filename"]
        xml_url = BASE_GDR_URL + product_info["xml_filename"]

        # Download label files first
        lbl_res = self.collector.download_file(lbl_url, filename=product_info["lbl_filename"])
        xml_res = self.collector.download_file(xml_url, filename=product_info["xml_filename"])

        # Download IMG file
        img_res = self.collector.download_file(img_url, filename=product_info["filename"])

        # Parse metadata from label
        parsed_meta = self.parser.parse_file(lbl_res["file_path"])

        return {
            "product_info": product_info,
            "img": img_res,
            "lbl": lbl_res,
            "xml": xml_res,
            "metadata": parsed_meta,
        }

    def register_in_db(self, download_result: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Register downloaded product in data_sources, data_products, and terrain_products tables.
        """
        meta = download_result["metadata"]
        img_info = download_result["img"]

        # 1. Data Source: NASA PDS Geosciences Node (LRO LOLA)
        source_id = "src-pds-lro-lola"
        data_source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if not data_source:
            data_source = DataSource(
                id=source_id,
                name="NASA Planetary Data System (PDS) Geosciences Node - LRO LOLA",
                source_url="https://pds-geosciences.wustl.edu/missions/lro/lola.htm",
                organization="NASA / GSFC",
                is_placeholder=False,
            )
            db.add(data_source)
            db.flush()

        # 2. Data Product
        product_identifier = "urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_75s_240m"
        data_product = db.query(DataProduct).filter(DataProduct.id == product_identifier).first()
        if not data_product:
            data_product = DataProduct(
                id=product_identifier,
                source_id=source_id,
                product_identifier=product_identifier,
                version=meta.get("version") or "V2.0",
                checksum=img_info.get("sha256") or img_info.get("md5"),
                observation_time=datetime.datetime(2009, 7, 13, 17, 33, 17, tzinfo=datetime.timezone.utc),
                retrieved_at=datetime.datetime.now(datetime.timezone.utc),
                coordinate_frame="MOON_ME_DE421",
                units=meta.get("units") or "METER",
                processing_method="Interpolated using Generic Mapping Tools programs 'mapproject', 'blockmedian' and 'surface'",
                uncertainty=None,
                label="Verified",
                is_placeholder=False,
            )
            db.add(data_product)
            db.flush()
        else:
            data_product.checksum = img_info.get("sha256") or img_info.get("md5")
            data_product.retrieved_at = datetime.datetime.now(datetime.timezone.utc)
            data_product.processing_method = "Interpolated using Generic Mapping Tools programs 'mapproject', 'blockmedian' and 'surface'"
            data_product.uncertainty = None
            db.flush()

        # 3. Terrain Product
        terrain_prod_id = "lola-dem-75s-240m"
        terrain_product = db.query(TerrainProduct).filter(TerrainProduct.id == terrain_prod_id).first()
        if not terrain_product:
            terrain_product = TerrainProduct(
                id=terrain_prod_id,
                source_product_id=product_identifier,
                resolution=meta.get("resolution") or "240 m/pixel",
                vertical_reference=meta.get("vertical_reference"),
                coverage=meta.get("coverage"),
                version=meta.get("version") or "V2.0",
                no_data_value=meta.get("no_data_value"),
                coordinate_reference_note=meta.get("coordinate_reference_note"),
            )
            db.add(terrain_product)
            db.flush()
        else:
            terrain_product.resolution = meta.get("resolution") or "240 m/pixel"
            terrain_product.vertical_reference = meta.get("vertical_reference")
            terrain_product.coverage = meta.get("coverage")
            terrain_product.version = meta.get("version") or "V2.0"
            terrain_product.no_data_value = meta.get("no_data_value")
            terrain_product.coordinate_reference_note = meta.get("coordinate_reference_note")
            db.flush()

        db.commit()

        return {
            "source_id": source_id,
            "product_id": product_identifier,
            "terrain_product_id": terrain_prod_id,
            "status": "registered",
        }


def run_collection(db: Session) -> Dict[str, Any]:
    """Execute download and database registration."""
    collector = LROLOLACollector()
    smallest = collector.get_smallest_product()
    download_res = collector.download_product(smallest)
    reg_res = collector.register_in_db(download_res, db)
    return {
        "download": download_res,
        "registration": reg_res,
    }


if __name__ == "__main__":
    from backend.app.database.session import SessionLocal
    db = SessionLocal()
    try:
        res = run_collection(db)
        print("Collection and registration successful:")
        print(f"Product: {res['registration']['product_id']}")
        print(f"Size: {res['download']['img']['size_mb']} MB")
        print(f"SHA-256: {res['download']['img']['sha256']}")
    finally:
        db.close()
