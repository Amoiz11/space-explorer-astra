"""
Unit and integration tests for HorizonProcessor and horizon endpoints (Phase B3b).
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from data_pipeline.processors.horizon_processor import HorizonProcessor, MOON_RADIUS_M, MAP_SCALE_M
from backend.app.services.horizon_service import HorizonService, get_horizon_service
from backend.app.services.dem_service import DEMService
from backend.app.models.models import CandidateLandingSite


class TestHorizonProcessorMath:
    """Mathematical tests for ray marching, curvature drop, and synthetic features."""

    def test_flat_plane_horizon_near_zero(self):
        """
        On an entirely flat DEM, the horizon angle at every azimuth must be near 0 degrees
        (only the slight negative spherical curvature dip, approx -0.01 to 0 deg).
        """
        N = 100
        elev = np.full((N, N), 1000.0, dtype=np.float32)
        proc = HorizonProcessor(moon_radius_m=MOON_RADIUS_M, map_scale_m=MAP_SCALE_M)

        result = proc.compute_horizon_profile(
            elev_array=elev,
            site_row=50.0,
            site_col=50.0,
            site_lon_deg=0.0,
            site_lat_deg=-89.9,
            azimuth_step_deg=10.0,
            max_distance_km=5.0,  # ~21 steps
            observer_height_m=0.0,
        )

        assert len(result["profile"]) == 36
        for pt in result["profile"]:
            el = pt["horizon_elevation_deg"]
            # Curvature drop over 240m is 240^2/(2*1.7374e6) = 0.016m -> el = -0.004 deg
            assert -0.2 <= el <= 0.05, f"Expected horizon near 0 deg, got {el}"
            assert not pt["cut_by_coverage"]

    def test_wall_at_known_distance_and_azimuth(self):
        """
        A flat DEM with a wall of known height h at known distance d due North (azimuth 0 deg).
        At azimuth 0, horizon elevation must be approximately atan(h / d) in degrees.
        At other azimuths, horizon elevation must remain near 0.
        """
        N = 200
        elev = np.zeros((N, N), dtype=np.float32)
        proc = HorizonProcessor(moon_radius_m=MOON_RADIUS_M, map_scale_m=MAP_SCALE_M)

        center_r, center_c = 100.0, 100.0
        # Place wall 10 pixels due North (delta_row = -10, delta_col = 0)
        # Distance d = 10 * 240 = 2400 m
        # Wall height h = 500 m
        wall_r = 90
        wall_c = 100
        elev[wall_r, wall_c] = 500.0

        # Expected angle: atan(h / d) with curvature correction
        d_m = 2400.0
        h_m = 500.0
        curv_drop = (d_m ** 2) / (2.0 * MOON_RADIUS_M)  # ~1.65 m
        expected_deg = math.degrees(math.atan((h_m - curv_drop) / d_m))

        result = proc.compute_horizon_profile(
            elev_array=elev,
            site_row=center_r,
            site_col=center_c,
            site_lon_deg=0.0,
            site_lat_deg=-89.9,
            azimuth_step_deg=5.0,
            max_distance_km=5.0,
            observer_height_m=0.0,
        )

        prof = {p["azimuth_deg"]: p["horizon_elevation_deg"] for p in result["profile"]}

        # Azimuth 0 (North) should capture the wall
        assert math.isclose(prof[0.0], expected_deg, abs_tol=0.2), (
            f"Expected ~{expected_deg:.2f} deg at az=0, got {prof[0.0]}"
        )

        # Distant azimuths (e.g. East 90, South 180, West 270) must have horizon near 0
        assert math.isclose(prof[90.0], 0.0, abs_tol=0.1)
        assert math.isclose(prof[180.0], 0.0, abs_tol=0.1)
        assert math.isclose(prof[270.0], 0.0, abs_tol=0.1)

    def test_coverage_edge_detection(self):
        """
        When rays march past the DEM boundary, they must terminate and flag cut_by_coverage=True.
        """
        N = 50
        elev = np.zeros((N, N), dtype=np.float32)
        proc = HorizonProcessor(moon_radius_m=MOON_RADIUS_M, map_scale_m=MAP_SCALE_M)

        # Place observer near top edge (row 3, col 25)
        # Ray pointing North (azimuth 0, delta_row < 0) will hit row < 0 after 4 steps!
        result = proc.compute_horizon_profile(
            elev_array=elev,
            site_row=3.0,
            site_col=25.0,
            site_lon_deg=0.0,
            site_lat_deg=-89.9,
            azimuth_step_deg=45.0,
            max_distance_km=10.0,  # ~41 steps
            observer_height_m=0.0,
        )

        prof_by_az = {p["azimuth_deg"]: p for p in result["profile"]}
        # Azimuth 0 points North -> must be cut short by grid boundary
        assert prof_by_az[0.0]["cut_by_coverage"] is True
        assert result["summary"]["cut_azimuth_count"] > 0
        assert 0.0 in result["cut_azimuths"]


class TestHorizonEndpoints:
    """Test API endpoints /api/v1/lunar/sites/{id}/horizon and geometry with include_horizon."""

    @pytest.fixture(autouse=True)
    def setup_sites(self):
        from backend.app.database.session import SessionLocal
        db = SessionLocal()
        try:
            site_north = CandidateLandingSite(
                id="test-north-site-02",
                name="Equatorial Test Site",
                body_id="moon",
                coordinates={"values": [-60.0, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
                frame="MOON_ME_DE421",
                analysis_radius_m=500.0,
                is_placeholder=True,
            )
            db.merge(site_north)
            db.commit()
        finally:
            db.close()

    def test_get_horizon_200(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/horizon?azimuth_step=5&max_distance_km=20")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["site_id"] == "site-shackleton-01"
        assert data["label"] == "Derived"
        assert data["product_id"] == "lola-dem-75s-240m"
        assert "Bilinear" in data["method"]
        assert len(data["profile"]) == 72  # 360 / 5
        assert "summary" in data
        assert "min_horizon_elevation_deg" in data["summary"]
        assert "max_horizon_elevation_deg" in data["summary"]
        assert "mean_horizon_elevation_deg" in data["summary"]
        assert "max_horizon_azimuth_deg" in data["summary"]
        assert len(data["disclaimers"]) >= 2

    def test_get_horizon_404_unknown_site(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/unknown-nonexistent-site/horizon")
        assert res.status_code == 404

    def test_get_horizon_422_bad_parameters(self, client: TestClient):
        # Bad azimuth_step (0)
        res1 = client.get("/api/v1/lunar/sites/site-shackleton-01/horizon?azimuth_step=0")
        assert res1.status_code == 422

        # Bad max_distance_km (negative)
        res2 = client.get("/api/v1/lunar/sites/site-shackleton-01/horizon?max_distance_km=-10")
        assert res2.status_code == 422

        # Bad observer_height_m (negative)
        res3 = client.get("/api/v1/lunar/sites/site-shackleton-01/horizon?observer_height_m=-5")
        assert res3.status_code == 422

    def test_get_horizon_422_outside_coverage(self, client: TestClient):
        # test-north-site-02 is at latitude -60° (north of 75°S boundary)
        res = client.get("/api/v1/lunar/sites/test-north-site-02/horizon")
        assert res.status_code == 422
        assert "outside dem coverage" in res.json()["detail"].lower()

    def test_geometry_with_include_horizon_true(self, client: TestClient):
        res = client.get(
            "/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&days=1&step_minutes=60&include_horizon=true"
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data["series"]) == 24
        pt0 = data["series"][0]
        assert "horizon_elevation_at_sun_azimuth" in pt0
        assert pt0["horizon_elevation_at_sun_azimuth"] is not None
        assert isinstance(pt0["horizon_elevation_at_sun_azimuth"], (int, float))
        assert "horizon_elevation_at_earth_azimuth" in pt0
        assert pt0["horizon_elevation_at_earth_azimuth"] is not None

        # Verify windows and totals are unchanged flat horizon metrics
        assert "totals" in data
        assert data["totals"]["total_simulation_hours"] == 24.0

    def test_geometry_with_include_horizon_false_default(self, client: TestClient):
        res = client.get(
            "/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&days=1&step_minutes=60"
        )
        assert res.status_code == 200, res.text
        data = res.json()
        pt0 = data["series"][0]
        assert pt0.get("horizon_elevation_at_sun_azimuth") is None
        assert pt0.get("horizon_elevation_at_earth_azimuth") is None
