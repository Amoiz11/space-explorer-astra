"""
Tests for Phase B5b: Lunar MMGIS Layers and Geospatial Exports.
Covers layer metadata listing, GeoJSON validity, sidecars, coordinates checks, and 404 handling.
"""

import json
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.models import (
    CandidateLandingSite,
    TerrainMetrics,
    IlluminationResult,
    EarthVisibilityWindow,
)
from datetime import datetime, timezone

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def setup_test_lunar_data():
    """Ensure candidate sites and stored metrics exist in test DB."""
    db = SessionLocal()
    try:
        site = db.query(CandidateLandingSite).filter_by(id="site-shackleton-01").first()
        if not site:
            site = CandidateLandingSite(
                id="site-shackleton-01",
                body_id="moon",
                name="Shackleton Rim Candidate Area",
                coordinates={"values": [-89.9, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
                frame="MOON_ME_DE421",
                analysis_radius_m=1000.0,
                is_placeholder=True,
            )
            db.add(site)

        # Ensure at least one TerrainMetrics record
        tm = db.query(TerrainMetrics).filter_by(site_id="site-shackleton-01").first()
        if not tm:
            tm = TerrainMetrics(
                site_id="site-shackleton-01",
                product_id="lola-dem-75s-240m",
                mean_slope=21.54,
                max_slope=28.1,
                elevation_stats={"mean_m": 665.2, "local_relief_m": 689.5},
                method="Horn (1981)",
                is_placeholder=True,
            )
            db.add(tm)

        # Ensure at least one IlluminationResult record
        ir = db.query(IlluminationResult).filter_by(site_id="site-shackleton-01").first()
        if not ir:
            ir = IlluminationResult(
                site_id="site-shackleton-01",
                start_time=datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 12, 15, 0, 0, tzinfo=timezone.utc),
                sun_azimuth=45.0,
                sun_elevation=1.2,
                illuminated_fraction=1.0,
                method="SPICE + LOLA DEM",
                parameters={"start": "2026-12-01", "days": 30, "step_minutes": 30},
            )
            db.add(ir)

        # Ensure at least one EarthVisibilityWindow record
        ev = db.query(EarthVisibilityWindow).filter_by(site_id="site-shackleton-01").first()
        if not ev:
            ev = EarthVisibilityWindow(
                site_id="site-shackleton-01",
                start_time=datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 12, 14, 0, 0, tzinfo=timezone.utc),
                earth_azimuth=6.5,
                earth_elevation=0.8,
                obstruction_status="clear",
                parameters={"start": "2026-12-01", "days": 30, "step_minutes": 30},
            )
            db.add(ev)

        db.commit()
    finally:
        db.close()


class TestLunarLayerList:
    """Tests for GET /api/v1/map/layers/{mission_id} for lunar layers."""

    def test_layer_list_contains_new_layers(self):
        """Must return candidate_sites, illumination, earth_visibility, lunar_dem, lunar_slope."""
        resp = client.get("/api/v1/map/layers/moon")
        assert resp.status_code == 200
        layers = resp.json()
        layer_ids = [l["id"] for l in layers]

        expected_ids = ["candidate_sites", "illumination", "earth_visibility", "lunar_dem", "lunar_slope"]
        for eid in expected_ids:
            assert eid in layer_ids, f"Expected layer '{eid}' in layer list, got: {layer_ids}"

    def test_layer_types_and_fields(self):
        """Layers must have correct types, names, URLs, source products, labels, and disclaimers."""
        resp = client.get("/api/v1/map/layers/moon")
        assert resp.status_code == 200
        layers_by_id = {l["id"]: l for l in resp.json()}

        # Vector layers
        assert layers_by_id["candidate_sites"]["type"] == "vector"
        assert layers_by_id["illumination"]["type"] == "vector"
        assert layers_by_id["earth_visibility"]["type"] == "vector"

        # Raster layers
        assert layers_by_id["lunar_dem"]["type"] == "raster"
        assert layers_by_id["lunar_slope"]["type"] == "raster"

        for lid in ["candidate_sites", "illumination", "earth_visibility", "lunar_dem", "lunar_slope"]:
            l = layers_by_id[lid]
            assert l["name"]
            assert l["url"]
            assert l["source_product_id"]
            assert l["label"]
            assert l["disclaimer"]


class TestCandidateSitesGeoJSON:
    """Tests for candidate_sites GeoJSON validity and contents."""

    def test_candidate_sites_features(self):
        """Must contain Point per site plus Polygon for analysis radius or landing ellipse."""
        resp = client.get("/api/v1/map/layers/moon/candidate_sites.geojson")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/geo+json")
        fc = resp.json()
        assert fc["type"] == "FeatureCollection"
        features = fc["features"]
        assert len(features) >= 2  # At least 1 point + 1 polygon

        types = {f["geometry"]["type"] for f in features}
        assert "Point" in types
        assert "Polygon" in types

        # Check polygon is closed ring
        polygons = [f for f in features if f["geometry"]["type"] == "Polygon"]
        for p in polygons:
            ring = p["geometry"]["coordinates"][0]
            assert len(ring) >= 4
            assert ring[0] == ring[-1], "Polygon ring must be closed"

        # Check properties
        for f in features:
            props = f["properties"]
            assert "id" in props
            assert "name" in props
            assert "is_placeholder" in props
            assert props["coordinate_frame"] == "MOON_ME_DE421"


class TestLunarSummaryLayersGeoJSON:
    """Tests for illumination and earth_visibility summary GeoJSONs."""

    def test_illumination_geojson(self):
        resp = client.get("/api/v1/map/layers/moon/illumination.geojson")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) >= 1
        props = fc["features"][0]["properties"]
        assert "window_totals" in props
        assert "parameters" in props
        assert props["coordinate_frame"] == "MOON_ME_DE421"

    def test_earth_visibility_geojson(self):
        resp = client.get("/api/v1/map/layers/moon/earth_visibility.geojson")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["type"] == "FeatureCollection"
        assert len(fc["features"]) >= 1
        props = fc["features"][0]["properties"]
        assert "window_totals" in props
        assert "parameters" in props
        assert props["coordinate_frame"] == "MOON_ME_DE421"


class TestLunarRasterSidecarsAndPNGs:
    """Tests for lunar DEM and slope sidecar JSON and PNG endpoints."""

    def test_lunar_slope_sidecar_fields_present(self):
        """Sidecar must include bounds, projection matching DEM label, pixel_size, colour_scale, units."""
        resp = client.get("/api/v1/map/layers/moon/lunar_slope.json")
        assert resp.status_code == 200
        data = resp.json()

        assert "bounds" in data
        assert "projection" in data
        assert "pixel_size" in data
        assert "colour_scale" in data
        assert "units" in data

        # Projection matching DEM label
        proj = data["projection"]
        assert proj["map_projection_type"] == "POLAR STEREOGRAPHIC"
        assert proj["coordinate_system_name"] == "MEAN EARTH/POLAR AXIS OF DE421"
        assert proj["center_latitude"] == -90.0

        # Bounds
        bounds = data["bounds"]
        assert bounds["minimum_latitude_deg"] == -90.0
        assert bounds["maximum_latitude_deg"] == -75.0

        # Pixel size and colour scale
        assert "pixel_resolution_m" in data["pixel_size"]
        assert data["colour_scale"]["units"] == "degrees"

    def test_lunar_dem_sidecar_fields_present(self):
        resp = client.get("/api/v1/map/layers/moon/lunar_dem.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["projection"]["map_projection_type"] == "POLAR STEREOGRAPHIC"
        assert data["colour_scale"]["units"] == "meters"

    def test_lunar_raster_pngs_served(self):
        resp_dem = client.get("/api/v1/map/layers/moon/lunar_dem.png")
        assert resp_dem.status_code == 200
        assert resp_dem.headers["content-type"].startswith("image/png")

        resp_slope = client.get("/api/v1/map/layers/moon/lunar_slope.png")
        assert resp_slope.status_code == 200
        assert resp_slope.headers["content-type"].startswith("image/png")


class TestCoordinateSafety:
    """Moon coordinates must never be labelled as EPSG:4326."""

    def test_metadata_never_says_epsg4326(self):
        endpoints = [
            "/api/v1/map/layers/moon",
            "/api/v1/map/layers/moon/candidate_sites.geojson",
            "/api/v1/map/layers/moon/illumination.geojson",
            "/api/v1/map/layers/moon/earth_visibility.geojson",
            "/api/v1/map/layers/moon/lunar_dem.json",
            "/api/v1/map/layers/moon/lunar_slope.json",
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.status_code == 200, f"Endpoint {ep} failed with {resp.status_code}"
            text = resp.text
            assert "EPSG:4326" not in text, f"Found EPSG:4326 in {ep}"
            assert "epsg:4326" not in text.lower(), f"Found epsg:4326 in {ep}"


class TestUnknownLayer404:
    """Must return 404 for unknown layer."""

    def test_unknown_geojson_layer_404(self):
        resp = client.get("/api/v1/map/layers/moon/nonexistent_layer.geojson")
        assert resp.status_code == 404

    def test_unknown_raster_png_404(self):
        resp = client.get("/api/v1/map/layers/moon/nonexistent_layer.png")
        assert resp.status_code == 404

    def test_unknown_json_sidecar_404(self):
        resp = client.get("/api/v1/map/layers/moon/nonexistent_layer.json")
        assert resp.status_code == 404
