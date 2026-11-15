"""
Unit and integration tests for Lunar Geometry Service (LL-11 to LL-13, LL-17, LL-18 / Phase B3a).
Tests:
  - Local East-North-Up frame conversion with hand-made unit vectors:
      * Straight up -> elevation = 90 deg
      * Due north on horizon -> azimuth = 0 deg, elevation = 0 deg
      * Due east on horizon -> azimuth = 90 deg, elevation = 0 deg
      * Due south on horizon -> azimuth = 180 deg, elevation = 0 deg
      * Due west on horizon -> azimuth = 270 deg, elevation = 0 deg
  - Window detection on synthetic series
  - HTTP 404 for unknown site
  - HTTP 422 for bad dates, days > 60, step_minutes < 5
  - HTTP 503 when SPICE kernels are absent
  - Kernel-based test that runs if kernels are present and skips cleanly if absent
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.services.lunar_geometry_service import (
    compute_local_enu_basis,
    vector_to_az_el,
    detect_windows,
    KernelManager,
)


class TestLocalFrameConversion:
    """Tests local ENU frame projections with exact geometric vectors."""

    def test_enu_basis_orthonormality(self):
        """East, North, and Up unit vectors must be orthogonal and normalized."""
        for lat in [-89.9, -85.0, 0.0, 45.0]:
            for lon in [0.0, 90.0, 180.0, 270.0]:
                e_hat, n_hat, u_hat = compute_local_enu_basis(lat, lon)
                # Norms
                assert math.isclose(np.linalg.norm(e_hat), 1.0, abs_tol=1e-10)
                assert math.isclose(np.linalg.norm(n_hat), 1.0, abs_tol=1e-10)
                assert math.isclose(np.linalg.norm(u_hat), 1.0, abs_tol=1e-10)
                # Dot products (orthogonality)
                assert math.isclose(np.dot(e_hat, n_hat), 0.0, abs_tol=1e-10)
                assert math.isclose(np.dot(e_hat, u_hat), 0.0, abs_tol=1e-10)
                assert math.isclose(np.dot(n_hat, u_hat), 0.0, abs_tol=1e-10)
                # Right-handed cross product: E x N = U
                cross_en = np.cross(e_hat, n_hat)
                assert np.allclose(cross_en, u_hat, atol=1e-10)

    def test_straight_up_vector_elevation_90(self):
        """A vector pointing straight up (+U) must have elevation = 90 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        vec_up = 1000.0 * u_hat
        az, el = vector_to_az_el(vec_up, e_hat, n_hat, u_hat)
        assert math.isclose(el, 90.0, abs_tol=1e-6)

    def test_due_north_horizon_azimuth_0(self):
        """A vector pointing due north on the horizon (+N) must have azimuth = 0 deg and elevation = 0 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        vec_north = 500.0 * n_hat
        az, el = vector_to_az_el(vec_north, e_hat, n_hat, u_hat)
        assert math.isclose(az, 0.0, abs_tol=1e-6)
        assert math.isclose(el, 0.0, abs_tol=1e-6)

    def test_due_east_horizon_azimuth_90(self):
        """A vector pointing due east on the horizon (+E) must have azimuth = 90 deg and elevation = 0 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        vec_east = 750.0 * e_hat
        az, el = vector_to_az_el(vec_east, e_hat, n_hat, u_hat)
        assert math.isclose(az, 90.0, abs_tol=1e-6)
        assert math.isclose(el, 0.0, abs_tol=1e-6)

    def test_due_south_horizon_azimuth_180(self):
        """A vector pointing due south on the horizon (-N) must have azimuth = 180 deg and elevation = 0 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        vec_south = -300.0 * n_hat
        az, el = vector_to_az_el(vec_south, e_hat, n_hat, u_hat)
        assert math.isclose(az, 180.0, abs_tol=1e-6)
        assert math.isclose(el, 0.0, abs_tol=1e-6)

    def test_due_west_horizon_azimuth_270(self):
        """A vector pointing due west on the horizon (-E) must have azimuth = 270 deg and elevation = 0 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        vec_west = -250.0 * e_hat
        az, el = vector_to_az_el(vec_west, e_hat, n_hat, u_hat)
        assert math.isclose(az, 270.0, abs_tol=1e-6)
        assert math.isclose(el, 0.0, abs_tol=1e-6)

    def test_45_deg_elevation_and_azimuth(self):
        """Vector pointing equal parts East and North, and equal Up must have az = 45 deg, el = 45 deg."""
        e_hat, n_hat, u_hat = compute_local_enu_basis(-89.9, 0.0)
        # horizontal vector at 45 deg azimuth has length 1: (E + N)/sqrt(2)
        # up component = 1 -> tan(elev) = 1/1 = 1 -> elev = 45 deg
        vec = (e_hat + n_hat) / math.sqrt(2.0) + u_hat
        az, el = vector_to_az_el(vec, e_hat, n_hat, u_hat)
        assert math.isclose(az, 45.0, abs_tol=1e-6)
        assert math.isclose(el, 45.0, abs_tol=1e-6)


class TestWindowDetection:
    """Unit tests for contiguous visibility window extraction."""

    def test_window_detection_synthetic(self):
        # 30-minute steps
        # True for 3 steps, False for 2 steps, True for 1 step
        series = [
            {"timestamp": "2026-12-01T00:00:00Z", "vis": True},
            {"timestamp": "2026-12-01T00:30:00Z", "vis": True},
            {"timestamp": "2026-12-01T01:00:00Z", "vis": True},
            {"timestamp": "2026-12-01T01:30:00Z", "vis": False},
            {"timestamp": "2026-12-01T02:00:00Z", "vis": False},
            {"timestamp": "2026-12-01T02:30:00Z", "vis": True},
        ]
        windows = detect_windows(series, "vis", step_minutes=30)
        assert len(windows) == 2
        # First window: 3 steps * 0.5h = 1.5h
        assert windows[0]["start"] == "2026-12-01T00:00:00Z"
        assert windows[0]["end"] == "2026-12-01T01:00:00Z"
        assert windows[0]["duration_hours"] == 1.5
        assert windows[0]["steps"] == 3

        # Second window: 1 step * 0.5h = 0.5h
        assert windows[1]["start"] == "2026-12-01T02:30:00Z"
        assert windows[1]["end"] == "2026-12-01T02:30:00Z"
        assert windows[1]["duration_hours"] == 0.5
        assert windows[1]["steps"] == 1

    def test_window_detection_all_false(self):
        series = [
            {"timestamp": "2026-12-01T00:00:00Z", "vis": False},
            {"timestamp": "2026-12-01T00:30:00Z", "vis": False},
        ]
        windows = detect_windows(series, "vis", step_minutes=30)
        assert windows == []

    def test_window_detection_all_true(self):
        series = [
            {"timestamp": "2026-12-01T00:00:00Z", "vis": True},
            {"timestamp": "2026-12-01T00:30:00Z", "vis": True},
        ]
        windows = detect_windows(series, "vis", step_minutes=30)
        assert len(windows) == 1
        assert windows[0]["duration_hours"] == 1.0


class TestGeometryEndpointsValidation:
    """Tests 404, 422, and 503 error handling."""

    def test_404_unknown_site(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/non-existent-site-999/geometry?start=2026-12-01")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_422_bad_start_date(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/geometry?start=invalid-date")
        assert res.status_code == 422
        assert "start date" in res.json()["detail"].lower()

    def test_422_days_exceeds_limit(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&days=90")
        assert res.status_code == 422

    def test_422_step_minutes_too_small(self, client: TestClient):
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&step_minutes=2")
        assert res.status_code == 422

    def test_503_when_kernels_missing(self, client: TestClient, monkeypatch):
        monkeypatch.setattr(KernelManager, "are_kernels_available", lambda: False)
        monkeypatch.setattr(KernelManager, "check_kernels", lambda: ["mock_missing.bsp"])
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01")
        assert res.status_code == 503
        assert "kernels missing" in res.json()["detail"].lower()

    def test_compare_404_unknown_site(self, client: TestClient):
        res = client.get("/api/v1/lunar/compare?site_ids=site-shackleton-01,fake-site-999&start=2026-12-01")
        assert res.status_code == 404


class TestKernelGeometryExecution:
    """Real SPICE kernel calculation test (skips cleanly if kernels are absent)."""

    @pytest.mark.skipif(
        not KernelManager.are_kernels_available(),
        reason="Required SPICE kernels not present on disk",
    )
    def test_site_geometry_200_with_real_kernels(self, client: TestClient):
        res = client.get(
            "/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&days=2&step_minutes=60"
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["site_id"] == "site-shackleton-01"
        assert data["frame"] == "MOON_ME_DE421"
        assert data["label"] == "Modelled"
        assert "SPICE geometric, flat horizon" in data["method"]
        assert len(data["series"]) == 48  # 2 days * 24 steps
        assert "totals" in data
        assert data["totals"]["total_simulation_hours"] == 48.0
        assert "sunlight_hours" in data["totals"]
        assert "earth_visible_hours" in data["totals"]
        assert "windows" in data
        assert "sunlight" in data["windows"]
        assert len(data["disclaimers"]) >= 4

    @pytest.mark.skipif(
        not KernelManager.are_kernels_available(),
        reason="Required SPICE kernels not present on disk",
    )
    def test_compare_endpoint_200_with_real_kernels(self, client: TestClient):
        res = client.get(
            "/api/v1/lunar/compare?site_ids=site-shackleton-01,site-connecting-ridge-02&start=2026-12-01&days=2&step_minutes=60"
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["label"] == "Modelled"
        assert data["frame"] == "MOON_ME_DE421"
        assert len(data["sites"]) == 2
        s1 = data["sites"][0]
        assert s1["site_id"] == "site-shackleton-01"
        assert s1["totals"]["total_simulation_hours"] == 48.0
