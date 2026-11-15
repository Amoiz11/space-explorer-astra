import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class ImagesParser:
    """
    Parses NASA Mars rover raw image feed JSON into structured dictionaries.
    """

    def __init__(self, raw_json_path: Optional[str] = None):
        self.raw_json_path = raw_json_path

    def parse_data(self, raw_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if raw_dict is None:
            if not self.raw_json_path:
                raise ValueError("Must provide either raw_json_path or raw_dict")
            with open(self.raw_json_path, "r", encoding="utf-8") as f:
                raw_dict = json.load(f)

        raw_items = raw_dict.get("images", [])
        parsed_records: List[Dict[str, Any]] = []

        for item in raw_items:
            img_id = item.get("imageid") or item.get("id")
            if not img_id:
                continue

            # Extract image URL from image_files dictionary
            files = item.get("image_files") or {}
            img_url = (
                files.get("medium")
                or files.get("large")
                or files.get("full_res")
                or files.get("small")
                or item.get("img_src")  # api.nasa.gov format if applicable
            )

            # Camera name
            cam_obj = item.get("camera")
            if isinstance(cam_obj, dict):
                camera_name = cam_obj.get("instrument") or cam_obj.get("name") or "UNKNOWN_CAMERA"
            elif isinstance(cam_obj, str):
                camera_name = cam_obj
            else:
                camera_name = "UNKNOWN_CAMERA"

            # Date captured (UTC)
            date_utc_str = item.get("date_taken_utc") or item.get("earth_date")
            captured_at = None
            if date_utc_str:
                try:
                    # e.g. 2026-11-06T12:16:25.848 or 2026-11-06
                    captured_at = datetime.fromisoformat(date_utc_str.replace("Z", "+00:00"))
                except Exception:
                    try:
                        captured_at = datetime.strptime(date_utc_str[:19], "%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        captured_at = None

            # Sol
            sol_raw = item.get("sol")
            try:
                sol_val = int(sol_raw) if sol_raw is not None else None
            except (ValueError, TypeError):
                sol_val = None

            # Extended fields (sclk)
            extended = item.get("extended") or {}
            sclk_val = extended.get("sclk")

            record = {
                "id": str(img_id),
                "sol": sol_val,
                "captured_at": captured_at,
                "camera": str(camera_name).strip(),
                "image_url": str(img_url).strip() if img_url else None,
                "caption": item.get("caption"),
                "credit": item.get("credit", "NASA/JPL-Caltech"),
                "archive_url": item.get("link") or item.get("json_link"),
                "sclk": sclk_val,
            }
            parsed_records.append(record)

        return parsed_records
