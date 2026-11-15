import os
import sys
import json
import argparse
import datetime
from typing import Dict, Any

from backend.app.database.session import SessionLocal
from backend.app.database.init_db import init_database
from data_pipeline.collectors.places_collector import PlacesCollector, compute_sha256
from data_pipeline.parsers.places_parser import PlacesParser
from data_pipeline.validators.places_validator import PlacesValidator
from data_pipeline.processors.places_processor import PlacesProcessor
from data_pipeline.loaders.places_loader import PlacesLoader

def run_places_import(limit: int = 50, skip_download: bool = False, reset_previous: bool = True) -> Dict[str, Any]:
    """Run the PLACES import pipeline and produce an import report."""
    init_database()

    reports_dir = os.path.join("storage", "processed", "import_reports")
    os.makedirs(reports_dir, exist_ok=True)
    raw_dir = os.path.join("storage", "raw", "places")
    os.makedirs(raw_dir, exist_ok=True)

    csv_path = os.path.join(raw_dir, "best_interp.csv")
    xml_path = os.path.join(raw_dir, "best_interp.csv.xml")
    sclk_csv_path = os.path.join(raw_dir, "sclk_table.csv")
    sclk_xml_path = os.path.join(raw_dir, "sclk_table.csv.xml")

    # 1. Collection
    collector = PlacesCollector(storage_dir="storage/raw")
    downloaded_files = []
    need_download = not skip_download or not (
        os.path.exists(csv_path) and os.path.exists(xml_path) and os.path.exists(sclk_csv_path) and os.path.exists(sclk_xml_path)
    )

    if need_download:
        print("[Pipeline] Downloading/caching PLACES data files...")
        download_results = collector.collect()
        for res in download_results:
            downloaded_files.append({
                "url": res["url"],
                "path": res["dest_path"],
                "checksum": res["checksum"],
                "size_bytes": res["file_size"],
            })
    else:
        print(f"[Pipeline] Using cached files in {raw_dir}...")
        for p in (csv_path, xml_path, sclk_csv_path, sclk_xml_path):
            if os.path.exists(p):
                downloaded_files.append({
                    "path": p,
                    "checksum": compute_sha256(p),
                    "size_bytes": os.path.getsize(p),
                })

    csv_checksum = compute_sha256(csv_path)
    sclk_checksum = compute_sha256(sclk_csv_path) if os.path.exists(sclk_csv_path) else None

    # 2. Parsing
    print(f"[Pipeline] Parsing PDS4 XML label: {xml_path}")
    parser = PlacesParser(xml_label_path=xml_path, csv_path=csv_path)
    metadata = parser.parse_label()
    print(f"[Pipeline] Parsing table records (limit: {limit})...")
    _, raw_records = parser.parse_data(limit=limit)
    parsed_count = len(raw_records)

    # 3. Validation
    print(f"[Pipeline] Validating {parsed_count} records...")
    validator = PlacesValidator()
    valid_records, rejected_records = validator.validate_batch(raw_records)
    valid_count = len(valid_records)
    rejected_count = len(rejected_records)

    # 4. Processing / Transformation
    print(f"[Pipeline] Processing {valid_count} valid records...")
    product_id = metadata.get("logical_identifier", "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv")
    processor = PlacesProcessor(metadata=metadata)
    processed_locations = processor.process_batch(valid_records, product_id=product_id)

    # 5. Registration & Loading
    db = SessionLocal()
    deleted_count = 0
    try:
        loader = PlacesLoader(db)

        # 5a. Register sclk_table.csv product
        sclk_prod_id = "urn:nasa:pds:mars2020_rover_places:data_ancillary:sclk_table.csv"
        if sclk_checksum:
            print(f"[Pipeline] Registering SCLK DataProduct: {sclk_prod_id} (version 16.0)...")
            loader.register_product(
                product_id=sclk_prod_id,
                version="16.0",
                checksum=sclk_checksum,
                coordinate_frame="Geometry as reported by the spacecraft in telemetry",
                units="sclk",
                processing_method="Spacecraft clock correlation table for RMC site/drive",
                label="Verified",
            )

        # 5b. Register best_interp.csv product
        print(f"[Pipeline] Registering Localization DataProduct: {product_id} (version 16.0)...")
        data_product, is_dup_product = loader.register_product(
            product_id=product_id,
            version=metadata.get("version_id", "16.0"),
            checksum=csv_checksum,
            coordinate_frame=metadata.get("coordinate_frame", "Geometry as reported by the spacecraft in telemetry"),
            units=metadata.get("units", "deg, m"),
            processing_method="Rover localization and traverse mesh reconstruction (PLACES best_interp)",
            label="Estimated",
        )

        # 5c. Delete previously imported PLACES rows if requested (keep placeholders!)
        if reset_previous:
            deleted_count = loader.delete_imported_places_locations(product_id=product_id)
            print(f"[Pipeline] Deleted {deleted_count} previously imported PLACES locations (placeholders preserved).")

        # 5d. Load locations
        print(f"[Pipeline] Loading locations into database...")
        loaded_count, dup_skipped = loader.load_locations(processed_locations)
    finally:
        db.close()

    # 6. Warnings
    warnings = [
        "SCLK to UTC conversion: sclk_table.csv maps RMC (site/drive/pose) to min/max SCLK counts (spacecraft clock seconds) but does not provide UTC timestamps or a self-contained conversion formula. Converting SCLK to UTC requires the NAIF SPICE SCLK kernel (m2020_sclkscet_*.tsc) not contained in the PDS table. Observed_at is stored as null, with sol and sclk preserved per-record and exposed in the API response.",
    ]
    if is_dup_product and not reset_previous:
        warnings.append(f"DataProduct {product_id} already existed with same checksum.")

    # 7. Import Report
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_filename = f"import_report_{timestamp_str}.json"
    report_path = os.path.join(reports_dir, report_filename)

    report_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bundle": {
            "title": metadata.get("title"),
            "logical_identifier": metadata.get("logical_identifier"),
            "version": metadata.get("version_id", "16.0"),
            "coordinate_frame": metadata.get("coordinate_frame", "Geometry as reported by the spacecraft in telemetry"),
            "coordinate_description": metadata.get("coordinate_description"),
            "units": metadata.get("units", "deg, m"),
        },
        "files_downloaded": downloaded_files,
        "counts": {
            "downloaded": len(downloaded_files),
            "parsed": parsed_count,
            "valid": valid_count,
            "rejected": rejected_count,
            "loaded": loaded_count,
            "duplicates_skipped": dup_skipped,
            "previously_deleted": deleted_count,
        },
        "rejected_reasons": [r["reason"] for r in rejected_records[:10]],
        "warnings": warnings,
        "limit_applied": limit,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"[Pipeline] Import report written to: {report_path}")
    return report_data


def run_downsampled_places_import(
    raw_dir: str = "storage/raw/places",
    reset_previous: bool = False,
) -> Dict[str, Any]:
    """
    Import one localization per sol (the last pose of each sol with highest SCLK)
    across the entire PLACES best_interp dataset (~1,900 sols span).
    Preserves existing records without duplication.
    """
    import csv

    init_database()
    csv_path = os.path.join(raw_dir, "best_interp.csv")
    xml_path = os.path.join(raw_dir, "best_interp.csv.xml")

    if not os.path.exists(csv_path) or not os.path.exists(xml_path):
        raise FileNotFoundError(f"PLACES raw files missing in {raw_dir}")

    parser = PlacesParser(xml_label_path=xml_path, csv_path=csv_path)
    metadata = parser.parse_label()
    product_id = metadata.get(
        "logical_identifier",
        "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
    )

    # 1. Group rows by sol and select the pose with highest SCLK per sol
    print(f"[Downsample Pipeline] Scanning {csv_path} for last pose per sol...")
    sol_best: Dict[int, Dict[str, Any]] = {}
    total_scanned = 0

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_scanned += 1
            sol_str = row.get("sol", "").strip()
            if not sol_str:
                continue
            try:
                sol = int(float(sol_str))
            except (ValueError, TypeError):
                continue
            if sol < 0:
                continue

            sclk_str = row.get("sclk", "").strip()
            try:
                sclk_val = float(sclk_str)
            except (ValueError, TypeError):
                sclk_val = -1.0

            if sol not in sol_best or sclk_val > sol_best[sol]["_sclk_float"]:
                row_copy = dict(row)
                row_copy["_sclk_float"] = sclk_val
                sol_best[sol] = row_copy

    distinct_sols = sorted(sol_best.keys())
    min_sol = distinct_sols[0] if distinct_sols else 0
    max_sol = distinct_sols[-1] if distinct_sols else 0
    total_sol_span = (max_sol - min_sol + 1) if distinct_sols else 0
    sols_with_no_pose = total_sol_span - len(distinct_sols)

    print(
        f"[Downsample Pipeline] Found {len(distinct_sols)} distinct sols with poses (Sol {min_sol}..{max_sol})."
    )
    print(f"[Downsample Pipeline] Sols with no pose: {sols_with_no_pose}.")

    # 2. Process records through PlacesProcessor with downsampled method label
    processor = PlacesProcessor(metadata=metadata)
    processed_records = []
    for sol in distinct_sols:
        raw_row = sol_best[sol]
        raw_row.pop("_sclk_float", None)
        loc = processor.process_record(raw_row, product_id=product_id)
        loc["position_method"] = "downsampled: last localization of each sol"
        processed_records.append(loc)

    # 3. Load into database idempotently
    db = SessionLocal()
    try:
        loader = PlacesLoader(db)
        loader.register_product(
            product_id=product_id,
            version=metadata.get("version_id", "16.0"),
            checksum=compute_sha256(csv_path),
            coordinate_frame=metadata.get("coordinate_frame", "Geometry as reported by the spacecraft in telemetry"),
            units=metadata.get("units", "deg, m"),
            processing_method="Rover localization and traverse mesh reconstruction (PLACES best_interp)",
            label="Estimated",
        )
        if reset_previous:
            loader.delete_imported_places_locations(product_id=product_id)

        loaded_count, dup_skipped = loader.load_locations(processed_records)
    finally:
        db.close()

    print(
        f"[Downsample Pipeline] Finished: {loaded_count} new loaded, {dup_skipped} duplicates skipped."
    )
    return {
        "total_scanned": total_scanned,
        "distinct_sols": len(distinct_sols),
        "sol_min": min_sol,
        "sol_max": max_sol,
        "sols_with_no_pose": sols_with_no_pose,
        "loaded_count": loaded_count,
        "duplicates_skipped": dup_skipped,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mars 2020 Rover PLACES Data Import Pipeline")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of rows to parse and import")
    parser.add_argument("--skip-download", action="store_true", help="Skip download if raw files already exist")
    parser.add_argument("--no-reset", action="store_true", help="Do not delete previously imported rows")
    parser.add_argument("--downsample-sols", action="store_true", help="Import one pose per sol across full archive")
    args = parser.parse_args()

    if args.downsample_sols:
        report = run_downsampled_places_import(reset_previous=not args.no_reset)
        print("\n--- DOWNSAMPLED IMPORT SUMMARY ---")
        print(f"Distinct Sols: {report['distinct_sols']} (Sol {report['sol_min']} to {report['sol_max']})")
        print(f"Sols With No Pose: {report['sols_with_no_pose']}")
        print(f"Loaded: {report['loaded_count']}, Duplicates Skipped: {report['duplicates_skipped']}")
    else:
        report = run_places_import(
            limit=args.limit,
            skip_download=args.skip_download,
            reset_previous=not args.no_reset,
        )
        print("\n--- IMPORT SUMMARY ---")
        print(f"Bundle Version: {report['bundle']['version']}")
        print(f"Coordinate Frame: {report['bundle']['coordinate_frame']}")
        print(f"Units: {report['bundle']['units']}")
        print(f"Counts: Downloaded={report['counts']['downloaded']}, Parsed={report['counts']['parsed']}, Valid={report['counts']['valid']}, Rejected={report['counts']['rejected']}, Loaded={report['counts']['loaded']}, Duplicates Skipped={report['counts']['duplicates_skipped']}")
        if report["warnings"]:
            print("Warnings:")
            for w in report["warnings"]:
                print(f"  - {w}")
