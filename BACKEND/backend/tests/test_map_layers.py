"""
Tests for GeoJSON exporter (Phase 6 / MMGIS).
All tests use isolated fixture data - never the real database.
"""
import pytest
from data_pipeline.exporters.geojson_exporter import GeoJSONExporter


# ---------------------------------------------------------------------------
# Minimal Location fixture objects (plain dicts - never real DB data)
# ---------------------------------------------------------------------------

FIXTURE_LANDING_LOC = {
    "explorer_id": "perseverance",
    "observed_at": None,
    "original_coordinates": {
        "values": [18.4446, 77.4508],
        "units": "deg",
        "site": {"value": 1, "units": None},
        "drive": {"value": -1, "units": None},
        "pose": {"value": -1, "units": None},
        "sol": {"value": -1, "units": "sol"},
        "sclk": {"value": "0", "units": "seconds"},
        "landing_x": {"value": 0.0, "units": "METER"},
        "landing_y": {"value": 0.0, "units": "METER"},
        "landing_z": {"value": 0.0, "units": "METER"},
        "planetocentric_latitude": {"value": 18.4446, "units": "DEGREE"},
        "planetodetic_latitude": {"value": 18.3461, "units": "DEGREE"},
        "longitude": {"value": 77.4508, "units": "DEGREE"},
        "elevation": {"value": -2569.91, "units": "METER"},
    },
    "coordinate_frame": (
        "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
        "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
        "Mars body-fixed frame name not stated in the label."
    ),
    "product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
    "position_method": "interpolated",
    "position_status": "estimated",
    "label": "Estimated",
    "is_placeholder": False,
}

FIXTURE_DRIVE_LOC = {
    "explorer_id": "perseverance",
    "observed_at": None,
    "original_coordinates": {
        "values": [18.5000, 77.5000],
        "units": "deg",
        "site": {"value": 1, "units": None},
        "drive": {"value": 44, "units": None},
        "pose": {"value": -1, "units": None},
        "sol": {"value": 10, "units": "sol"},
        "sclk": {"value": "666952977", "units": "seconds"},
        "landing_x": {"value": 50.0, "units": "METER"},
        "landing_y": {"value": 10.0, "units": "METER"},
        "landing_z": {"value": -1.0, "units": "METER"},
        "planetocentric_latitude": {"value": 18.5000, "units": "DEGREE"},
        "planetodetic_latitude": {"value": 18.4015, "units": "DEGREE"},
        "longitude": {"value": 77.5000, "units": "DEGREE"},
        "elevation": {"value": -2560.00, "units": "METER"},
    },
    "coordinate_frame": (
        "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
        "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
        "Mars body-fixed frame name not stated in the label."
    ),
    "product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
    "position_method": "interpolated",
    "position_status": "estimated",
    "label": "Estimated",
    "is_placeholder": False,
}

FIXTURE_PLACEHOLDER_LOC = {
    "explorer_id": "perseverance",
    "observed_at": None,
    "original_coordinates": {
        "values": [18.4446, 77.4508],
        "units": "deg",
        "sol": {"value": 5, "units": "sol"},
        "sclk": {"value": "12345", "units": "seconds"},
        "planetocentric_latitude": {"value": 18.4446, "units": "DEGREE"},
        "longitude": {"value": 77.4508, "units": "DEGREE"},
    },
    "coordinate_frame": "IAU_MARS_2000",
    "product_id": "urn:nasa:pds:mars2020_rover_places:site_0001",
    "position_method": "localized",
    "position_status": "estimated",
    "label": "Unknown",
    "is_placeholder": True,
}

FIXTURE_INVALID_LOC = {
    "explorer_id": "perseverance",
    "observed_at": None,
    "original_coordinates": {
        "values": [999.9, 999.9],  # invalid coordinates
        "units": "deg",
        "sol": {"value": 20, "units": "sol"},
        "sclk": {"value": "77777", "units": "seconds"},
    },
    "coordinate_frame": "IAU_MARS_2000",
    "product_id": "urn:nasa:pds:test_fixture_bad",
    "position_method": "interpolated",
    "label": "Estimated",
    "is_placeholder": False,
}

FIXTURE_CANDIDATE_SITE_1 = {
    "id": "site-fixture-shackleton",
    "name": "Shackleton Rim Test Fixture",
    "body_id": "moon",
    "coordinates": {"values": [-89.9, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
    "frame": "MOON_ME_DE421",
    "analysis_radius_m": 1000.0,
    "notes": "Test fixture candidate site.",
    "is_placeholder": True,
}

FIXTURE_CANDIDATE_SITE_2 = {
    "id": "site-fixture-connecting-ridge",
    "name": "Connecting Ridge Test Fixture",
    "body_id": "moon",
    "coordinates": {"values": [-89.5, 120.0], "units": "deg", "frame": "MOON_ME_DE421"},
    "frame": "MOON_ME_DE421",
    "analysis_radius_m": 1500.0,
    "notes": "Test fixture candidate site 2.",
    "is_placeholder": False,
}


# ---------------------------------------------------------------------------
# Tests: GeoJSON Exporter (unit tests with fixture dicts)
# ---------------------------------------------------------------------------

class TestGeoJSONExporterStructure:
    """Test valid GeoJSON structure from the exporter."""

    def test_locations_feature_collection_structure(self):
        """Must produce valid GeoJSON FeatureCollection with correct top-level keys."""
        fc = GeoJSONExporter.export_locations_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC], explorer_id="perseverance"
        )
        assert fc["type"] == "FeatureCollection"
        assert "features" in fc
        assert isinstance(fc["features"], list)
        assert "properties" in fc
        assert fc["properties"]["explorer_id"] == "perseverance"
        assert fc["properties"]["layer"] == "historical-positions"

    def test_no_epsg4326_claim(self):
        """GeoJSON output must never reference EPSG:4326."""
        fc = GeoJSONExporter.export_locations_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC]
        )
        import json
        fc_json = json.dumps(fc)
        assert "EPSG:4326" not in fc_json
        assert "epsg:4326" not in fc_json.lower()

    def test_coordinate_reference_note_present(self):
        """Must have coordinate_reference_note at top level and properties level."""
        fc = GeoJSONExporter.export_locations_feature_collection([FIXTURE_DRIVE_LOC])
        note = fc.get("coordinate_reference_note") or fc["properties"].get("coordinate_reference_note")
        assert note is not None
        assert "Mars planetocentric" in note
        assert "EPSG" not in note

    def test_coordinates_order_lon_lat(self):
        """GeoJSON coordinates order must be [longitude, latitude]."""
        fc = GeoJSONExporter.export_locations_feature_collection([FIXTURE_DRIVE_LOC])
        assert len(fc["features"]) >= 1
        pt = fc["features"][0]
        # For FIXTURE_DRIVE_LOC: lat=18.5, lon=77.5 → coords should be [77.5, 18.5]
        coords = pt["geometry"]["coordinates"]
        assert len(coords) == 2
        assert coords[0] == pytest.approx(77.5000, abs=0.001)  # longitude first
        assert coords[1] == pytest.approx(18.5000, abs=0.001)  # latitude second

    def test_invalid_coordinates_excluded(self):
        """Rows with invalid coordinates (out of range) must be excluded from features."""
        fc = GeoJSONExporter.export_locations_feature_collection([FIXTURE_INVALID_LOC])
        assert fc["features"] == []

    def test_placeholder_flag_preserved(self):
        """is_placeholder must be preserved in feature properties."""
        fc = GeoJSONExporter.export_locations_feature_collection(
            [FIXTURE_PLACEHOLDER_LOC, FIXTURE_DRIVE_LOC]
        )
        props_map = {f["properties"]["source_product_id"]: f["properties"] for f in fc["features"]}
        placeholder_props = props_map.get("urn:nasa:pds:mars2020_rover_places:site_0001")
        assert placeholder_props is not None
        assert placeholder_props["is_placeholder"] is True

        non_placeholder_props = props_map.get(
            "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv"
        )
        assert non_placeholder_props is not None
        assert non_placeholder_props["is_placeholder"] is False

    def test_sol_minus1_feature_role(self):
        """Rows with sol == -1 must have feature_role: landing_site_reference."""
        fc = GeoJSONExporter.export_locations_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC]
        )
        landing_features = [
            f for f in fc["features"] if f["properties"].get("feature_role") == "landing_site_reference"
        ]
        drive_features = [
            f for f in fc["features"] if f["properties"].get("feature_role") == "drive_point"
        ]
        assert len(landing_features) == 1
        assert len(drive_features) == 1
        assert landing_features[0]["properties"]["sol"] == -1

    def test_interpolated_label_set_to_estimated(self):
        """Interpolated points must carry label Estimated regardless of stored value."""
        loc_with_verified = dict(FIXTURE_DRIVE_LOC, label="Verified", position_method="interpolated")
        fc = GeoJSONExporter.export_locations_feature_collection([loc_with_verified])
        for f in fc["features"]:
            assert f["properties"]["label"] == "Estimated"

    def test_placeholder_gets_feature_role_placeholder(self):
        """
        Placeholder rows must get feature_role 'placeholder'.
        They must NOT get 'landing_site_reference' even if sol == -1.
        """
        # Placeholder row with sol == -1 (should NOT be landing_site_reference)
        placeholder_sol_neg1 = dict(
            FIXTURE_PLACEHOLDER_LOC,
            original_coordinates=dict(
                FIXTURE_PLACEHOLDER_LOC["original_coordinates"],
                sol={"value": -1, "units": "sol"},
            ),
        )
        fc = GeoJSONExporter.export_locations_feature_collection([placeholder_sol_neg1])
        assert len(fc["features"]) == 1
        props = fc["features"][0]["properties"]
        assert props["feature_role"] == "placeholder"
        assert props["is_placeholder"] is True

    def test_placeholder_sol_minus1_not_landing_ref(self):
        """
        A placeholder row with sol == -1 must never become 'landing_site_reference'.
        Only a real non-placeholder row with sol == -1 qualifies.
        """
        placeholder_sol_neg1 = dict(
            FIXTURE_PLACEHOLDER_LOC,
            original_coordinates=dict(
                FIXTURE_PLACEHOLDER_LOC["original_coordinates"],
                sol={"value": -1, "units": "sol"},
            ),
        )
        real_sol_neg1 = FIXTURE_LANDING_LOC  # is_placeholder=False, sol=-1

        fc = GeoJSONExporter.export_locations_feature_collection(
            [placeholder_sol_neg1, real_sol_neg1]
        )
        roles = {f["properties"]["is_placeholder"]: f["properties"]["feature_role"] for f in fc["features"]}
        # Placeholder → "placeholder"
        assert roles[True] == "placeholder"
        # Real non-placeholder sol==-1 → "landing_site_reference"
        assert roles[False] == "landing_site_reference"


class TestGeoJSONTraversedRoute:
    """Test traversed route exports."""

    def test_route_has_linestring_and_landing_point(self):
        """Route must have a LineString feature and a separate landing_site_reference Point."""
        fc = GeoJSONExporter.export_traversed_route_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC], explorer_id="perseverance"
        )
        types = {f["geometry"]["type"] for f in fc["features"]}
        assert "LineString" in types
        assert "Point" in types  # landing site reference

    def test_landing_site_excluded_from_route_line(self):
        """sol == -1 coords must NOT be included in the traversed route LineString."""
        fc = GeoJSONExporter.export_traversed_route_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC]
        )
        lines = [f for f in fc["features"] if f["geometry"]["type"] == "LineString"]
        assert len(lines) == 1
        line_coords = lines[0]["geometry"]["coordinates"]
        # Only drive points (sol 10) should be in the line
        for c in line_coords:
            assert c[0] == pytest.approx(77.5000, abs=0.01)
            assert c[1] == pytest.approx(18.5000, abs=0.01)

    def test_route_label_is_estimated(self):
        """Traversed route LineString must carry label: Estimated."""
        fc = GeoJSONExporter.export_traversed_route_feature_collection(
            [FIXTURE_DRIVE_LOC]
        )
        lines = [f for f in fc["features"] if f["geometry"]["type"] == "LineString"]
        assert len(lines) == 1
        assert lines[0]["properties"]["label"] == "Estimated"

    def test_placeholder_excluded_from_route_and_not_landing_ref(self):
        """
        Placeholder rows must be entirely excluded from the traversed route:
        not in the LineString coordinates and not as a landing_site_reference Point.
        """
        # Mix: one real landing ref (sol=-1, is_placeholder=False),
        #      one real drive point, one placeholder (sol=-1, is_placeholder=True)
        placeholder_sol_neg1 = dict(
            FIXTURE_PLACEHOLDER_LOC,
            original_coordinates=dict(
                FIXTURE_PLACEHOLDER_LOC["original_coordinates"],
                sol={"value": -1, "units": "sol"},
            ),
        )
        fc = GeoJSONExporter.export_traversed_route_feature_collection(
            [FIXTURE_LANDING_LOC, FIXTURE_DRIVE_LOC, placeholder_sol_neg1]
        )
        # Placeholder must not appear as landing_site_reference
        landing_refs = [
            f for f in fc["features"]
            if f["properties"].get("feature_role") == "landing_site_reference"
        ]
        assert len(landing_refs) == 1
        assert landing_refs[0]["properties"]["is_placeholder"] is False

        # Placeholder coords must not be in the LineString
        lines = [f for f in fc["features"] if f["geometry"]["type"] == "LineString"]
        assert len(lines) == 1
        for c in lines[0]["geometry"]["coordinates"]:
            # Placeholder coords are [77.4508, 18.4446] same as landing loc —
            # but drive loc is [77.5, 18.5]; the landing loc (sol=-1, real) is a Point, not in line
            assert c[0] == pytest.approx(77.5000, abs=0.01)


class TestGeoJSONCandidateSites:
    """Test candidate lunar sites export."""

    def test_candidate_sites_structure(self):
        """Must be a valid GeoJSON FeatureCollection of Points."""
        fc = GeoJSONExporter.export_candidate_sites_feature_collection(
            [FIXTURE_CANDIDATE_SITE_1, FIXTURE_CANDIDATE_SITE_2]
        )
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) == 2
        for f in fc["features"]:
            assert f["type"] == "Feature"
            assert f["geometry"]["type"] == "Point"

    def test_candidate_site_placeholder_flag_preserved(self):
        """is_placeholder must be preserved per site."""
        fc = GeoJSONExporter.export_candidate_sites_feature_collection(
            [FIXTURE_CANDIDATE_SITE_1, FIXTURE_CANDIDATE_SITE_2]
        )
        flags = {f["properties"]["id"]: f["properties"]["is_placeholder"] for f in fc["features"]}
        assert flags["site-fixture-shackleton"] is True
        assert flags["site-fixture-connecting-ridge"] is False

    def test_candidate_site_no_epsg4326(self):
        """Must never reference EPSG:4326."""
        import json
        fc = GeoJSONExporter.export_candidate_sites_feature_collection(
            [FIXTURE_CANDIDATE_SITE_1]
        )
        fc_json = json.dumps(fc)
        assert "EPSG:4326" not in fc_json
        assert "epsg:4326" not in fc_json.lower()

    def test_candidate_site_coordinates_lon_lat_order(self):
        """GeoJSON coordinates must be [longitude, latitude]."""
        # Site 1: lat=-89.9, lon=0.0 → coords should be [0.0, -89.9]
        fc = GeoJSONExporter.export_candidate_sites_feature_collection(
            [FIXTURE_CANDIDATE_SITE_1]
        )
        coords = fc["features"][0]["geometry"]["coordinates"]
        assert coords[0] == pytest.approx(0.0, abs=0.001)   # longitude
        assert coords[1] == pytest.approx(-89.9, abs=0.001)  # latitude


class TestMapLayersEndpoints:
    """Test /api/v1/map/layers endpoints using the isolated test client."""

    def test_get_layers_mars_mission(self, client):
        """Mars mission must return at least historical-positions and traversed-route layers."""
        response = client.get("/api/v1/map/layers/mars-2020")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        ids = [l["id"] for l in data]
        assert "historical-positions" in ids
        assert "traversed-route" in ids

    def test_get_layers_moon_mission(self, client):
        """Moon mission must return candidate-lunar-sites layer."""
        response = client.get("/api/v1/map/layers/artemis-lunar")
        assert response.status_code == 200
        data = response.json()
        ids = [l["id"] for l in data]
        assert "candidate-lunar-sites" in ids

    def test_get_layers_unknown_mission_404(self, client):
        """Unknown mission_id must return 404."""
        response = client.get("/api/v1/map/layers/nonexistent-mission-xyz")
        assert response.status_code == 404

    def test_get_layers_contains_geojson_url(self, client):
        """Each layer must have a geojson_url pointing to the layer geojson endpoint."""
        response = client.get("/api/v1/map/layers/mars-2020")
        assert response.status_code == 200
        for layer in response.json():
            assert "geojson_url" in layer
            assert layer["geojson_url"].endswith(".geojson")

    def test_get_layer_geojson_positions(self, client):
        """Historical positions GeoJSON must be valid FeatureCollection."""
        response = client.get("/api/v1/map/layers/mars-2020/historical-positions.geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        # Confirm no EPSG:4326
        import json
        raw = json.dumps(data)
        assert "EPSG:4326" not in raw

    def test_get_layer_geojson_route(self, client):
        """Traversed route GeoJSON must be a valid FeatureCollection."""
        response = client.get("/api/v1/map/layers/mars-2020/traversed-route.geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data

    def test_get_layer_geojson_candidate_sites(self, client):
        """Candidate sites GeoJSON must have is_placeholder preserved."""
        response = client.get("/api/v1/map/layers/artemis-lunar/candidate-lunar-sites.geojson")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        for f in data["features"]:
            assert "is_placeholder" in f["properties"]
            assert "source_product_id" in f["properties"]

    def test_get_layer_geojson_unknown_layer_404(self, client):
        """Unknown layer for valid mission must return 404."""
        response = client.get("/api/v1/map/layers/mars-2020/not-a-layer.geojson")
        assert response.status_code == 404

    def test_get_layer_geojson_unknown_mission_404(self, client):
        """Unknown mission must return 404 on geojson endpoint."""
        response = client.get("/api/v1/map/layers/jupiter-not-exist/historical-positions.geojson")
        assert response.status_code == 404

    def test_layer_metadata_has_all_required_fields(self, client):
        """Layer metadata response must include all required schema fields."""
        response = client.get("/api/v1/map/layers/mars-2020")
        assert response.status_code == 200
        required_keys = {
            "id", "name", "type", "description", "geojson_url",
            "label", "source", "is_placeholder", "disclaimer",
        }
        for layer in response.json():
            assert required_keys.issubset(set(layer.keys()))

    def test_layer_positions_has_coordinate_ref_note(self, client):
        """Historical positions GeoJSON must have coordinate_reference_note at top level."""
        response = client.get("/api/v1/map/layers/mars-2020/historical-positions.geojson")
        assert response.status_code == 200
        data = response.json()
        note = data.get("coordinate_reference_note") or data.get("properties", {}).get("coordinate_reference_note")
        assert note is not None
        assert "EPSG" not in note

    def test_sol_minus1_in_positions_geojson(self, client):
        """Sol == -1 feature must have feature_role: landing_site_reference."""
        response = client.get("/api/v1/map/layers/mars-2020/historical-positions.geojson")
        assert response.status_code == 200
        data = response.json()
        # Must have at least one feature
        assert len(data["features"]) > 0
        # Check sol and feature_role present in all features
        for f in data["features"]:
            props = f["properties"]
            assert "feature_role" in props
            assert "source_product_id" in props
            if props.get("sol") == -1:
                assert props["feature_role"] == "landing_site_reference"
