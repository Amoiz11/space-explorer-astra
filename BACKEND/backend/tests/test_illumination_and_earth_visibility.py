"""
Tests for Phase B4a: Terrain-aware Illumination and Earth Visibility (LL-14 to LL-16, LL-19 to LL-22).
"""

import math
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.models import CandidateLandingSite
from backend.app.services.lunar_geometry_service import KernelManager
from data_pipeline.processors.illumination_processor import (
    compute_illuminated_fraction,
    compute_solar_angular_radius_deg,
    refine_continuous_windows,
    IlluminationProcessor,
)
from data_pipeline.processors.earth_visibility_processor import (
    determine_obstruction_status,
    compute_earth_angular_radius_deg,
    EarthVisibilityProcessor,
)


@pytest.fixture(autouse=True)
def ensure_test_sites():
    db = SessionLocal()
    try:
        # Ensure site-shackleton-01 exists in test DB
        site = db.query(CandidateLandingSite).filter_by(id="site-shackleton-01").first()
        if not site:
            site = CandidateLandingSite(
                id="site-shackleton-01",
                body_id="moon",
                name="Shackleton Rim Candidate Area",
                coordinates={"values": [-89.9, 0.0]},
                frame="MOON_ME_DE421",
                analysis_radius_m=2000.0,
                is_placeholder=True,
            )
            db.add(site)

        # Ensure out-of-coverage site exists for 422 testing
        north_site = db.query(CandidateLandingSite).filter_by(id="test-north-site-b4").first()
        if not north_site:
            north_site = CandidateLandingSite(
                id="test-north-site-b4",
                body_id="moon",
                name="North Test Site",
                coordinates={"values": [-60.0, 0.0]},
                frame="MOON_ME_DE421",
                analysis_radius_m=1000.0,
                is_placeholder=True,
            )
            db.add(north_site)
        db.commit()
    finally:
        db.close()


class TestIlluminationDiskGeometry:
    """Tests for synthetic circular segment disk illumination."""

    def test_disk_fraction_center_on_horizon(self):
        """When Sun center sits exactly on the horizon, fraction is ~0.5."""
        ang_rad = 0.26
        frac, status = compute_illuminated_fraction(
            sun_elevation_deg=5.0,
            horizon_elevation_deg=5.0,
            angular_radius_deg=ang_rad,
        )
        assert math.isclose(frac, 0.5, abs_tol=1e-4)
        assert status == "partial"

    def test_disk_fraction_well_above_and_below(self):
        """When Sun is well above horizon -> fraction 1 (lit); well below -> fraction 0 (shadow)."""
        ang_rad = 0.26
        # Above: delta_h = 1.0 > 0.26
        frac_lit, status_lit = compute_illuminated_fraction(
            sun_elevation_deg=6.0,
            horizon_elevation_deg=5.0,
            angular_radius_deg=ang_rad,
        )
        assert frac_lit == 1.0
        assert status_lit == "lit"

        # Below: delta_h = -1.0 < -0.26
        frac_shad, status_shad = compute_illuminated_fraction(
            sun_elevation_deg=4.0,
            horizon_elevation_deg=5.0,
            angular_radius_deg=ang_rad,
        )
        assert frac_shad == 0.0
        assert status_shad == "shadow"

    def test_disk_fraction_partial_segment(self):
        """Test intermediate partial fraction with circular segment geometry."""
        ang_rad = 0.25
        # At delta_h = 0.5 * ang_rad (x = 0.5), area above chord should be ~0.8045
        frac, status = compute_illuminated_fraction(
            sun_elevation_deg=5.125,
            horizon_elevation_deg=5.0,
            angular_radius_deg=ang_rad,
        )
        assert 0.80 < frac < 0.81
        assert status == "partial"


class TestSyntheticWindowsAndCrossings:
    """Tests for synthetic Sun crossing a 5° horizon and negative horizon handling."""

    def test_constant_5deg_horizon_crossing(self):
        """A constant 5 deg horizon with synthetic Sun path crossing it gives window start and end at crossing times."""
        timestamps = [
            "2026-12-01T00:00:00Z",  # t = 0 h, el = 4.0 (below 5)
            "2026-12-01T01:00:00Z",  # t = 1 h, el = 4.8 (below 5)
            "2026-12-01T02:00:00Z",  # t = 2 h, el = 5.6 (above 5)
            "2026-12-01T03:00:00Z",  # t = 3 h, el = 5.2 (above 5)
            "2026-12-01T04:00:00Z",  # t = 4 h, el = 4.4 (below 5)
        ]
        # Horizon = 5.0
        signals = [4.0 - 5.0, 4.8 - 5.0, 5.6 - 5.0, 5.2 - 5.0, 4.4 - 5.0]
        # Signals: [-1.0, -0.2, +0.6, +0.2, -0.6]
        # Rising crossing between step 1 (01:00, -0.2) and step 2 (02:00, +0.6):
        # frac = 0.2 / 0.8 = 0.25 -> 01:15:00
        # Falling crossing between step 3 (03:00, +0.2) and step 4 (04:00, -0.6):
        # frac = 0.2 / 0.8 = 0.25 -> 03:15:00
        windows = refine_continuous_windows(timestamps, signals, threshold=0.0)
        assert len(windows) == 1
        assert windows[0]["start"] == "2026-12-01T01:15:00Z"
        assert windows[0]["end"] == "2026-12-01T03:15:00Z"
        assert math.isclose(windows[0]["duration_hours"], 2.0, abs_tol=1e-3)

    def test_negative_horizon_handling(self):
        """Negative horizon site: Sun/Earth below 0 deg but above negative horizon is handled correctly."""
        h_horiz = -2.0  # dip horizon e.g. -2 deg
        ang_rad = 0.25

        # Sun at -1.0 deg: below 0 deg, but above -2 deg horizon
        frac, status = compute_illuminated_fraction(-1.0, h_horiz, ang_rad)
        assert frac == 1.0
        assert status == "lit"

        # Earth at -1.0 deg: below 0 deg, but above -2 deg horizon -> "clear"
        status_earth = determine_obstruction_status(-1.0, h_horiz)
        assert status_earth == "clear"


class TestObstructionStatusClassification:
    """Tests for Earth obstruction_status: 'clear', 'blocked_by_terrain', 'below_horizon'."""

    def test_obstruction_status_three_cases(self):
        # Case 1: Earth above terrain horizon -> "clear"
        assert determine_obstruction_status(effective_elevation_deg=4.0, horizon_elevation_deg=2.0) == "clear"

        # Case 2: Earth > 0 deg but below terrain horizon -> "blocked_by_terrain"
        assert determine_obstruction_status(effective_elevation_deg=2.0, horizon_elevation_deg=4.0) == "blocked_by_terrain"

        # Case 3: Earth <= 0 deg and below terrain horizon -> "below_horizon"
        assert determine_obstruction_status(effective_elevation_deg=-1.0, horizon_elevation_deg=0.0) == "below_horizon"


class TestIlluminationAndEarthEndpointsValidation:
    """Test 404 and 422 validations for both endpoints."""

    def test_404_unknown_site(self):
        client = TestClient(app)
        r1 = client.get("/api/v1/lunar/sites/non-existent-site-xyz/illumination?start=2026-12-01")
        assert r1.status_code == 404

        r2 = client.get("/api/v1/lunar/sites/non-existent-site-xyz/earth-visibility?start=2026-12-01")
        assert r2.status_code == 404

    def test_422_bad_parameters(self):
        client = TestClient(app)
        # Invalid earth_disk
        r = client.get("/api/v1/lunar/sites/site-shackleton-01/earth-visibility?start=2026-12-01&earth_disk=invalid")
        assert r.status_code == 422

        # Invalid days (> 60)
        r = client.get("/api/v1/lunar/sites/site-shackleton-01/illumination?start=2026-12-01&days=100")
        assert r.status_code == 422

        # Invalid step_minutes (< 5)
        r = client.get("/api/v1/lunar/sites/site-shackleton-01/illumination?start=2026-12-01&step_minutes=2")
        assert r.status_code == 422

        # Invalid start date
        r = client.get("/api/v1/lunar/sites/site-shackleton-01/illumination?start=not-a-date")
        assert r.status_code == 422

    def test_422_outside_coverage(self):
        client = TestClient(app)
        r1 = client.get("/api/v1/lunar/sites/test-north-site-b4/illumination?start=2026-12-01")
        assert r1.status_code == 422

        r2 = client.get("/api/v1/lunar/sites/test-north-site-b4/earth-visibility?start=2026-12-01")
        assert r2.status_code == 422


class TestKernelBasedIlluminationAndEarthVisibility:
    """Kernel-based test that skips cleanly if SPICE kernels are absent."""

    def test_real_kernels_illumination_and_visibility(self):
        if not KernelManager.are_kernels_available():
            pytest.skip("SPICE kernels not available in storage/kernels/")

        client = TestClient(app)
        # Test illumination
        resp_illum = client.get(
            "/api/v1/lunar/sites/site-shackleton-01/illumination?start=2026-12-01&days=2&step_minutes=60&observer_height_m=0"
        )
        assert resp_illum.status_code == 200, resp_illum.text
        data_i = resp_illum.json()
        assert data_i["site_id"] == "site-shackleton-01"
        assert data_i["label"] == "Modelled"
        assert data_i["frame"] == "MOON_ME_DE421"
        assert data_i["product_id"] == "lola-dem-75s-240m"
        assert "series" in data_i
        assert "windows" in data_i
        assert "totals" in data_i
        assert len(data_i["series"]) == 48  # 2 days * 24 steps
        assert "hours_any_part_lit" in data_i["totals"]
        assert "hours_fully_lit" in data_i["totals"]
        assert "hours_shadow" in data_i["totals"]

        # Test earth visibility
        resp_earth = client.get(
            "/api/v1/lunar/sites/site-shackleton-01/earth-visibility?start=2026-12-01&days=2&step_minutes=60&earth_disk=center"
        )
        assert resp_earth.status_code == 200
        data_e = resp_earth.json()
        assert data_e["site_id"] == "site-shackleton-01"
        assert data_e["earth_disk_criterion"] == "center"
        assert data_e["relay_communication"] == "not modelled"
        assert "series" in data_e
        assert "windows" in data_e
        assert "totals" in data_e
        assert "earth_visible_hours" in data_e["totals"]
        assert "blocked_by_terrain_hours" in data_e["totals"]


class TestConcurrentSpiceRequests:
    """Several threads hitting /illumination and /earth-visibility concurrently must all return 200."""

    def test_concurrent_illumination_and_earth_visibility(self):
        import threading

        if not KernelManager.are_kernels_available():
            pytest.skip("SPICE kernels not present — skipping concurrency test")

        client = TestClient(app)
        results = []
        lock = threading.Lock()

        def call_illumination():
            r = client.get(
                "/api/v1/lunar/sites/site-shackleton-01/illumination"
                "?start=2026-12-25&days=1&step_minutes=60&observer_height_m=0"
            )
            with lock:
                results.append(("illumination", r.status_code, len(r.json().get("series", []))))

        def call_earth():
            r = client.get(
                "/api/v1/lunar/sites/site-shackleton-01/earth-visibility"
                "?start=2026-12-25&days=1&step_minutes=60&observer_height_m=0&earth_disk=center"
            )
            with lock:
                results.append(("earth", r.status_code, len(r.json().get("series", []))))

        threads = [
            threading.Thread(target=call_illumination if i % 2 == 0 else call_earth)
            for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        failures = [r for r in results if r[1] != 200]
        empty = [r for r in results if r[2] == 0]
        assert not failures, f"Non-200 responses: {failures}"
        assert not empty, f"Empty series in responses: {empty}"
