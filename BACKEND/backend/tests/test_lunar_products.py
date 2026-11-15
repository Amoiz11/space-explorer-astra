import datetime
import pytest
from data_pipeline.parsers.lunar_metadata_parser import LunarMetadataParser
from backend.app.database.session import SessionLocal
from backend.app.models.models import DataSource, DataProduct, TerrainProduct, Mission


@pytest.fixture
def db_session():
    with SessionLocal() as session:
        yield session


# Synthetic PDS3 label fixture clearly marked as test fixture (no network required)
SYNTHETIC_PDS3_LBL_FIXTURE = """
PDS_VERSION_ID            = "PDS3"
PRODUCT_VERSION_ID        = "V2.0"
DATA_SET_ID               = "LRO-L-LOLA-4-GDR-V1.0"

INSTRUMENT_HOST_NAME      = "LUNAR RECONNAISSANCE ORBITER"
INSTRUMENT_NAME           = "LUNAR ORBITER LASER ALTIMETER"
INSTRUMENT_ID             = "LOLA"
TARGET_NAME               = MOON
FILE_NAME                 = "LDEM_75S_240M_FIXTURE.IMG"
PRODUCT_ID                = "urn:nasa:pds:test_fixture:ldem_75s_240m"

OBJECT                    = UNCOMPRESSED_FILE
FILE_NAME                 = "LDEM_75S_240M_FIXTURE.IMG"
RECORD_TYPE               = FIXED_LENGTH
RECORD_BYTES              = 7624
FILE_RECORDS              = 3812
^IMAGE                    = "LDEM_75S_240M_FIXTURE.IMG"
  OBJECT                  = IMAGE
    NAME                  = HEIGHT
    LINES                 = 3812
    LINE_SAMPLES          = 3812
    SAMPLE_TYPE           = LSB_INTEGER
    SAMPLE_BITS           = 16
    UNIT                  = METER
    SCALING_FACTOR        = 0.5
    OFFSET                = 1737400.
  END_OBJECT              = IMAGE
END_OBJECT                = UNCOMPRESSED_FILE

OBJECT                    = IMAGE_MAP_PROJECTION
 MAP_PROJECTION_TYPE          = "POLAR STEREOGRAPHIC"
 KEYWORD_LATITUDE_TYPE        = "PLANETOCENTRIC"
 MAP_RESOLUTION               = 126.347 <pix/deg>
 A_AXIS_RADIUS                = 1737.4 <km>
 POSITIVE_LONGITUDE_DIRECTION = "EAST"
 CENTER_LATITUDE              = -90 <deg>
 CENTER_LONGITUDE             = 0 <deg>
 MAP_SCALE                    = 240 <m/pix>
 MAXIMUM_LATITUDE             = -75 <deg>
 MINIMUM_LATITUDE             = -90 <deg>
 WESTERNMOST_LONGITUDE        = 'N/A'
 EASTERNMOST_LONGITUDE        = 'N/A'
 COORDINATE_SYSTEM_NAME       = "MEAN EARTH/POLAR AXIS OF DE421"
END_OBJECT                    = IMAGE_MAP_PROJECTION

END
"""


def test_lunar_metadata_parser_synthetic_fixture():
    """Verify LunarMetadataParser extracts correct metadata and notes non-stated values."""
    parser = LunarMetadataParser()
    meta = parser.parse_pds3_label(SYNTHETIC_PDS3_LBL_FIXTURE)

    assert meta["version"] == "V2.0"
    assert meta["resolution"] == "240 m/pixel"
    assert meta["units"] == "METER"

    # Coverage
    cov = meta["coverage"]
    assert cov["south_latitude"] == -90.0
    assert cov["north_latitude"] == -75.0
    assert cov["west_longitude"] == "not stated in label"
    assert cov["east_longitude"] == "not stated in label"

    # Vertical reference
    assert "1737.4" in meta["vertical_reference"]
    assert "1737400" in meta["vertical_reference"]

    # Coordinate reference (never EPSG:4326)
    assert "EPSG:4326" not in meta["coordinate_reference_note"]
    assert "polar stereographic" in meta["coordinate_reference_note"].lower()
    assert "MEAN EARTH/POLAR AXIS OF DE421" in meta["coordinate_reference_note"]

    # No-data value is not in label -> None with note
    assert meta["no_data_value"] is None
    assert meta["no_data_note"] == "not stated in label"


def test_lunar_product_endpoint(client, db_session):
    """Verify GET /api/v1/lunar/products/{id} returns product with provenance and disclaimer."""
    # Seed test fixture in temporary DB session
    source = DataSource(
        id="src-pds-test-fixture",
        name="NASA PDS Test Geosciences Node",
        source_url="https://pds-geosciences.wustl.edu/missions/lro/lola.htm",
        organization="NASA / GSFC",
        is_placeholder=False,
    )
    db_session.add(source)
    db_session.flush()

    prod = DataProduct(
        id="urn:nasa:pds:test_fixture:lola_dem_75s_240m",
        source_id="src-pds-test-fixture",
        product_identifier="urn:nasa:pds:test_fixture:lola_dem_75s_240m",
        version="V2.0",
        checksum="test-sha256-checksum-1234567890abcdef",
        observation_time=datetime.datetime(2009, 7, 13, 17, 33, 17, tzinfo=datetime.timezone.utc),
        retrieved_at=datetime.datetime(2026, 11, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
        coordinate_frame="MOON_ME_DE421",
        units="METER",
        processing_method="Interpolated using Generic Mapping Tools",
        uncertainty=None,
        label="Verified",
        is_placeholder=False,
    )
    db_session.add(prod)
    db_session.flush()

    terrain_prod = TerrainProduct(
        id="lola-dem-75s-240m-fixture",
        source_product_id="urn:nasa:pds:test_fixture:lola_dem_75s_240m",
        resolution="240 m/pixel",
        vertical_reference="Reference sphere radius: 1737.4 km (OFFSET = 1737400. m)",
        coverage={"south_latitude": -90.0, "north_latitude": -75.0},
        version="V2.0",
        no_data_value=None,
        coordinate_reference_note="Polar Stereographic, MOON_ME_DE421",
    )
    db_session.add(terrain_prod)
    db_session.commit()

    # Call endpoint
    res = client.get("/api/v1/lunar/products/lola-dem-75s-240m-fixture")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == "lola-dem-75s-240m-fixture"
    assert data["resolution"] == "240 m/pixel"
    assert data["source_name"] == "NASA PDS Test Geosciences Node"
    assert data["checksum"] == "test-sha256-checksum-1234567890abcdef"
    assert data["label"] == "Verified"
    assert data["is_placeholder"] is False
    assert "micro-hazards" in data["disclaimer"]
    assert "cannot detect small rocks" in data["disclaimer"]


def test_lunar_product_not_found(client):
    """Verify 404 for unknown lunar terrain product."""
    res = client.get("/api/v1/lunar/products/unknown-non-existent-product")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_lro_mission_record(client):
    """Verify LRO mission record is present in temporary DB and correctly initialized."""
    res = client.get("/api/v1/missions/lro")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "lro"
    assert data["name"] == "Lunar Reconnaissance Orbiter"
    assert data["body_id"] == "moon"
    assert data["is_placeholder"] is False
    assert "2009-06-18" in data["launch_date"]
    assert data["landing_date"] is None
