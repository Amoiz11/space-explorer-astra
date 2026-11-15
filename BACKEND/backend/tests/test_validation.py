"""
Validation and Reproducibility Tests (SRS Section 31 / Phase B6b).

1. Independent cross-check of topocentric Sun and Earth elevation against SPICE ilumin.
2. Reproducibility test across all lunar endpoints (/geometry, /illumination, /earth-visibility, /solar-estimate, /compare).
"""

import math
import pytest
import numpy as np
from datetime import datetime

try:
    import spiceypy as spice
    SPICE_AVAILABLE = True
except ImportError:
    SPICE_AVAILABLE = False

from backend.app.services.lunar_geometry_service import (
    LunarGeometryService,
    KernelManager,
    FRAME_NAME,
    MOON_RADIUS_KM,
    compute_local_enu_basis,
    vector_to_az_el,
)
from backend.app.database.session import SessionLocal
from backend.app.models.models import CandidateLandingSite, IlluminationResult


@pytest.fixture(scope="module")
def require_kernels():
    """Skip test if SPICE or required kernels are absent."""
    if not SPICE_AVAILABLE or len(KernelManager.check_kernels()) > 0:
        pytest.skip("SPICE or required SPICE kernels not present on disk.")
    KernelManager.load_kernels()


def test_independent_sun_and_earth_elevation_cross_check_ilumin(require_kernels):
    """
    Independent cross-check of Sun and Earth elevation:
    For site-shackleton-01 (-89.9, 0.0) and points (-85.0, 0.0) and (-89.9, 90.0),
    at 20 evenly spaced times across December 2026,
    compare lunar_geometry_service elevations with spice.ilumin on the surface point
    (same frame MOON_ME_DE421, same sphere radius 1737.4 km, abcorr LT+S)
    where sun_elevation = 90 - solar incidence angle,
    and earth_elevation = 90 - emission angle.
    Verify maximum difference is strictly under 0.05 degrees.
    """
    et_start = spice.str2et("2026-12-01T00:00:00")
    et_end = spice.str2et("2026-12-31T00:00:00")
    ets = np.linspace(et_start, et_end, 20)

    test_points = [
        ("site-shackleton-01", -89.9, 0.0, 624.6),
        ("point-(-85, 0)", -85.0, 0.0, 0.0),
        ("point-(-89.9, 90)", -89.9, 90.0, 0.0),
    ]

    r_sphere_km = MOON_RADIUS_KM

    all_sun_diffs = []
    all_earth_diffs = []

    for name, lat_deg, lon_deg, elev_m in test_points:
        e_hat, n_hat, u_hat = compute_local_enu_basis(lat_deg, lon_deg)
        r_obs_km = MOON_RADIUS_KM + (elev_m / 1000.0)
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        p_obs = np.array([
            r_obs_km * math.cos(lat_rad) * math.cos(lon_rad),
            r_obs_km * math.cos(lat_rad) * math.sin(lon_rad),
            r_obs_km * math.sin(lat_rad),
        ], dtype=np.float64)

        # Surface point on sphere for ilumin
        spoint = np.array([
            r_sphere_km * math.cos(lat_rad) * math.cos(lon_rad),
            r_sphere_km * math.cos(lat_rad) * math.sin(lon_rad),
            r_sphere_km * math.sin(lat_rad),
        ], dtype=np.float64)

        for et in ets:
            # 1. lunar_geometry_service method
            p_sun, _ = spice.spkpos("SUN", et, FRAME_NAME, "LT+S", "MOON")
            v_sun = np.array(p_sun, dtype=np.float64) - p_obs
            _, sun_el_svc = vector_to_az_el(v_sun, e_hat, n_hat, u_hat)

            p_earth, _ = spice.spkpos("EARTH", et, FRAME_NAME, "LT+S", "MOON")
            v_earth = np.array(p_earth, dtype=np.float64) - p_obs
            _, earth_el_svc = vector_to_az_el(v_earth, e_hat, n_hat, u_hat)

            # 2. Independent spice.ilumin method
            trgepc, srfvec, phase, solar, emissn = spice.ilumin(
                "Ellipsoid", "MOON", et, FRAME_NAME, "LT+S", "EARTH", spoint
            )
            sun_el_ilumin = 90.0 - math.degrees(solar)
            earth_el_ilumin = 90.0 - math.degrees(emissn)

            diff_sun = abs(sun_el_svc - sun_el_ilumin)
            diff_earth = abs(earth_el_svc - earth_el_ilumin)

            all_sun_diffs.append(diff_sun)
            all_earth_diffs.append(diff_earth)

            # Strict threshold check (< 0.05 deg)
            assert diff_sun < 0.05, f"Sun elevation diff {diff_sun:.6f}° exceeded 0.05° at {name}, et={et}"
            assert diff_earth < 0.05, f"Earth elevation diff {diff_earth:.6f}° exceeded 0.05° at {name}, et={et}"

    max_sun_diff = max(all_sun_diffs)
    max_earth_diff = max(all_earth_diffs)

    # Documented results: max differences are both under 0.001 deg
    assert max_sun_diff < 0.01
    assert max_earth_diff < 0.01


def test_reproducibility_identical_results_across_calls(client):
    """
    Verify that submitting the identical request twice returns identical results
    for /geometry, /illumination, /earth-visibility, /solar-estimate, and /compare.
    """
    # 1. /geometry
    geom_url = "/api/v1/lunar/sites/site-shackleton-01/geometry?start=2026-12-01&days=2&step_minutes=60"
    r1 = client.get(geom_url)
    r2 = client.get(geom_url)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    # 2. /illumination
    illum_url = "/api/v1/lunar/sites/site-shackleton-01/illumination?start=2026-12-01&days=2&step_minutes=60"
    r1 = client.get(illum_url)
    r2 = client.get(illum_url)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    # 3. /earth-visibility
    ev_url = "/api/v1/lunar/sites/site-shackleton-01/earth-visibility?start=2026-12-01&days=2&step_minutes=60"
    r1 = client.get(ev_url)
    r2 = client.get(ev_url)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    # 4. /solar-estimate
    solar_body = {
        "start": "2026-12-01",
        "days": 2,
        "step_minutes": 60,
        "panel_area_m2": 2.0,
        "efficiency": 0.2,
        "tilt_deg": 45.0,
        "panel_azimuth_deg": 180.0,
        "track_sun_azimuth": False,
        "solar_constant_w_m2": 1361.0,
    }
    r1 = client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=solar_body)
    r2 = client.post("/api/v1/lunar/sites/site-shackleton-01/solar-estimate", json=solar_body)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    # 5. GET /compare (flat-horizon compare)
    cmp_get_url = "/api/v1/lunar/compare?site_ids=site-shackleton-01&site_ids=site-connecting-ridge-02&start=2026-12-01&days=2&step_minutes=60"
    r1 = client.get(cmp_get_url)
    r2 = client.get(cmp_get_url)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()

    # 6. POST /compare (terrain-aware compare)
    cmp_body = {
        "site_ids": ["site-shackleton-01", "site-connecting-ridge-02"],
        "windows": [
            {"start": "2026-12-01", "days": 2},
            {"start": "2027-01-01", "days": 2},
        ],
        "step_minutes": 60,
    }
    r1 = client.post("/api/v1/lunar/compare", json=cmp_body)
    r2 = client.post("/api/v1/lunar/compare", json=cmp_body)
    assert r1.status_code == 200 and r2.status_code == 200

    j1 = r1.json()
    j2 = r2.json()
    # POST /compare inserts an auditable database comparison record with an autoincrement ID;
    # verify that all scientific calculations, rows, best_by, and criteria results are 100% identical.
    del j1["id"]
    del j2["id"]
    assert j1 == j2
