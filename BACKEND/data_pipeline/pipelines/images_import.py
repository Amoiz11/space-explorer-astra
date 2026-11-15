import os
import sys
import json
import argparse
import datetime
from typing import Dict, Any

from backend.app.database.session import SessionLocal
from backend.app.database.init_db import init_database
from data_pipeline.collectors.images_collector import ImagesCollector
from data_pipeline.parsers.images_parser import ImagesParser
from data_pipeline.validators.images_validator import ImagesValidator
from data_pipeline.loaders.images_loader import ImagesLoader


def run_images_import(rover: str = "perseverance", limit: int = 100) -> Dict[str, Any]:
    """
    Executes end-to-end import pipeline for NASA rover images.
    Collects, parses, validates, and loads real rover image metadata with provenance.
    """
    init_database()

    reports_dir = os.path.join("storage", "processed", "import_reports")
    os.makedirs(reports_dir, exist_ok=True)

    print(f"\n[Images Pipeline] Starting import for rover: {rover} (limit: {limit})...")

    # 1. Collection
    collector = ImagesCollector()
    collect_res = collector.collect_rover_images(rover=rover, limit=limit)
    raw_path = collect_res["dest_path"]
    fetched_count = collect_res["count"]
    raw_checksum = collect_res["checksum"]
    print(f"[Images Pipeline] Collected {fetched_count} images (checksum: {raw_checksum[:12]}...).")

    # 2. Parsing
    parser = ImagesParser(raw_json_path=raw_path)
    parsed_records = parser.parse_data(collect_res["raw_payload"])
    print(f"[Images Pipeline] Parsed {len(parsed_records)} image records.")

    # 3. Validation
    validator = ImagesValidator()
    valid_records, rejected_records = validator.validate_batch(parsed_records)
    valid_count = len(valid_records)
    rejected_count = len(rejected_records)
    print(f"[Images Pipeline] Validation complete: {valid_count} valid, {rejected_count} rejected.")

    # 4. Loading
    db = SessionLocal()
    try:
        loader = ImagesLoader(db)
        load_res = loader.load_images(valid_records, rover_id=rover)
    finally:
        db.close()

    loaded_count = load_res["loaded"]
    skipped_duplicates = load_res["duplicates_skipped"]
    cameras_found = load_res["cameras_found"]
    sol_min = load_res["sol_min"]
    sol_max = load_res["sol_max"]

    print(f"[Images Pipeline] Load complete: {loaded_count} loaded, {skipped_duplicates} duplicates skipped.")
    print(f"[Images Pipeline] Cameras found: {', '.join(cameras_found)}")
    print(f"[Images Pipeline] Sol range: {sol_min} to {sol_max}")

    # 5. Report
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report = {
        "pipeline": "images_import",
        "rover": rover,
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "counts": {
            "fetched": fetched_count,
            "parsed": len(parsed_records),
            "valid": valid_count,
            "rejected": rejected_count,
            "loaded": loaded_count,
            "duplicates_skipped": skipped_duplicates,
        },
        "coverage": {
            "cameras": cameras_found,
            "camera_count": len(cameras_found),
            "sol_min": sol_min,
            "sol_max": sol_max,
        },
        "provenance": {
            "source_url": collect_res["source_url"],
            "raw_file": raw_path,
            "raw_sha256": raw_checksum,
            "label": "Verified",
        },
        "rejected_sample": rejected_records[:10] if rejected_records else [],
    }

    report_filename = f"images_import_{rover}_{timestamp}.json"
    report_path = os.path.join(reports_dir, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[Images Pipeline] Import report written to: {report_path}\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import real NASA Mars rover images into database.")
    parser.add_argument("--rover", type=str, default="perseverance", help="Rover ID (e.g. perseverance, curiosity)")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of images to import")
    args = parser.parse_args()

    run_images_import(rover=args.rover, limit=args.limit)
