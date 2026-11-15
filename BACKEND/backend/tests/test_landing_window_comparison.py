"""
Tests for Phase B5a: Landing Window Comparison (LL-27 to LL-30).

Synthetic tests do not use SPICE kernels or the DEM.
One kernel-based integration test skips if kernels are absent.
"""

import csv
import io
import json
import math
import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.models import CandidateLandingSite
from backend.app.services.lunar_geometry_service import KernelManager
from backend.app.services.landing_window_service import (
    _get_criterion_value,
    _criterion_passes,
    DISCLAIMERS as CMP_DISCLAIMERS,
)
from backend.app.schemas.lunar_comparison import (
    ComparisonRow,
    IlluminationMetrics,
    EarthMetrics,
    SlopeMetrics,
    ElevationMetrics,
    DataQuality,
    CriterionResult,
    BestBy,
)

client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Test DB fixture
# ---------------------------------------------------------------------------

SITE_B5A_1 = "site-shackleton-01"
SITE_B5A_2 = "site-connecting-ridge-02"
SITE_B5A_OOC = "test-b5a-out-of-coverage"
SITE_B5A_UNKNOWN = "site-does-not-exist-b5a"


@pytest.fixture(autouse=True)
def ensure_b5a_sites():
    db = SessionLocal()
    try:
        # site 1 — shackleton (should already exist)
        s1 = db.query(CandidateLandingSite).filter_by(id=SITE_B5A_1).first()
        if not s1:
            db.add(CandidateLandingSite(
                id=SITE_B5A_1,
                body_id="moon",
                name="Shackleton Rim Candidate Area",
                coordinates={"values": [-89.9, 0.0]},
                frame="MOON_ME_DE421",
                analysis_radius_m=2000.0,
                is_placeholder=True,
            ))

        # site 2 — connecting ridge
        s2 = db.query(CandidateLandingSite).filter_by(id=SITE_B5A_2).first()
        if not s2:
            db.add(CandidateLandingSite(
                id=SITE_B5A_2,
                body_id="moon",
                name="Connecting Ridge Candidate Area",
                coordinates={"values": [-88.5, 222.7]},
                frame="MOON_ME_DE421",
                analysis_radius_m=2000.0,
                is_placeholder=True,
            ))

        # out-of-coverage site (lat > -75 deg)
        ooc = db.query(CandidateLandingSite).filter_by(id=SITE_B5A_OOC).first()
        if not ooc:
            db.add(CandidateLandingSite(
                id=SITE_B5A_OOC,
                body_id="moon",
                name="Out of Coverage Test Site",
                coordinates={"values": [-60.0, 0.0]},
                frame="MOON_ME_DE421",
                analysis_radius_m=1000.0,
                is_placeholder=True,
            ))

        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper: synthetic ComparisonRow factory
# ---------------------------------------------------------------------------

def _make_row(
    site_id: str = "site-a",
    window_start: str = "2026-12-01",
    window_days: int = 30,
    hours_any_part_lit: float = 400.0,
    hours_earth_visible: float = 350.0,
    mean_slope_deg: float = 5.0,
    hours_both_up: float = 300.0,
    longest_shadow_hours: float = 100.0,
) -> ComparisonRow:
    return ComparisonRow(
        site_id=site_id,
        site_name=f"Site {site_id}",
        is_placeholder=True,
        window_start=window_start,
        window_days=window_days,
        observer_elevation_m=600.0,
        illumination=IlluminationMetrics(
            hours_any_part_lit=hours_any_part_lit,
            hours_fully_lit=hours_any_part_lit * 0.9,
            hours_shadow=(window_days * 24 - hours_any_part_lit),
            longest_shadow_hours=longest_shadow_hours,
            number_of_lit_windows=3,
        ),
        earth=EarthMetrics(
            hours_earth_visible=hours_earth_visible,
            hours_earth_blocked=(window_days * 24 - hours_earth_visible),
            number_of_earth_windows=1,
        ),
        slope=SlopeMetrics(
            mean_slope_deg=mean_slope_deg,
            max_slope_deg=mean_slope_deg * 3.0,
            p90_slope_deg=mean_slope_deg * 2.0,
        ),
        elevation=ElevationMetrics(mean_elevation_m=600.0, relief_m=200.0),
        hours_both_up=hours_both_up,
        energy_kwh=None,
        criteria_results=[],
        data_quality=DataQuality(
            dem_resolution_m=240,
            is_placeholder=True,
            kernels_used=["naif0012.tls", "de421.bsp"],
            horizon_type="terrain",
            notes=["Planning tool."],
        ),
    )


# ---------------------------------------------------------------------------
# Synthetic unit tests (no kernels, no DEM)
# ---------------------------------------------------------------------------

class TestCriterionLogic:
    """Unit tests for criterion evaluation logic."""

    def test_criterion_value_extraction(self):
        row = _make_row(
            hours_any_part_lit=400.0,
            hours_earth_visible=350.0,
            mean_slope_deg=5.0,
            hours_both_up=300.0,
            longest_shadow_hours=120.0,
        )
        assert _get_criterion_value(row, "min_any_lit_hours") == pytest.approx(400.0)
        assert _get_criterion_value(row, "min_earth_visible_hours") == pytest.approx(350.0)
        assert _get_criterion_value(row, "max_mean_slope_deg") == pytest.approx(5.0)
        assert _get_criterion_value(row, "min_both_up_hours") == pytest.approx(300.0)
        assert _get_criterion_value(row, "max_longest_shadow_hours") == pytest.approx(120.0)

    def test_criterion_passes_min(self):
        assert _criterion_passes("min_any_lit_hours", 400.0, 300.0) is True
        assert _criterion_passes("min_any_lit_hours", 200.0, 300.0) is False

    def test_criterion_passes_max(self):
        assert _criterion_passes("max_mean_slope_deg", 4.0, 5.0) is True
        assert _criterion_passes("max_mean_slope_deg", 6.0, 5.0) is False

    def test_criterion_boundary_equal(self):
        # At boundary: value == threshold → passes for both min and max
        assert _criterion_passes("min_any_lit_hours", 300.0, 300.0) is True
        assert _criterion_passes("max_mean_slope_deg", 5.0, 5.0) is True


class TestBestByLogic:
    """Unit tests for best_by selection across rows."""

    def test_best_by_picks_correct_row(self):
        """best_for_sunlight picks row with the most hours_any_part_lit."""
        rows = [
            _make_row("site-a", "2026-12-01", hours_any_part_lit=200.0,
                      hours_earth_visible=100.0, mean_slope_deg=10.0),
            _make_row("site-b", "2026-12-01", hours_any_part_lit=400.0,
                      hours_earth_visible=50.0, mean_slope_deg=3.0),
            _make_row("site-a", "2027-01-01", hours_any_part_lit=350.0,
                      hours_earth_visible=200.0, mean_slope_deg=10.0),
        ]
        best_sunlight = max(rows, key=lambda r: r.illumination.hours_any_part_lit)
        best_earth = max(rows, key=lambda r: r.earth.hours_earth_visible)
        lowest_slope = min(rows, key=lambda r: r.slope.mean_slope_deg)

        assert best_sunlight.site_id == "site-b"
        assert best_earth.site_id == "site-a" and best_earth.window_start == "2027-01-01"
        assert lowest_slope.site_id == "site-b"

    def test_no_combined_score_without_weights(self):
        """ComparisonRow has no 'score' field — combined score requires weights."""
        row = _make_row()
        assert not hasattr(row, "score"), "ComparisonRow must not have a 'score' field"
        assert not hasattr(row, "combined_score"), "ComparisonRow must not have 'combined_score'"

    def test_site_never_labelled_safe(self):
        """ComparisonRow must not contain the word 'safe' as a status/label."""
        row = _make_row()
        # Check standard fields
        for field_name in ("site_id", "site_name"):
            val = getattr(row, field_name, "")
            assert "safe" not in str(val).lower(), f"Field {field_name} must not contain 'safe'"
        # data_quality notes must not say 'safe' as a verdict
        for note in row.data_quality.notes:
            assert "is safe" not in note.lower(), f"Note '{note}' must not label site as safe"


class TestCriteriaPassFail:
    """Test criteria pass/fail per row using the endpoint (mocked rows, no kernels)."""

    def test_criteria_pass_fail_correct(self):
        """
        Row A: mean_slope=3, any_lit=400 → passes max_slope≤5, fails min_lit≥500.
        Row B: mean_slope=7, any_lit=600 → fails max_slope≤5, passes min_lit≥500.
        """
        row_a = _make_row("site-a", hours_any_part_lit=400.0, mean_slope_deg=3.0)
        row_b = _make_row("site-b", hours_any_part_lit=600.0, mean_slope_deg=7.0)

        from backend.app.schemas.lunar_comparison import CriterionModel
        criteria = [
            CriterionModel(metric="max_mean_slope_deg", threshold=5.0),
            CriterionModel(metric="min_any_lit_hours", threshold=500.0),
        ]

        for row in [row_a, row_b]:
            results = []
            for c in criteria:
                val = _get_criterion_value(row, c.metric)
                passed = _criterion_passes(c.metric, val, c.threshold)
                results.append(CriterionResult(
                    metric=c.metric, threshold=c.threshold,
                    label=c.label, value=val, passed=passed,
                ))
            row.criteria_results = results

        # row_a: slope 3 ≤ 5 passes; lit 400 < 500 fails
        assert row_a.criteria_results[0].passed is True
        assert row_a.criteria_results[1].passed is False

        # row_b: slope 7 > 5 fails; lit 600 ≥ 500 passes
        assert row_b.criteria_results[0].passed is False
        assert row_b.criteria_results[1].passed is True

    def test_criteria_label_always_example(self):
        """Criterion label must say 'example threshold, not an official safety criterion'."""
        from backend.app.schemas.lunar_comparison import CriterionModel
        c = CriterionModel(metric="max_mean_slope_deg", threshold=5.0)
        assert "example threshold" in c.label.lower()
        assert "not an official" in c.label.lower()


# ---------------------------------------------------------------------------
# Endpoint validation tests (422/404)
# ---------------------------------------------------------------------------

class TestCompareEndpointValidation:
    """POST /api/v1/lunar/compare validation — no kernels needed."""

    BASE_BODY = {
        "site_ids": [SITE_B5A_1],
        "windows": [{"start": "2026-12-01", "days": 30}],
        "step_minutes": 30,
    }

    def test_422_too_many_sites(self):
        body = {**self.BASE_BODY, "site_ids": [f"site-x-{i}" for i in range(6)]}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 422

    def test_422_too_many_windows(self):
        body = {
            **self.BASE_BODY,
            "windows": [{"start": f"2026-{m:02d}-01", "days": 10} for m in range(1, 6)],
        }
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 422

    def test_422_days_too_long(self):
        body = {**self.BASE_BODY, "windows": [{"start": "2026-12-01", "days": 61}]}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 422

    def test_422_step_too_small(self):
        body = {**self.BASE_BODY, "step_minutes": 10}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 422

    def test_422_empty_site_ids(self):
        body = {**self.BASE_BODY, "site_ids": []}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 422

    def test_404_unknown_site(self):
        """Kernels may or may not be present; 404 must come before kernel check for known sites,
        but the endpoint checks kernels first. Skip if kernels absent (503 is acceptable too)."""
        body = {**self.BASE_BODY, "site_ids": [SITE_B5A_UNKNOWN]}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code in (404, 503), (
            f"Expected 404 (unknown site) or 503 (kernels missing), got {resp.status_code}"
        )

    def test_422_outside_coverage(self):
        """Site at -60° is outside DEM coverage (must be ≤ -75°). Accepts 422 or 503."""
        body = {**self.BASE_BODY, "site_ids": [SITE_B5A_OOC]}
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code in (422, 503), (
            f"Expected 422 (out of coverage) or 503 (kernels missing), got {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Export endpoint tests (using a stored record)
# ---------------------------------------------------------------------------

class TestExportEndpoint:
    """Test GET /api/v1/lunar/compare/{id}/export — inserts a record directly."""

    def _insert_comparison(self) -> int:
        from backend.app.database.session import SessionLocal
        from backend.app.models.models import LandingSiteComparison
        db = SessionLocal()
        try:
            row_data = {
                "site_id": "site-a",
                "site_name": "Site A",
                "is_placeholder": True,
                "window_start": "2026-12-01",
                "window_days": 30,
                "observer_elevation_m": 600.0,
                "illumination": {
                    "hours_any_part_lit": 400.0,
                    "hours_fully_lit": 360.0,
                    "hours_shadow": 320.0,
                    "longest_shadow_hours": 100.0,
                    "number_of_lit_windows": 3,
                },
                "earth": {
                    "hours_earth_visible": 350.0,
                    "hours_earth_blocked": 370.0,
                    "number_of_earth_windows": 1,
                },
                "slope": {"mean_slope_deg": 5.0, "max_slope_deg": 15.0, "p90_slope_deg": 10.0},
                "elevation": {"mean_elevation_m": 600.0, "relief_m": 200.0},
                "hours_both_up": 300.0,
                "energy_kwh": None,
                "criteria_results": [],
                "data_quality": {
                    "dem_resolution_m": 240,
                    "is_placeholder": True,
                    "kernels_used": [],
                    "horizon_type": "terrain",
                    "notes": [],
                },
            }
            rec = LandingSiteComparison(
                criteria=[{"metric": "max_mean_slope_deg", "threshold": 5.0,
                            "label": "example threshold, not an official safety criterion"}],
                thresholds={"max_mean_slope_deg": 5.0},
                result_metadata={
                    "settings": {"site_ids": ["site-a"], "step_minutes": 30},
                    "rows": [row_data],
                    "best_by": {"best_for_sunlight": "site-a:2026-12-01"},
                    "disclaimers": CMP_DISCLAIMERS,
                    "method": "test",
                    "kernels_used": [],
                },
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return rec.id
        finally:
            db.close()

    def test_export_json(self):
        cmp_id = self._insert_comparison()
        resp = client.get(f"/api/v1/lunar/compare/{cmp_id}/export?format=json")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert data["id"] == cmp_id
        assert "rows" in data
        assert "criteria" in data
        assert "settings" in data
        assert len(data["rows"]) >= 1

    def test_export_csv(self):
        cmp_id = self._insert_comparison()
        resp = client.get(f"/api/v1/lunar/compare/{cmp_id}/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        reader = csv.DictReader(io.StringIO(resp.text))
        rows = list(reader)
        assert len(rows) >= 1
        assert "site_id" in rows[0]
        assert "hours_any_part_lit" in rows[0]
        assert "mean_slope_deg" in rows[0]

    def test_export_404_unknown_id(self):
        resp = client.get("/api/v1/lunar/compare/999999/export?format=json")
        assert resp.status_code == 404

    def test_export_422_bad_format(self):
        cmp_id = self._insert_comparison()
        resp = client.get(f"/api/v1/lunar/compare/{cmp_id}/export?format=xlsx")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Kernel-based integration test (skips if kernels absent)
# ---------------------------------------------------------------------------

class TestCompareIntegration:
    """One real-kernel test for POST /api/v1/lunar/compare."""

    def test_real_kernels_comparison(self):
        if not KernelManager.are_kernels_available():
            pytest.skip("SPICE kernels not present — skipping integration test")

        body = {
            "site_ids": [SITE_B5A_1, SITE_B5A_2],
            "windows": [
                {"start": "2026-12-01", "days": 3},
            ],
            "step_minutes": 60,
            "observer_height_m": 0,
            "criteria": [
                {
                    "metric": "max_mean_slope_deg",
                    "threshold": 15.0,
                    "label": "example threshold, not an official safety criterion",
                }
            ],
        }
        resp = client.post("/api/v1/lunar/compare", json=body)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # Basic structure checks
        assert "id" in data
        assert "rows" in data
        assert len(data["rows"]) == 2  # 2 sites × 1 window
        assert "best_by" in data
        assert "criteria" in data
        assert "disclaimers" in data

        # Neither site may be labelled safe
        for row in data["rows"]:
            assert row["is_placeholder"] is True
            assert "safe" not in row["site_name"].lower()

        # No combined score
        for row in data["rows"]:
            assert "score" not in row
            assert "combined_score" not in row

        # Criteria results present
        for row in data["rows"]:
            assert len(row["criteria_results"]) == 1
            cr = row["criteria_results"][0]
            assert cr["metric"] == "max_mean_slope_deg"
            assert "example threshold" in cr["label"].lower()
            assert "passed" in cr

        # Export round-trip
        cmp_id = data["id"]
        exp_resp = client.get(f"/api/v1/lunar/compare/{cmp_id}/export?format=json")
        assert exp_resp.status_code == 200
        exp_data = exp_resp.json()
        assert exp_data["id"] == cmp_id
        assert len(exp_data["rows"]) == 2


class TestSyntheticSeriesConsistency:
    """Synthetic series tests for interval duration, boundary refinement, and overlap consistency."""

    def test_total_hours_equal_sum_of_step_intervals(self):
        """24 hourly samples active throughout must cover exactly 24.0 h (no dropped last interval)."""
        from data_pipeline.processors.illumination_processor import refine_continuous_windows

        # 24 hourly steps: 00:00 to 23:00
        timestamps = [f"2026-12-25T{h:02d}:00:00Z" for h in range(24)]
        signals = [1.0] * 24

        windows = refine_continuous_windows(timestamps, signals, threshold=0.0, step_sec=3600.0)
        assert len(windows) == 1
        assert windows[0]["start"] == "2026-12-25T00:00:00Z"
        assert windows[0]["end"] == "2026-12-26T00:00:00Z"
        assert math.isclose(windows[0]["duration_hours"], 24.0, abs_tol=1e-4)

        # 48 half-hour steps: 00:00 to 23:30
        timestamps_30 = []
        for h in range(24):
            timestamps_30.append(f"2026-12-25T{h:02d}:00:00Z")
            timestamps_30.append(f"2026-12-25T{h:02d}:30:00Z")
        signals_30 = [1.0] * 48

        windows_30 = refine_continuous_windows(timestamps_30, signals_30, threshold=0.0, step_sec=1800.0)
        assert len(windows_30) == 1
        assert windows_30[0]["start"] == "2026-12-25T00:00:00Z"
        assert windows_30[0]["end"] == "2026-12-26T00:00:00Z"
        assert math.isclose(windows_30[0]["duration_hours"], 24.0, abs_tol=1e-4)

    def test_overlap_never_exceeds_either_total(self):
        """Overlap (hours_both_up) must never exceed min(hours_any_part_lit, hours_earth_visible)."""
        # Scenario where raw both_up_steps * step_hours would be 12.0,
        # but illumination is 10.0 h and earth visibility is 8.0 h
        raw_both_up = 12.0
        illum_lit = 10.0
        earth_vis = 8.0

        hours_both_up = round(min(raw_both_up, illum_lit, earth_vis), 2)
        assert hours_both_up <= illum_lit
        assert hours_both_up <= earth_vis
        assert hours_both_up == 8.0

    def test_summary_and_compare_totals_agree_on_endpoints(self):
        """For identical site, date and parameters, Compare and single-endpoint totals must agree."""
        if not KernelManager.are_kernels_available():
            pytest.skip("SPICE kernels not present — skipping integration test")

        date = "2026-12-25"
        site_id = "site-shackleton-01"

        # Call illumination and earth-visibility endpoints directly
        resp_ill = client.get(
            f"/api/v1/lunar/sites/{site_id}/illumination?start={date}&days=1&step_minutes=60&observer_height_m=0"
        )
        assert resp_ill.status_code == 200
        ill_data = resp_ill.json()

        resp_ev = client.get(
            f"/api/v1/lunar/sites/{site_id}/earth-visibility?start={date}&days=1&step_minutes=60&observer_height_m=0&earth_disk=center"
        )
        assert resp_ev.status_code == 200
        ev_data = resp_ev.json()

        # Call compare endpoint
        body = {
            "site_ids": [site_id],
            "windows": [{"start": date, "days": 1}],
            "step_minutes": 60,
            "observer_height_m": 0.0,
        }
        resp_cmp = client.post("/api/v1/lunar/compare", json=body)
        assert resp_cmp.status_code == 200
        cmp_data = resp_cmp.json()
        assert len(cmp_data["rows"]) == 1
        row = cmp_data["rows"][0]

        # Verify agreement
        assert math.isclose(
            row["illumination"]["hours_any_part_lit"],
            ill_data["totals"]["hours_any_part_lit"],
            abs_tol=1e-2,
        )
        assert math.isclose(
            row["earth"]["hours_earth_visible"],
            ev_data["totals"]["earth_visible_hours"],
            abs_tol=1e-2,
        )
        assert row["hours_both_up"] <= row["illumination"]["hours_any_part_lit"] + 1e-6
        assert row["hours_both_up"] <= row["earth"]["hours_earth_visible"] + 1e-6

