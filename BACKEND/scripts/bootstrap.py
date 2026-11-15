"""
bootstrap.py — Idempotent startup script for the Space Explorer backend.

Steps:
  (a) DB seeding   : copy seed/space_explorer.seed.db if DB missing or empty
  (b) SPICE kernels: download kernels if any are missing in storage/kernels/
  (c) LOLA DEM     : download ldem_75s_240m.img if missing and verify checksum
  (d) Processed    : regenerate .npy rasters and preview layers if missing

Run directly:
    python scripts/bootstrap.py

Or called on startup when BOOTSTRAP_ON_START=true (from main.py lifespan).
"""

import os
import sys
import shutil
import hashlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

LOLA_DEM_FILENAME = "ldem_75s_240m.img"
LOLA_DEM_LBL_FILENAME = "ldem_75s_240m.lbl"
# Known SHA256 of the official NASA PDS LOLA South Polar 240m DEM
LOLA_DEM_EXPECTED_SHA256 = "D031EFE2611B17DFBF3C158F5E15DC04CD5719349DCBF6384BB21FD97697C490"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def step_a_seed_database() -> None:
    """Copy seed DB if main DB is missing or effectively empty (< 100 KB)."""
    db_path = os.path.join(PROJECT_ROOT, "space_explorer.db")
    seed_path = os.path.join(PROJECT_ROOT, "seed", "space_explorer.seed.db")

    if not os.path.exists(seed_path):
        print(f"[bootstrap] SKIP seed: seed file not found at {seed_path}")
        return

    needs_seed = (
        not os.path.exists(db_path)
        or os.path.getsize(db_path) < 100_000
    )
    if needs_seed:
        shutil.copy2(seed_path, db_path)
        size_mb = os.path.getsize(db_path) / 1_048_576
        print(f"[bootstrap] DB seeded from {seed_path} → {db_path} ({size_mb:.2f} MB)")
    else:
        size_mb = os.path.getsize(db_path) / 1_048_576
        print(f"[bootstrap] DB already exists ({size_mb:.2f} MB) — skipping seed")


def step_b_kernels() -> None:
    """Download SPICE kernels if any are missing."""
    kernels_dir = os.path.join(PROJECT_ROOT, "storage", "kernels")
    os.makedirs(kernels_dir, exist_ok=True)

    download_kernels_path = os.path.join(PROJECT_ROOT, "scripts", "download_kernels.py")
    if not os.path.exists(download_kernels_path):
        print("[bootstrap] SKIP kernels: scripts/download_kernels.py not found")
        return

    import importlib.util
    spec = importlib.util.spec_from_file_location("download_kernels", download_kernels_path)
    dk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dk)

    missing = []
    for kernel in dk.KERNEL_SPECS:
        fpath = os.path.join(kernels_dir, kernel["filename"])
        if not os.path.exists(fpath):
            missing.append(kernel)

    if not missing:
        print(f"[bootstrap] Kernels: all {len(dk.KERNEL_SPECS)} kernels present — skipping download")
        return

    print(f"[bootstrap] Kernels: {len(missing)} missing — downloading …")
    for kernel in missing:
        try:
            dk.download_kernel(kernel)
            print(f"[bootstrap]   ✓ {kernel['filename']}")
        except Exception as e:
            print(f"[bootstrap]   ✗ {kernel['filename']}: {e}")


def step_c_lola_dem() -> None:
    """Download LOLA DEM if missing and verify checksum."""
    raw_lunar_dir = os.path.join(PROJECT_ROOT, "storage", "raw", "lunar")
    dem_path = os.path.join(raw_lunar_dir, LOLA_DEM_FILENAME)
    lbl_path = os.path.join(raw_lunar_dir, LOLA_DEM_LBL_FILENAME)

    if os.path.exists(dem_path) and os.path.getsize(dem_path) > 1_000_000:
        actual_sha = _sha256(dem_path)
        size_mb = os.path.getsize(dem_path) / 1_048_576
        if actual_sha == LOLA_DEM_EXPECTED_SHA256:
            print(f"[bootstrap] LOLA DEM already present and verified ({size_mb:.2f} MB, SHA256: {actual_sha[:16]}…) — skipping download")
            return
        else:
            print(f"[bootstrap] LOLA DEM checksum mismatch ({actual_sha} != {LOLA_DEM_EXPECTED_SHA256}), re-downloading …")

    print("[bootstrap] LOLA DEM missing or unverified — downloading via collector …")
    try:
        from data_pipeline.collectors.lro_lola_collector import LROLOLACollector
        from backend.app.database.session import SessionLocal

        collector = LROLOLACollector(target_dir=raw_lunar_dir)
        res = collector.download_product()

        db = SessionLocal()
        try:
            collector.register_in_db(res, db)
        finally:
            db.close()

        actual_sha = _sha256(dem_path)
        size_mb = os.path.getsize(dem_path) / 1_048_576
        print(f"[bootstrap] LOLA DEM downloaded ({size_mb:.2f} MB, SHA256: {actual_sha[:16]}…)")
    except Exception as e:
        print(f"[bootstrap] WARNING: LOLA DEM download failed: {e}")


def step_d_processed_rasters() -> None:
    """Regenerate processed lunar rasters (DEM .npy and preview sidecars) if missing."""
    npy_path = os.path.join(
        PROJECT_ROOT, "storage", "processed", "lunar", "ldem_75s_240m_elev.npy"
    )
    raw_lunar_dir = os.path.join(PROJECT_ROOT, "storage", "raw", "lunar")
    dem_path = os.path.join(raw_lunar_dir, LOLA_DEM_FILENAME)
    lbl_path = os.path.join(raw_lunar_dir, LOLA_DEM_LBL_FILENAME)

    npy_exists = os.path.exists(npy_path) and os.path.getsize(npy_path) > 1_000_000

    if not npy_exists:
        if not os.path.exists(dem_path) or not os.path.exists(lbl_path):
            print("[bootstrap] SKIP processed rasters: raw DEM / LBL not present")
        else:
            print("[bootstrap] Processed elevation .npy missing — generating from raw DEM …")
            try:
                from data_pipeline.parsers.dem_parser import DEMParser
                parser = DEMParser()
                parser.report(dem_path, lbl_path, save_processed=npy_path)
                size_mb = os.path.getsize(npy_path) / 1_048_576
                print(f"[bootstrap] Elevation .npy generated ({size_mb:.2f} MB)")
            except Exception as e:
                print(f"[bootstrap] WARNING: DEM .npy generation failed: {e}")
    else:
        size_mb = os.path.getsize(npy_path) / 1_048_576
        print(f"[bootstrap] Elevation .npy already present ({size_mb:.2f} MB) — skipping")

    # Check preview sidecars
    dem_png = os.path.join(PROJECT_ROOT, "storage", "processed", "lunar_dem.png")
    slope_png = os.path.join(PROJECT_ROOT, "storage", "processed", "lunar_slope.png")
    if not os.path.exists(dem_png) or not os.path.exists(slope_png):
        print("[bootstrap] Preview layers missing — generating sidecars …")
        try:
            from data_pipeline.processors.lunar_raster_processor import generate_lunar_rasters_and_sidecars
            generate_lunar_rasters_and_sidecars()
            print("[bootstrap] Preview layers and sidecars generated.")
        except Exception as e:
            print(f"[bootstrap] WARNING: Sidecars generation failed: {e}")
    else:
        print("[bootstrap] Preview layers and sidecars already present — skipping")


def run_bootstrap() -> None:
    """Run all bootstrap steps in order. Called from main.py on BOOTSTRAP_ON_START=true."""
    print("[bootstrap] === Starting bootstrap ===")
    step_a_seed_database()
    step_b_kernels()
    step_c_lola_dem()
    step_d_processed_rasters()
    print("[bootstrap] === Bootstrap complete ===")


if __name__ == "__main__":
    run_bootstrap()
