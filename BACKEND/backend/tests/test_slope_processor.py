"""
Unit and integration tests for Phase B2:
  - SlopeProcessor flat plane -> slope = 0 deg
  - SlopeProcessor tilted plane -> known slope in degrees
  - Landing ellipse and circular mask statistics on synthetic grid
  - Morphologic metrics (local relief, RMS roughness, histogram, criteria)
  - API endpoints GET /api/v1/lunar/sites/{id}/terrain and /slope:
      * 200 OK for valid site
      * 404 for unknown site
      * 422 for site outside DEM coverage (lat north of -75°S)
      * Disclaimers, Derived label, and threshold criteria fields present
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from data_pipeline.processors.slope_processor import SlopeProcessor
from backend.app.services.dem_service import DEMService, SiteCoverageError
from backend.app.services.slope_service import SlopeService
from backend.app.services.lunar_site_service import LunarSiteService
from backend.app.models.models import CandidateLandingSite, TerrainProduct, TerrainMetrics


class TestSlopeProcessor:
    """Mathematical verification of Horn slope and morphology statistics."""

    def test_flat_plane_zero_slope(self):
        """A flat elevation grid of constant height must have 0° slope everywhere."""
        proc = SlopeProcessor(pixel_spacing_m=240.0)
        elev = np.full((20, 20), 500.0, dtype=np.float32)
        slope = proc.compute_slope_grid(elev)
        assert slope.shape == (20, 20)
        assert np.allclose(slope, 0.0, atol=1e-5), f"Max slope was {np.max(slope)}"

    def test_tilted_plane_known_slope(self):
        """
        Elevation increasing linearly in x (eastward) with known gradient dz/dx.
        Let dz/dx = 0.1 (10% gradient), dy = 0.
        Expected slope = arctan(0.1) * 180 / pi ≈ 5.71059 degrees.
        Interior pixels must match this slope exactly.
        """
        proc = SlopeProcessor(pixel_spacing_m=240.0)
        dx = 240.0
        gradient = 0.1
        # rows: y (0 to 19), cols: x (0 to 19)
        # z(x, y) = gradient * x * dx
        cols = np.arange(20, dtype=np.float64)
        elev = np.tile(gradient * cols * dx, (20, 1))

        slope = proc.compute_slope_grid(elev)
        expected_deg = math.degrees(math.atan(gradient))

        # Check interior (excluding outer border where padding applies)
        interior_slopes = slope[2:-2, 2:-2]
        assert np.allclose(interior_slopes, expected_deg, atol=1e-3), (
            f"Expected {expected_deg:.4f} deg, got mean={np.mean(interior_slopes):.4f}"
        )

    def test_tilted_plane_45_degree_slope(self):
        """
        Tilted plane with dz/dx = 1.0 (45° incline).
        Interior slope must be exactly 45.0 degrees.
        """
        proc = SlopeProcessor(pixel_spacing_m=240.0)
        cols = np.arange(20, dtype=np.float64)
        elev = np.tile(1.0 * cols * 240.0, (20, 1))

        slope = proc.compute_slope_grid(elev)
        interior = slope[2:-2, 2:-2]
        assert np.allclose(interior, 45.0, atol=1e-3)

    def test_ellipse_mask_and_circular_mask(self):
        """Verify ellipse mask generation inside known grid."""
        proc = SlopeProcessor(pixel_spacing_m=10.0)
        # 21x21 grid, center at (10, 10)
        # Circular mask with radius 50m (5 pixels)
        mask_circle = proc.get_ellipse_mask(
            grid_shape=(21, 21),
            center_row=10.0,
            center_col=10.0,
            analysis_radius_m=50.0,
        )
        assert mask_circle[10, 10] is True or mask_circle[10, 10] == 1
        # Corner (0, 0) is sqrt(10^2+10^2)*10 ≈ 141m > 50m -> False
        assert not mask_circle[0, 0]

        # Elliptical mask: semi_major 80m (8 px along x), semi_minor 20m (2 px along y)
        mask_ellipse = proc.get_ellipse_mask(
            grid_shape=(21, 21),
            center_row=10.0,
            center_col=10.0,
            semi_major_m=80.0,
            semi_minor_m=20.0,
            orientation_deg=0.0,
        )
        assert mask_ellipse[10, 10]
        # (10, 16) is dx=60m, dy=0 -> inside major axis (60 < 80)
        assert mask_ellipse[10, 16]
        # (15, 10) is dx=0, dy=50m -> outside minor axis (50 > 20)
        assert not mask_ellipse[15, 10]

    def test_terrain_statistics_on_known_grid(self):
        """Verify mean, max, percentiles, relief, roughness and criteria results."""
        proc = SlopeProcessor(pixel_spacing_m=10.0)
        # Simple 5x5 grid
        elev = np.array([
            [10.0, 20.0, 30.0, 40.0, 50.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
        ], dtype=np.float32)
        slope = np.array([
            [5.0, 10.0, 15.0, 20.0, 25.0],
            [5.0, 10.0, 15.0, 20.0, 25.0],
            [5.0, 10.0, 15.0, 20.0, 25.0],
            [5.0, 10.0, 15.0, 20.0, 25.0],
            [5.0, 10.0, 15.0, 20.0, 25.0],
        ], dtype=np.float32)
        mask = np.ones((5, 5), dtype=bool)

        stats = proc.compute_terrain_statistics(
            elev_grid=elev,
            slope_grid=slope,
            mask=mask,
            criteria={"slope_threshold_deg": 15.0},
        )

        assert stats["elevation"]["min_m"] == 10.0
        assert stats["elevation"]["max_m"] == 50.0
        assert stats["elevation"]["local_relief_m"] == 40.0
        assert stats["slope"]["mean_deg"] == 15.0
        assert stats["slope"]["min_deg"] == 5.0
        assert stats["slope"]["max_deg"] == 25.0
        assert stats["slope"]["p50_deg"] == 15.0
        # Criteria: values > 15.0 are 20.0 and 25.0 (10 pixels out of 25 -> 40%)
        assert stats["criteria_result"]["fraction_exceeding_threshold"] == 0.4
        assert "example threshold, not an official safety criterion" in stats["criteria_result"]["threshold_label"]
        assert "never labelled safe" in stats["criteria_result"]["site_safety_disclaimer"]


class TestTerrainEndpoints:
    """Test API endpoints /api/v1/lunar/sites/{id}/terrain and /slope."""

    @pytest.fixture(autouse=True)
    def setup_synthetic_test_env(self, monkeypatch):
        """
        Set up a synthetic 50x50 DEM in DEMService so tests run isolated without
        relying on external raw downloads.
        """
        from backend.app.database.session import SessionLocal

        N = 50
        # Synthetic DEM array centered on south pole
        elev = np.zeros((N, N), dtype=np.float32)
        # Add a depression at center (pole) and elevation outside
        r_idx, c_idx = np.ogrid[0:N, 0:N]
        dist = np.sqrt((r_idx - 25) ** 2 + (c_idx - 25) ** 2)
        elev = (dist * 50.0).astype(np.float32)

        synthetic_params = {
            "map_scale": 240.0,
            "lines": N,
            "line_samples": N,
            "center_latitude": -90.0,
            "sphere_radius_m": 1737400.0,
            "minimum_latitude": -90.0,
            "maximum_latitude": -75.0,
        }

        mock_dem_service = DEMService(
            dem_path="mock_path",
            label_params=synthetic_params,
            elev_array=elev,
        )
        mock_slope_service = SlopeService(
            dem_service=mock_dem_service,
            slope_processor=SlopeProcessor(pixel_spacing_m=240.0),
        )

        # Monkeypatch singletons
        import backend.app.services.dem_service as ds_mod
        import backend.app.services.slope_service as ss_mod
        monkeypatch.setattr(ds_mod, "get_dem_service", lambda: mock_dem_service)
        monkeypatch.setattr(ss_mod, "get_slope_service", lambda: mock_slope_service)

        db = SessionLocal()
        try:
            # Create candidate sites in temp DB
            site_in_bounds = CandidateLandingSite(
                id="test-south-site-01",
                name="Test South Polar Site",
                body_id="moon",
                coordinates={"values": [-89.9, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
                frame="MOON_ME_DE421",
                analysis_radius_m=500.0,
                semi_major_m=800.0,
                semi_minor_m=400.0,
                orientation_deg=45.0,
                criteria={"slope_threshold_deg": 12.0},
                is_placeholder=True,
            )
            site_out_of_bounds = CandidateLandingSite(
                id="test-north-site-02",
                name="Test Equatorial Site Out of Bounds",
                body_id="moon",
                coordinates={"values": [-60.0, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
                frame="MOON_ME_DE421",
                analysis_radius_m=500.0,
                is_placeholder=True,
            )
            prod = TerrainProduct(
                id="lola-dem-75s-240m",
                source_product_id="urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_75s_240m",
                resolution="240 m/pixel (240.0 m/pix, true at south pole)",
                vertical_reference="Reference sphere radius: 1737.4 km",
                coverage={"south_latitude": -90.0, "north_latitude": -75.0},
                version="V2.0",
                no_data_value=None,
                coordinate_reference_note="DSMAP_POLAR.CAT Polar Stereographic",
            )
            db.merge(site_in_bounds)
            db.merge(site_out_of_bounds)
            db.merge(prod)
            db.commit()
        finally:
            db.close()

    def test_terrain_endpoint_200(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/terrain returns 200 and required fields."""
        res = client.get("/api/v1/lunar/sites/test-south-site-01/terrain")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["site_id"] == "test-south-site-01"
        assert data["label"] == "Derived"
        assert data["product_id"] == "lola-dem-75s-240m"
        assert data["units"] == "m"
        assert "elevation" in data
        assert "min_m" in data["elevation"]
        assert "max_m" in data["elevation"]
        assert "mean_m" in data["elevation"]
        assert "local_relief_m" in data["elevation"]
        assert "roughness_rms_m" in data["elevation"]
        assert "disclaimer" in data
        assert "criteria_result" in data
        assert data["criteria_result"]["threshold_label"] == "example threshold, not an official safety criterion"

    def test_slope_endpoint_200(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/slope returns 200 and required slope statistics."""
        res = client.get("/api/v1/lunar/sites/test-south-site-01/slope")
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["site_id"] == "test-south-site-01"
        assert data["label"] == "Derived"
        assert data["units"] == "deg"
        assert "slope" in data
        assert "mean_deg" in data["slope"]
        assert "max_deg" in data["slope"]
        assert "p50_deg" in data["slope"]
        assert "p90_deg" in data["slope"]
        assert "p95_deg" in data["slope"]
        assert "histogram" in data["slope"]
        assert len(data["slope"]["histogram"]["counts"]) == 10
        assert "Horn" in data["slope"]["method"]
        assert data["slope"]["pixel_spacing_m"] == 240.0

    def test_terrain_endpoint_404_unknown_site(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/terrain returns 404 for unknown site."""
        res = client.get("/api/v1/lunar/sites/non-existent-site-999/terrain")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_slope_endpoint_404_unknown_site(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/slope returns 404 for unknown site."""
        res = client.get("/api/v1/lunar/sites/non-existent-site-999/slope")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_terrain_endpoint_422_outside_coverage(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/terrain returns 422 for site outside DEM (north of -75°S)."""
        res = client.get("/api/v1/lunar/sites/test-north-site-02/terrain")
        assert res.status_code == 422
        assert "outside dem coverage" in res.json()["detail"].lower()

    def test_slope_endpoint_422_outside_coverage(self, client: TestClient):
        """GET /api/v1/lunar/sites/{id}/slope returns 422 for site outside DEM (north of -75°S)."""
        res = client.get("/api/v1/lunar/sites/test-north-site-02/slope")
        assert res.status_code == 422
        assert "outside dem coverage" in res.json()["detail"].lower()
