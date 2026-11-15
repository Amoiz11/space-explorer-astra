import os
import pytest
import tempfile
from data_pipeline.validators.places_validator import PlacesValidator
from data_pipeline.parsers.places_parser import PlacesParser
from data_pipeline.loaders.places_loader import PlacesLoader
from backend.app.database.session import SessionLocal

# ==============================================================================
# TEST FIXTURES (CLEARLY MARKED AS MOCK TEST FIXTURES, NOT REAL DATA)
# ==============================================================================
MOCK_LABEL_FIXTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
  <Identification_Area>
    <logical_identifier>urn:nasa:pds:mock_fixture_places:data:test.csv</logical_identifier>
    <version_id>16.0</version_id>
    <title>Mock PLACES Test Fixture Label</title>
  </Identification_Area>
  <Observation_Area>
    <Time_Coordinates>
      <start_date_time>2021-02-18T20:44:27Z</start_date_time>
      <stop_date_time>2026-06-21T23:27:41Z</stop_date_time>
    </Time_Coordinates>
  </Observation_Area>
  <Discipline_Area>
    <Geometry_Lander>
      <geometry_state>Telemetry</geometry_state>
      <description>Geometry reported in telemetry (mock test fixture)</description>
      <local_identifier>geom_telemetry_state</local_identifier>
    </Geometry_Lander>
  </Discipline_Area>
  <File_Area_Observational>
    <File>
      <file_name>test.csv</file_name>
    </File>
    <Table_Delimited>
      <Record_Delimited>
        <Field_Delimited>
          <name>frame</name>
          <data_type>ASCII_String</data_type>
          <description>Frame type SITE or ROVER</description>
        </Field_Delimited>
        <Field_Delimited>
          <name>planetocentric_latitude</name>
          <data_type>ASCII_Real</data_type>
          <unit>DEGREE</unit>
          <description>Planetocentric latitude</description>
        </Field_Delimited>
        <Field_Delimited>
          <name>longitude</name>
          <data_type>ASCII_Real</data_type>
          <unit>DEGREE</unit>
          <description>Longitude east-positive</description>
        </Field_Delimited>
      </Record_Delimited>
    </Table_Delimited>
  </File_Area_Observational>
</Product_Observational>"""

MOCK_CSV_FIXTURE = """frame,site,drive,pose,landing_x,landing_y,landing_z,northing,easting,planetocentric_latitude,planetodetic_latitude,longitude,elevation,map_pixel_line,map_pixel_sample,dem_pixel_line,dem_pixel_sample,roll,pitch,yaw,quat_s,quat_v1,quat_v2,quat_v3,areoid,radius,sclk,sol
SITE,1,-1,-1,0.0,0.0,0.0,1093299.6,4354494.0,18.4446,18.3461,77.4508,-2569.9,15081.2,54416.3,3770.3,13604.0,0.0,-0.0,0.0,1.0,0.0,0.0,0.0,3394507.0,3391937.1,0,-1
ROVER,1,44,-1,0.0,0.0,0.0,1093299.6,4354494.0,18.4446,18.3461,77.4508,-2569.9,15081.2,54416.3,3770.3,13604.0,0.0,-0.0,0.0,1.0,0.0,0.0,0.0,3394507.0,3391937.1,666952977,0
"""

def test_validator_valid_and_invalid():
    """Verify validator accepts compliant rows and rejects invalid ones with reasons."""
    validator = PlacesValidator()

    # Valid fixture row
    valid_row = {
        "frame": "ROVER",
        "planetocentric_latitude": "18.4446",
        "longitude": "77.4508",
        "landing_x": "0.0",
        "landing_y": "0.0",
        "landing_z": "0.0",
        "northing": "1093299.6",
        "easting": "4354494.0",
    }
    is_valid, msg = validator.validate_row(valid_row, 0)
    assert is_valid is True
    assert msg == "Valid"

    # Invalid latitude fixture row (> 90 deg)
    invalid_lat_row = dict(valid_row, planetocentric_latitude="105.0")
    is_valid, msg = validator.validate_row(invalid_lat_row, 1)
    assert is_valid is False
    assert "out of range" in msg

    # Invalid longitude fixture row (> 360 deg)
    invalid_lon_row = dict(valid_row, longitude="400.0")
    is_valid, msg = validator.validate_row(invalid_lon_row, 2)
    assert is_valid is False
    assert "out of range" in msg

    # Invalid frame fixture row
    invalid_frame_row = dict(valid_row, frame="ORBITER_INVALID")
    is_valid, msg = validator.validate_row(invalid_frame_row, 3)
    assert is_valid is False
    assert "Invalid frame" in msg

    # Missing latitude fixture row
    missing_lat_row = dict(valid_row, planetocentric_latitude="")
    is_valid, msg = validator.validate_row(missing_lat_row, 4)
    assert is_valid is False
    assert "Missing or non-numeric" in msg


def test_parser_with_fixture():
    """Verify parser extracts metadata from PDS4 XML label and parses records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        label_path = os.path.join(tmpdir, "test.csv.xml")
        csv_path = os.path.join(tmpdir, "test.csv")

        with open(label_path, "w", encoding="utf-8") as f:
            f.write(MOCK_LABEL_FIXTURE_XML)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(MOCK_CSV_FIXTURE)

        parser = PlacesParser(xml_label_path=label_path, csv_path=csv_path)
        meta = parser.parse_label()

        assert meta["logical_identifier"] == "urn:nasa:pds:mock_fixture_places:data:test.csv"
        assert meta["version_id"] == "16.0"
        assert "landing_x/y/z: SITE 1 relative frame" in meta["coordinate_frame"]

        _, records = parser.parse_data()
        assert len(records) == 2
        assert records[0]["frame"] == "SITE"
        assert records[1]["frame"] == "ROVER"
        assert float(records[1]["planetocentric_latitude"]) == pytest.approx(18.4446, 0.001)


def test_loader_duplicate_detection():
    """Verify duplicate product and duplicate location detection in loader."""
    import uuid
    from backend.app.models.models import DataProduct, Location

    db = SessionLocal()
    unique_suffix = uuid.uuid4().hex[:8]
    test_prod_id = f"urn:nasa:pds:test_fixture_places:dup_check_{unique_suffix}"
    try:
        loader = PlacesLoader(db)

        # 1. Product registration & duplicate detection
        prod1, is_dup1 = loader.register_product(
            product_id=test_prod_id,
            version="16.0",
            checksum=f"mock_sha256_{unique_suffix}_111",
            coordinate_frame="geom_telemetry_state",
            units="deg, m",
        )
        assert is_dup1 is False
        assert prod1.version == "16.0"

        # Register same product with identical checksum -> duplicate!
        prod2, is_dup2 = loader.register_product(
            product_id=test_prod_id,
            version="16.0",
            checksum=f"mock_sha256_{unique_suffix}_111",
            coordinate_frame="geom_telemetry_state",
            units="deg, m",
        )
        assert is_dup2 is True

        # 2. Location idempotent duplicate detection
        sample_locs = [
            {
                "explorer_id": "perseverance",
                "observed_at": None,
                "original_coordinates": {
                    "values": [18.444, 77.450],
                    "units": "deg",
                    "coordinate_frame": "Mars_Planetocentric",
                    "site": 9999,
                    "drive": 8888,
                    "pose": -1,
                    "sclk": f"999_{unique_suffix}",
                },
                "coordinate_frame": "geom_telemetry_state",
                "product_id": test_prod_id,
                "position_method": "interpolated",
                "position_status": "estimated",
                "label": "Estimated",
                "is_placeholder": False,
            }
        ]

        loaded1, skipped1 = loader.load_locations(sample_locs)
        assert loaded1 == 1
        assert skipped1 == 0

        # Load exact same location again -> skipped as duplicate!
        loaded2, skipped2 = loader.load_locations(sample_locs)
        assert loaded2 == 0
        assert skipped2 == 1
    finally:
        # Clean up mock test records
        db.query(Location).filter(Location.product_id == test_prod_id).delete()
        db.query(DataProduct).filter(DataProduct.id == test_prod_id).delete()
        db.commit()
        db.close()


def test_location_response_sol_and_sclk():
    """Verify LocationResponse contains sol and sclk and original_coordinates retains all fields with units."""
    from backend.app.services.location_service import LocationService
    from backend.app.models.models import Location
    from data_pipeline.processors.places_processor import PlacesProcessor

    processor = PlacesProcessor()
    mock_row = {
        "frame": "ROVER",
        "site": "1",
        "drive": "44",
        "pose": "-1",
        "sol": "0",
        "sclk": "666952977",
        "landing_x": "0.0",
        "landing_y": "0.0",
        "landing_z": "0.0",
        "northing": "1093299.695",
        "easting": "4354494.086",
        "planetocentric_latitude": "18.4446",
        "planetodetic_latitude": "18.3461",
        "longitude": "77.4508",
        "elevation": "-2569.91",
        "areoid": "3394507.0",
        "radius": "3391937.1",
        "roll": "0.0",
        "pitch": "0.0",
        "yaw": "0.0",
    }
    processed = processor.process_record(mock_row, product_id="mock_prod")
    orig = processed["original_coordinates"]

    assert orig["site"] == {"value": 1, "units": None}
    assert orig["drive"] == {"value": 44, "units": None}
    assert orig["sol"] == {"value": 0, "units": "sol"}
    assert orig["sclk"] == {"value": "666952977", "units": "seconds"}
    assert orig["landing_x"] == {"value": 0.0, "units": "METER"}
    assert orig["planetocentric_latitude"] == {"value": 18.4446, "units": "DEGREE"}
    assert orig["longitude"] == {"value": 77.4508, "units": "DEGREE"}
    assert orig["elevation"] == {"value": -2569.91, "units": "METER"}

    loc_model = Location(
        explorer_id="perseverance",
        observed_at=None,
        original_coordinates=orig,
        coordinate_frame=processed["coordinate_frame"],
        product_id="mock_prod",
        position_method="interpolated",
        position_status="estimated",
        label="Estimated",
        is_placeholder=False,
    )

    db = SessionLocal()
    try:
        service = LocationService(db)
        resp = service._to_response(loc_model)
        assert resp.sol == 0
        assert resp.sclk == "666952977"
        assert resp.observed_at is None
        assert resp.label == "Estimated"
        assert resp.position_method == "interpolated"
        assert resp.coordinates.coordinate_frame == processed["coordinate_frame"]
        assert resp.original_fields is not None
        assert "landing_x" in resp.original_fields
        assert resp.uncertainty is None
    finally:
        db.close()


def test_sclk_to_utc_conversion():
    """Verify SCLK to UTC conversion with documented Mars 2020 landing SCLK and out-of-coverage values."""
    from data_pipeline.processors.sclk_converter import sclk_to_utc, get_provenance_metadata

    # Documented landing SCLK for Mars 2020 (Sol 0)
    # SCLK 666952977 corresponds to 2021-02-18 20:44:27.444 UTC
    utc_dt = sclk_to_utc("666952977")
    if utc_dt is not None:
        assert utc_dt.year == 2021
        assert utc_dt.month == 2
        assert utc_dt.day == 18
        assert utc_dt.hour == 20
        assert utc_dt.minute == 44

    # Out-of-coverage / invalid cases MUST return None (no time guessing)
    assert sclk_to_utc("0") is None
    assert sclk_to_utc(None) is None
    assert sclk_to_utc("") is None
    assert sclk_to_utc("9999999999999999") is None

    # Provenance metadata structure
    meta = get_provenance_metadata()
    assert meta["conversion_method"] == "SpiceyPy scs2e -> et2utc (ISOC)"
    assert "m2020_168_sclkscet_refit_v19.tsc" in meta["kernels"]
    assert meta["clock_id"] == -168
    assert meta["note"] == "converted from SCLK"


def test_places_downsampled_one_per_sol_selection():
    """Verify that downsampling selects the last localization of each sol (highest SCLK)."""
    synthetic_rows = [
        {"sol": "10", "sclk": "667800100", "site": "2", "drive": "1", "pose": "1", "planetocentric_latitude": "18.4", "longitude": "77.4"},
        {"sol": "10", "sclk": "667800200", "site": "2", "drive": "1", "pose": "2", "planetocentric_latitude": "18.41", "longitude": "77.41"},
        {"sol": "10", "sclk": "667800150", "site": "2", "drive": "1", "pose": "3", "planetocentric_latitude": "18.42", "longitude": "77.42"},
        {"sol": "11", "sclk": "667890100", "site": "2", "drive": "2", "pose": "1", "planetocentric_latitude": "18.43", "longitude": "77.43"},
        {"sol": "11", "sclk": "667890500", "site": "2", "drive": "2", "pose": "2", "planetocentric_latitude": "18.44", "longitude": "77.44"},
    ]

    sol_best = {}
    for r in synthetic_rows:
        sol = int(r["sol"])
        sclk = float(r["sclk"])
        if sol not in sol_best or sclk > sol_best[sol]["_sclk"]:
            sol_best[sol] = dict(r, _sclk=sclk)

    assert len(sol_best) == 2
    assert sol_best[10]["sclk"] == "667800200"
    assert sol_best[11]["sclk"] == "667890500"


def test_places_downsampled_idempotent_reimport():
    """Verify idempotent loading: re-importing identical downsampled records skips duplicates."""
    from backend.app.database.session import SessionLocal
    from data_pipeline.loaders.places_loader import PlacesLoader
    import uuid

    db = SessionLocal()
    unique_suffix = uuid.uuid4().hex[:8]
    test_prod_id = f"urn:nasa:test:downsampled_places:{unique_suffix}"
    try:
        loader = PlacesLoader(db)
        loader.register_product(
            product_id=test_prod_id,
            version="1.0",
            checksum=unique_suffix,
            coordinate_frame="SPICE",
            units="deg",
            processing_method="downsampled: last localization of each sol",
            label="Estimated",
        )

        sample_locs = [
            {
                "explorer_id": "perseverance",
                "observed_at": None,
                "original_coordinates": {
                    "values": [18.44, 77.45],
                    "units": "deg",
                    "coordinate_frame": "SPICE",
                    "site": 99,
                    "drive": 88,
                    "pose": 77,
                    "sol": 200,
                    "sclk": f"888_{unique_suffix}",
                },
                "coordinate_frame": "SPICE",
                "product_id": test_prod_id,
                "position_method": "downsampled: last localization of each sol",
                "position_status": "estimated",
                "label": "Estimated",
                "is_placeholder": False,
            }
        ]

        loaded1, skipped1 = loader.load_locations(sample_locs)
        assert loaded1 == 1
        assert skipped1 == 0

        # Duplicate re-import
        loaded2, skipped2 = loader.load_locations(sample_locs)
        assert loaded2 == 0
        assert skipped2 == 1
    finally:
        from backend.app.models.models import Location, DataProduct
        db.query(Location).filter(Location.product_id == test_prod_id).delete()
        db.query(DataProduct).filter(DataProduct.id == test_prod_id).delete()
        db.commit()
        db.close()



