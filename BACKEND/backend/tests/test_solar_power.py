"""
Tests for Phase B4b: Solar Power and Energy Estimation (LL-23 to LL-26).
"""

import math
import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.models import CandidateLandingSite
from backend.app.services.lunar_geometry_service import KernelManager
from backend.app.services.solar_power_service import (
    compute_incidence_cos,
    calculate_panel_normal_enu,
    calculate_sun_vector_enu,
    AU_KM,
    DEFAULT_SOLAR_CONSTANT_W_M2,
)


@pytest.fixture(autouse=True)
def ensure_test_sites():
    db = SessionLocal()
    try:
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

        north_site = db.query(CandidateLandingSite).filter_by(id="test-north-site-b4b").first()
        if not north_site:
            north_site = CandidateLandingSite(
                id="test-north-site-b4b",
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


class TestSolarGeometrySynthetic:
    """Synthetic unit tests for panel incidence angles, irradiance, and energy equations."""

    def test_panel_facing_sun_directly(self):
        """
        A panel facing the Sun directly (Sun el 30 deg, az 45 deg, panel tilt 60 deg, panel az 45 deg)
        has cos(theta_inc) = 1.0. With illuminated_fraction = 1, irradiance = solar_constant * 1.0.
        Energy over 2 hours = 1361 W/m^2 * area * efficiency * 2 h.
        """
        # beta = 60 deg tilt, h = 30 deg elevation -> beta + h = 90 deg (normal directly faces sun)
        cos_inc = compute_incidence_cos(
            sun_az_deg=45.0,
            sun_el_deg=30.0,
            tilt_deg=60.0,
            panel_az_deg=45.0,
            track_sun_azimuth=False,
        )
        assert math.isclose(cos_inc, 1.0, abs_tol=1e-6)

        area = 2.0  # m^2
        efficiency = 0.20
        hours = 2.0
        power_w = DEFAULT_SOLAR_CONSTANT_W_M2 * 1.0 * cos_inc * 1.0 * area * efficiency
        energy_wh = power_w * hours
        expected_energy_wh = DEFAULT_SOLAR_CONSTANT_W_M2 * area * efficiency * hours
        assert math.isclose(energy_wh, expected_energy_wh, abs_tol=1e-3)
        assert math.isclose(energy_wh, 1361.0 * 2.0 * 0.20 * 2.0, abs_tol=1e-3)

    def test_horizontal_panel_sun_at_1deg(self):
        """
        A horizontal panel (tilt = 0) with Sun at 1 degree elevation gives about sin(1 degree)
        of the direct normal irradiance.
        """
        cos_inc = compute_incidence_cos(
            sun_az_deg=180.0,
            sun_el_deg=1.0,
            tilt_deg=0.0,
            panel_az_deg=0.0,
            track_sun_azimuth=False,
        )
        expected_cos = math.sin(math.radians(1.0))
        assert math.isclose(cos_inc, expected_cos, abs_tol=1e-6)
        assert 0.0174 < cos_inc < 0.0175

    def test_zero_energy_during_shadow(self):
        """Illuminated fraction = 0 results in zero irradiance and zero energy regardless of angle."""
        cos_inc = compute_incidence_cos(
            sun_az_deg=90.0,
            sun_el_deg=45.0,
            tilt_deg=45.0,
            panel_az_deg=90.0,
            track_sun_azimuth=True,
        )
        frac_lit = 0.0
        irradiance = DEFAULT_SOLAR_CONSTANT_W_M2 * cos_inc * frac_lit
        power_w = irradiance * 1.5 * 0.25
        assert power_w == 0.0

    def test_backside_illumination_cutoff(self):
        """Sun behind the panel gives cos(theta) = 0 (no negative generation)."""
        # Panel facing North (az = 0), Sun from South (az = 180), vertical tilt (90)
        cos_inc = compute_incidence_cos(
            sun_az_deg=180.0,
            sun_el_deg=10.0,
            tilt_deg=90.0,
            panel_az_deg=0.0,
            track_sun_azimuth=False,
        )
        assert cos_inc == 0.0


class TestSolarEstimateEndpointsValidation:
    """Integration tests for validation, missing panel input, 404, and 422."""

    def test_missing_panel_returns_illumination_opportunity_only(self):
        """If NO panel inputs are given, return only illumination opportunity and message (LL-26)."""
        client = TestClient(app)
        payload = {
            "start": "2026-12-01",
            "days": 2,
            "step_minutes": 60,
        }
        resp = client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=payload)
        if resp.status_code == 503:
            pytest.skip("SPICE kernels not available")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["energy_wh"] is None
        assert data["energy_kwh"] is None
        assert data["mean_power_w"] is None
        assert data["peak_power_w"] is None
        assert data["per_day_energy"] == []
        assert "illumination_opportunity" in data
        assert "hours_any_part_lit" in data["illumination_opportunity"]
        assert "fraction_of_period" in data["illumination_opportunity"]
        assert "shadow_periods" in data
        assert "Panel inputs (area, efficiency, tilt) are required" in data["message"]

    def test_404_unknown_site(self):
        client = TestClient(app)
        resp = client.post("/api/v1/lunar/sites/non-existent-site-xyz/solar-estimate", json={"start": "2026-12-01"})
        assert resp.status_code == 404

    def test_422_bad_parameters(self):
        client = TestClient(app)
        # Invalid panel area (<= 0)
        p1 = {"start": "2026-12-01", "panel": {"panel_area_m2": 0.0, "efficiency": 0.2}}
        assert client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=p1).status_code == 422

        # Invalid efficiency (> 1)
        p2 = {"start": "2026-12-01", "panel": {"panel_area_m2": 1.0, "efficiency": 1.5}}
        assert client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=p2).status_code == 422

        # Invalid days (> 60)
        p3 = {"start": "2026-12-01", "days": 100}
        assert client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=p3).status_code == 422

        # Invalid step_minutes (< 5)
        p4 = {"start": "2026-12-01", "step_minutes": 2}
        assert client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=p4).status_code == 422

        # Invalid date
        p5 = {"start": "invalid-date"}
        assert client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=p5).status_code == 422

    def test_422_outside_coverage(self):
        client = TestClient(app)
        payload = {"start": "2026-12-01", "days": 1, "step_minutes": 60}
        resp = client.post("/api/v1/lunar/sites/test-north-site-b4b/solar-estimate", json=payload)
        assert resp.status_code == 422


class TestKernelBasedSolarEstimate:
    """Integration test with real SPICE kernels."""

    def test_real_kernels_solar_estimate(self):
        if not KernelManager.are_kernels_available():
            pytest.skip("SPICE kernels not available in storage/kernels/")

        client = TestClient(app)
        payload = {
            "start": "2026-12-01",
            "days": 2,
            "step_minutes": 60,
            "observer_height_m": 0.0,
            "panel": {
                "panel_area_m2": 1.0,
                "efficiency": 0.25,
                "tilt_deg": 90.0,
                "panel_azimuth_deg": 0.0,
                "track_sun_azimuth": True,
            },
        }
        resp = client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["site_id"] == "site-shackleton-01"
        assert data["label"] == "Modelled"
        assert data["energy_wh"] is not None
        assert data["energy_kwh"] is not None
        assert data["mean_power_w"] is not None
        assert data["peak_power_w"] is not None
        assert len(data["per_day_energy"]) == 2
        assert "assumptions" in data
        assert len(data["assumptions"]) >= 5
        assert "uncertainty" in data
        assert "disclaimers" in data
        assert data["sun_distance_au_factor"] is not None
