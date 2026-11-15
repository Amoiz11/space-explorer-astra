"""
Tests for B1b DEM pipeline:
  - DEMParser with synthetic label and array
  - LunarCoordinateProcessor lat/lon <-> pixel round-trip
  - UnsupportedProjectionError on missing parameter
  - No-data handling (suspicious sentinel reporting)
  - dem_reprojection metadata (no reprojection applied)

No network calls. No real .IMG file read (uses synthetic data).
"""
import math
import numpy as np
import pytest

from data_pipeline.parsers.dem_parser import DEMParser
from data_pipeline.processors.lunar_coordinate_processor import (
    LunarCoordinateProcessor,
    UnsupportedProjectionError,
)
from data_pipeline.processors.dem_reprojection import get_conversion_metadata


# ---------------------------------------------------------------------------
# Synthetic label string for DEMParser tests
# ---------------------------------------------------------------------------
SYNTHETIC_LABEL = """\
PDS_VERSION_ID       = "PDS3"
PRODUCT_VERSION_ID   = "V2.0"

OBJECT               = UNCOMPRESSED_FILE
FILE_NAME            = "SYNTHETIC_DEM.IMG"
RECORD_TYPE          = FIXED_LENGTH
FILE_RECORDS         = 4
RECORD_BYTES         = 8
^IMAGE               = "SYNTHETIC_DEM.IMG"
  OBJECT             = IMAGE
    NAME             = HEIGHT
    LINES            = 4
    LINE_SAMPLES     = 4
    SAMPLE_TYPE      = LSB_INTEGER
    SAMPLE_BITS      = 16
    UNIT             = METER
    SCALING_FACTOR   = 0.5
    OFFSET           = 1737400.
  END_OBJECT         = IMAGE
END_OBJECT           = UNCOMPRESSED_FILE

OBJECT               = IMAGE_MAP_PROJECTION
 MAP_PROJECTION_TYPE          = "POLAR STEREOGRAPHIC"
 KEYWORD_LATITUDE_TYPE        = "PLANETOCENTRIC"
 MAP_SCALE                    = 240 <m/pix>
 A_AXIS_RADIUS                = 1737.4 <km>
 POSITIVE_LONGITUDE_DIRECTION = "EAST"
 CENTER_LATITUDE              = -90 <deg>
 CENTER_LONGITUDE             = 0 <deg>
 MAP_RESOLUTION               = 126.347 <pix/deg>
 MAXIMUM_LATITUDE             = -75 <deg>
 MINIMUM_LATITUDE             = -90 <deg>
END_OBJECT                    = IMAGE_MAP_PROJECTION

END
"""


class TestDEMParser:
    """Unit tests for DEMParser using synthetic label text and in-memory array."""

    def _make_parser_and_label(self, tmp_path):
        """Write synthetic label to a temp file and parse it."""
        lbl_file = tmp_path / "synthetic.lbl"
        lbl_file.write_text(SYNTHETIC_LABEL, encoding="utf-8")
        parser = DEMParser()
        label = parser.parse_label(str(lbl_file))
        return parser, label

    def test_label_parsing(self, tmp_path):
        _, label = self._make_parser_and_label(tmp_path)
        assert label["lines"] == 4
        assert label["line_samples"] == 4
        assert label["sample_type"] == "LSB_INTEGER"
        assert label["dtype"] == "<i2"
        assert label["scaling_factor"] == 0.5
        assert label["offset_m"] == 1737400.0
        assert label["map_scale"] == 240.0
        assert label["unit"] == "METER"

    def test_elevation_conversion(self, tmp_path):
        """HEIGHT = DN * SCALING_FACTOR (from label NOTE and DSMAP_POLAR.CAT)."""
        parser, label = self._make_parser_and_label(tmp_path)
        # DN values: 0, 100, -200, 32767 (sentinel)
        dn = np.array([[0, 100, -200, 32767]], dtype=np.int16)
        elev = parser.to_elevation(dn, label)
        assert elev[0, 0] == 0.0
        assert elev[0, 1] == 50.0        # 100 * 0.5
        assert elev[0, 2] == -100.0      # -200 * 0.5
        # Sentinel value: reported as suspicious but still converted correctly
        assert elev[0, 3] == 32767 * 0.5

    def test_no_data_note(self, tmp_path):
        """Label states no fill value; no_data_note must be 'not stated in label'."""
        parser, label = self._make_parser_and_label(tmp_path)
        # Build a small synthetic IMG with one sentinel pixel
        dn = np.array([[0, 100, -32768, 50]], dtype="<i2")
        # simulate report on a fresh synthetic img file
        img_file = tmp_path / "synthetic.img"
        dn_4x4 = np.zeros((4, 4), dtype="<i2")
        dn_4x4[0, 0] = -32768   # suspicious sentinel
        dn_4x4.tofile(str(img_file))

        lbl_file = tmp_path / "synthetic.lbl"
        lbl_file.write_text(SYNTHETIC_LABEL, encoding="utf-8")
        result = parser.report(str(img_file), str(lbl_file))

        assert result["no_data_note"] == "not stated in label"
        # Sentinel -32768 should be flagged as suspicious
        assert -32768 in result["suspicious_fill_sentinels"]
        assert result["suspicious_fill_sentinels"][-32768] == 1
        assert result["suspicious_fill_pct"] > 0.0

    def test_no_suspicious_fills_in_clean_data(self, tmp_path):
        """Clean data with no sentinels: suspicious count = 0."""
        parser, label = self._make_parser_and_label(tmp_path)
        img_file = tmp_path / "clean.img"
        dn = np.zeros((4, 4), dtype="<i2")
        dn[1, 1] = 100
        dn[2, 2] = -200
        dn.tofile(str(img_file))

        lbl_file = tmp_path / "synthetic.lbl"
        lbl_file.write_text(SYNTHETIC_LABEL, encoding="utf-8")
        result = parser.report(str(img_file), str(lbl_file))
        assert result["suspicious_fill_count"] == 0
        assert result["suspicious_fill_pct"] == 0.0


class TestLunarCoordinateProcessor:
    """
    Tests for DSMAP_POLAR.CAT formula implementation.
    Uses the ACTUAL label parameters from LDEM_75S_240M.
    """

    LABEL_PARAMS = {
        "map_scale": 240.0,       # metres/pixel (from label MAP_SCALE)
        "lines": 3812,            # from label LINES (square image)
        "line_samples": 3812,     # from label LINE_SAMPLES
        "center_latitude": -90.0, # from label CENTER_LATITUDE
    }

    def test_projection_info_never_epsg4326(self):
        proc = LunarCoordinateProcessor(self.LABEL_PARAMS)
        info = proc.projection_info()
        # Projection must be POLAR STEREOGRAPHIC, never EPSG:4326 as the CRS
        assert "POLAR STEREOGRAPHIC" in info["projection"]
        assert info["hemisphere"] == "south"
        assert info["sphere_radius_m"] == 1737400.0
        # The coordinate_system must NOT reference EPSG:4326
        assert "EPSG:4326" not in info.get("coordinate_system", "")
        assert "EPSG:4326" not in info["projection"]

    def test_unsupported_error_missing_map_scale(self):
        """Missing map_scale must raise UnsupportedProjectionError."""
        bad_params = dict(self.LABEL_PARAMS)
        del bad_params["map_scale"]
        with pytest.raises(UnsupportedProjectionError) as exc_info:
            LunarCoordinateProcessor(bad_params)
        assert "map_scale" in str(exc_info.value)

    def test_unsupported_error_missing_lines(self):
        """Missing lines must raise UnsupportedProjectionError."""
        bad_params = dict(self.LABEL_PARAMS)
        del bad_params["lines"]
        with pytest.raises(UnsupportedProjectionError) as exc_info:
            LunarCoordinateProcessor(bad_params)
        assert "lines" in str(exc_info.value)

    def test_unsupported_error_non_polar(self):
        """Non-polar center_latitude must raise UnsupportedProjectionError."""
        bad_params = dict(self.LABEL_PARAMS)
        bad_params["center_latitude"] = 45.0
        with pytest.raises(UnsupportedProjectionError) as exc_info:
            LunarCoordinateProcessor(bad_params)
        assert "center_latitude" in str(exc_info.value)

    def test_south_pole_maps_to_image_center(self):
        """South pole (lat=-90, lon=0) must map very close to image centre."""
        proc = LunarCoordinateProcessor(self.LABEL_PARAMS)
        N = self.LABEL_PARAMS["lines"]
        I, J = proc.latlon_to_pixel(-90.0, 0.0)
        # Center is at N/2 + 0.5 = 1906.5
        assert abs(I - (N / 2 + 0.5)) < 0.01, f"I={I} should be {N/2+0.5}"
        assert abs(J - (N / 2 + 0.5)) < 0.01, f"J={J} should be {N/2+0.5}"

    def test_latlon_to_pixel_roundtrip_near_pole(self):
        """Round-trip at lat=-89.9, lon=0 must be exact (numerical precision)."""
        proc = LunarCoordinateProcessor(self.LABEL_PARAMS)
        lat_in, lon_in = -89.9, 0.0
        I, J = proc.latlon_to_pixel(lat_in, lon_in)
        lat_rt, lon_rt = proc.pixel_to_latlon(I, J)
        assert abs(lat_rt - lat_in) < 1e-6, f"lat round-trip error: {abs(lat_rt - lat_in)}"
        assert abs(lon_rt - lon_in) < 1e-6, f"lon round-trip error: {abs(lon_rt - lon_in)}"

    def test_latlon_to_pixel_roundtrip_at_coverage_edge(self):
        """Round-trip at lat=-75, lon=180 (coverage edge) must be < 1 pixel."""
        proc = LunarCoordinateProcessor(self.LABEL_PARAMS)
        lat_in, lon_in = -75.0, 180.0
        I, J = proc.latlon_to_pixel(lat_in, lon_in)
        lat_rt, lon_rt = proc.pixel_to_latlon(I, J)
        # Tolerance: 1 pixel = 240 m ≈ 0.008 deg at -75 lat
        assert abs(lat_rt - lat_in) < 0.01, f"lat round-trip error: {abs(lat_rt - lat_in)}"

    def test_pixel_to_latlon_roundtrip_mid_image(self):
        """Round-trip starting from latlon is lossless (sub-pixel)."""
        proc = LunarCoordinateProcessor(self.LABEL_PARAMS)
        # Use a point inside the coverage
        lat_in, lon_in = -82.0, 90.0
        I, J = proc.latlon_to_pixel(lat_in, lon_in)
        lat_rt, lon_rt = proc.pixel_to_latlon(I, J)
        assert abs(lat_rt - lat_in) < 1e-6, f"lat round-trip error: {abs(lat_rt - lat_in)}"
        assert abs(lon_rt - lon_in) < 1e-6, f"lon round-trip error: {abs(lon_rt - lon_in)}"

        # Also round-trip starting from pixel space
        I_in, J_in = 1500.0, 1500.0
        lat2, lon2 = proc.pixel_to_latlon(I_in, J_in)
        I_rt, J_rt = proc.latlon_to_pixel(lat2, lon2)
        assert abs(I_rt - I_in) < 0.5, f"Sample round-trip error: {abs(I_rt - I_in)} px"
        assert abs(J_rt - J_in) < 0.5, f"Line round-trip error: {abs(J_rt - J_in)} px"

    def test_synthetic_polar_grid_elevations(self):
        """
        Build a small synthetic 11x11 polar stereographic elevation grid
        centred on the south pole, with elevation = radial distance / 1000.
        Verify that the centre pixel (pole) is at elevation 0
        and the edge pixel has non-zero elevation.
        """
        N = 11
        proc = LunarCoordinateProcessor({
            "map_scale": 240.0,
            "lines": N,
            "line_samples": N,
            "center_latitude": -90.0,
        })
        # Build elevation array: elevation = pixel distance from centre in metres
        centre = N / 2 + 0.5
        grid_I, grid_J = np.meshgrid(
            np.arange(1, N + 1, dtype=float),
            np.arange(1, N + 1, dtype=float),
        )
        # Radial distance in pixels from centre
        dist = np.sqrt((grid_I - centre) ** 2 + (grid_J - centre) ** 2)
        # Elevation = dist * 240 / 1000 (metres / 1000 as a simple synthetic value)
        elev = (dist * 240.0 / 1000.0).astype(np.float32)

        # Centre pixel (1-based midpoint) should map to exactly the pole
        centre_I = centre
        centre_J = centre
        lat_c, lon_c = proc.pixel_to_latlon(centre_I, centre_J)
        assert abs(lat_c - (-90.0)) < 1e-10, f"Centre should be pole, got lat={lat_c}"

        # Elevation at south pole (centre pixel) should be ~0
        e_pole, row, col = proc.get_elevation_at_latlon(-90.0, 0.0, elev)
        assert abs(e_pole) < 0.01, f"Pole elevation should be 0, got {e_pole}"

        # Elevation at a non-pole point should be positive
        e_edge, _, _ = proc.get_elevation_at_latlon(
            proc.pixel_to_latlon(1.0, 1.0)[0],
            proc.pixel_to_latlon(1.0, 1.0)[1],
            elev,
        )
        assert e_edge > 0.0, f"Edge elevation should be positive, got {e_edge}"

    def test_orientation_asymmetric_synthetic_grid(self):
        """
        Step 0c orientation check:
        Construct an asymmetric synthetic grid with 4 distinct directional quadrants/features.
        Verify that lat/lon sampling retrieves the correct directional feature:
          - lon 0° points UP (top of grid, small line J)
          - lon 90°E points RIGHT (large sample I)
          - lon 180° points DOWN (bottom of grid, large line J)
          - lon 270°E points LEFT (small sample I)
        A flipped (vertically or horizontally) or rotated image will fail this test.
        """
        N = 11
        proc = LunarCoordinateProcessor({
            "map_scale": 240.0,
            "lines": N,
            "line_samples": N,
            "center_latitude": -90.0,
        })
        grid = np.zeros((N, N), dtype=np.float32)

        # Place 4 asymmetric markers around the south pole:
        # Center is at line J=6, sample I=6 (0-based row=5, col=5)
        # Top (lon=0°): row=2, col=5
        grid[2, 5] = 1000.0
        # Right (lon=90°E): row=5, col=8
        grid[5, 8] = 2000.0
        # Bottom (lon=180°): row=8, col=5
        grid[8, 5] = 3000.0
        # Left (lon=270°E): row=5, col=2
        grid[5, 2] = 4000.0

        # In DSMAP_POLAR.CAT, distance from center is:
        # R = 3 pixels * 240 m = 720 m
        # R = 2 * 1737400 * tan((90 - |lat|) * pi / 360)
        # tan((90 - |lat|) * pi / 360) = 720 / (2 * 1737400) ≈ 0.0002072
        # (90 - |lat|) = 2 * atan(720 / 3474800) * 180 / pi ≈ 0.02373 deg
        # lat ≈ -89.97627 deg
        lat_test = -90.0 + 2.0 * math.atan(720.0 / 3474800.0) * 180.0 / math.pi

        # Sample at lon = 0° (should be TOP: 1000.0)
        e_top, r_top, c_top = proc.get_elevation_at_latlon(lat_test, 0.0, grid)
        assert (r_top, c_top) == (2, 5), f"lon=0 should map to row=2, col=5; got ({r_top}, {c_top})"
        assert e_top == 1000.0, f"Expected 1000.0 at lon=0°, got {e_top} (flipped or rotated)"

        # Sample at lon = 90°E (should be RIGHT: 2000.0)
        e_right, r_right, c_right = proc.get_elevation_at_latlon(lat_test, 90.0, grid)
        assert (r_right, c_right) == (5, 8), f"lon=90 should map to row=5, col=8; got ({r_right}, {c_right})"
        assert e_right == 2000.0, f"Expected 2000.0 at lon=90°, got {e_right} (flipped or rotated)"

        # Sample at lon = 180° (should be BOTTOM: 3000.0)
        e_bottom, r_bottom, c_bottom = proc.get_elevation_at_latlon(lat_test, 180.0, grid)
        assert (r_bottom, c_bottom) == (8, 5), f"lon=180 should map to row=8, col=5; got ({r_bottom}, {c_bottom})"
        assert e_bottom == 3000.0, f"Expected 3000.0 at lon=180°, got {e_bottom} (flipped or rotated)"

        # Sample at lon = 270°E (should be LEFT: 4000.0)
        e_left, r_left, c_left = proc.get_elevation_at_latlon(lat_test, 270.0, grid)
        assert (r_left, c_left) == (5, 2), f"lon=270 should map to row=5, col=2; got ({r_left}, {c_left})"
        assert e_left == 4000.0, f"Expected 4000.0 at lon=270°, got {e_left} (flipped or rotated)"



class TestDEMReprojection:
    """Test reprojection module: no reprojection applied, metadata present."""

    def test_no_reprojection_applied(self):
        meta = get_conversion_metadata()
        assert meta["reprojection_applied"] is False

    def test_metadata_has_source_projection(self):
        meta = get_conversion_metadata()
        assert "POLAR STEREOGRAPHIC" in meta["source_projection"]
        assert "1737.4" in meta["source_datum"]

    def test_metadata_has_timestamp(self):
        meta = get_conversion_metadata()
        assert meta["timestamp"] is not None
        assert "T" in meta["timestamp"]   # ISO format
