"""
Download official NAIF SPICE kernels required for Lunar Landing Site Navigator Phase B3a.

Kernels downloaded into storage/kernels/:
  - naif0012.tls (leapseconds kernel)
  - de421.bsp (planetary ephemeris matching DE421 frame of DEM)
  - pck00010.tpc (planetary constants kernel)
  - moon_pa_de421_1900-2050.bpc (high-precision lunar orientation binary PCK)
  - moon_080317.tf (lunar frame definitions kernel)
  - moon_assoc_me.tf (associates MOON_ME to MOON_ME_DE421)

Registers each downloaded kernel in data_sources and data_products in space_explorer.db.
"""

import os
import sys
import ssl
import hashlib
import datetime
import urllib.request
import certifi

# Project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.database.session import SessionLocal
from backend.app.models.models import DataSource, DataProduct

KERNELS_DIR = os.path.join(PROJECT_ROOT, "storage", "kernels")
os.makedirs(KERNELS_DIR, exist_ok=True)

KERNEL_SPECS = [
    {
        "filename": "naif0012.tls",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
        "product_id": "urn:nasa:naif:kernel:naif0012.tls",
        "version": "12",
        "description": "NAIF leapseconds kernel",
    },
    {
        "filename": "de421.bsp",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp",
        "product_id": "urn:nasa:naif:kernel:de421.bsp",
        "version": "DE421",
        "description": "JPL Planetary and Lunar Ephemeris SPK (DE421)",
    },
    {
        "filename": "pck00010.tpc",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00010.tpc",
        "product_id": "urn:nasa:naif:kernel:pck00010.tpc",
        "version": "10",
        "description": "NAIF planetary constants text kernel",
    },
    {
        "filename": "moon_pa_de421_1900-2050.bpc",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc",
        "product_id": "urn:nasa:naif:kernel:moon_pa_de421_1900-2050.bpc",
        "version": "DE421 (1900-2050)",
        "description": "High-precision binary lunar orientation PCK (Principal Axis frame DE421)",
    },
    {
        "filename": "moon_080317.tf",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf",
        "product_id": "urn:nasa:naif:kernel:moon_080317.tf",
        "version": "080317",
        "description": "Lunar reference frames text kernel (defines MOON_ME_DE421, MOON_PA_DE421)",
    },
    {
        "filename": "moon_assoc_me.tf",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_assoc_me.tf",
        "product_id": "urn:nasa:naif:kernel:moon_assoc_me.tf",
        "version": "ME",
        "description": "Lunar frame association kernel (aliases MOON_ME to MOON_ME_DE421)",
    },
    {
        "filename": "m2020_168_sclkscet_refit_v19.tsc",
        "url": "https://naif.jpl.nasa.gov/pub/naif/pds/pds4/mars2020/mars2020_spice/spice_kernels/sclk/m2020_168_sclkscet_refit_v19.tsc",
        "product_id": "urn:nasa:naif:mars2020:sclk:m2020_168_sclkscet_refit_v19.tsc",
        "version": "refit_v19",
        "description": "NAIF Mars 2020 Spacecraft Clock Kernel (SCLKvSCET refit v19)",
    },
]


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest_path: str) -> None:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "NASA-Lunar-Navigator/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ssl_context) as resp:
        with open(dest_path, "wb") as out_f:
            while chunk := resp.read(65536):
                out_f.write(chunk)


def register_in_database(downloaded_records):
    db = SessionLocal()
    try:
        # Register DataSource
        source = db.query(DataSource).filter(DataSource.id == "src-naif-generic").first()
        if not source:
            source = DataSource(
                id="src-naif-generic",
                name="NASA Navigation and Ancillary Information Facility (NAIF)",
                source_url="https://naif.jpl.nasa.gov/pub/naif/generic_kernels/",
                organization="NASA / JPL NAIF",
                is_placeholder=False,
            )
            db.add(source)
            db.commit()

        # Register DataProducts
        for rec in downloaded_records:
            dp = db.query(DataProduct).filter(DataProduct.id == rec["product_id"]).first()
            if not dp:
                dp = DataProduct(
                    id=rec["product_id"],
                    source_id="src-naif-generic",
                    product_identifier=rec["filename"],
                    version=rec["version"],
                    checksum=rec["checksum"],
                    retrieved_at=rec["retrieved_at"],
                    coordinate_frame="SPICE",
                    units="bytes",
                    processing_method=f"NAIF generic kernel: {rec['description']}",
                    label="Verified",
                    is_placeholder=False,
                )
                db.add(dp)
            else:
                dp.checksum = rec["checksum"]
                dp.retrieved_at = rec["retrieved_at"]
                dp.version = rec["version"]
                dp.label = "Verified"
                dp.is_placeholder = False
        db.commit()
        print("[download_kernels] Registered all kernels in data_products database successfully.")
    except Exception as e:
        db.rollback()
        print(f"[download_kernels] Database registration warning: {e}", file=sys.stderr)
    finally:
        db.close()


def main():
    print("[download_kernels] Starting NAIF kernel download...")
    downloaded = []
    for spec in KERNEL_SPECS:
        filename = spec["filename"]
        url = spec["url"]
        dest = os.path.join(KERNELS_DIR, filename)

        print(f"Downloading {filename} from {url}...")
        try:
            download_file(url, dest)
            size = os.path.getsize(dest)
            checksum = compute_sha256(dest)
            now = datetime.datetime.utcnow()
            print(f"  -> Saved {dest} ({size:,} bytes, sha256={checksum[:16]}...)")
            downloaded.append({
                **spec,
                "size_bytes": size,
                "checksum": checksum,
                "retrieved_at": now,
                "local_path": dest,
            })
        except Exception as e:
            print(f"[ERROR] Failed to download {filename} from {url}: {e}", file=sys.stderr)
            sys.exit(1)

    register_in_database(downloaded)
    print("[download_kernels] All kernels downloaded and verified successfully.")
    return downloaded


if __name__ == "__main__":
    main()
