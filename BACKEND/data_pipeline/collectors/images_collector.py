import os
import json
import hashlib
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

MARS_RAW_FEED_BASE = "https://mars.nasa.gov/rss/api/?feed=raw_images&feedtype=json"

ROVER_CATEGORY_MAP = {
    "perseverance": "mars2020",
    "mars-2020": "mars2020",
    "curiosity": "msl",
    "msl": "msl",
}

# Sol milestones for wide temporal spread
SPREAD_SOLS = [10, 50, 100, 250, 500, 750, 1000, 1500, 2000]


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class ImagesCollector:
    """
    Collects raw camera image metadata from official NASA Mars rover image feeds.
    Configured via NASA_API_KEY env (falls back to DEMO_KEY, never logged).
    """

    def __init__(self, storage_dir: str = "storage/raw/images"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        raw_key = os.getenv("NASA_API_KEY", "").strip()
        if not raw_key:
            # Fallback to DEMO_KEY and warn about public rate limits without logging key
            print("[ImagesCollector Warning] NASA_API_KEY is not set in environment. Falling back to DEMO_KEY (subject to standard NASA public rate limits).")
            self.api_key = "DEMO_KEY"
        else:
            self.api_key = raw_key

    def collect_rover_images(self, rover: str = "perseverance", limit: int = 100) -> Dict[str, Any]:
        """
        Collect up to `limit` images spread across multiple sols and instruments.
        Saves combined raw JSON to storage and returns metadata with checksum.
        """
        category = ROVER_CATEGORY_MAP.get(rover.lower(), "mars2020")
        collected_images: List[Dict[str, Any]] = []
        seen_ids = set()

        # Query spread sols
        per_sol_limit = max(5, limit // len(SPREAD_SOLS) + 5)
        for sol in SPREAD_SOLS:
            if len(collected_images) >= limit:
                break
            url = f"{MARS_RAW_FEED_BASE}&category={category}&num={per_sol_limit}&page=0&sol={sol}"
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SpaceExplorer-NASA-LandingNavigator/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("images", [])
                    for item in items:
                        img_id = item.get("imageid") or item.get("id")
                        if img_id and img_id not in seen_ids:
                            seen_ids.add(img_id)
                            collected_images.append(item)
                            if len(collected_images) >= limit:
                                break
            except Exception as e:
                print(f"[ImagesCollector] Note: sol={sol} fetch skipped or unavailable ({e})")
                continue

        # If not enough images collected from spread sols, fetch from recent stream
        if len(collected_images) < limit:
            remaining = limit - len(collected_images)
            url = f"{MARS_RAW_FEED_BASE}&category={category}&num={min(remaining + 20, 100)}&page=0"
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SpaceExplorer-NASA-LandingNavigator/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("images", [])
                    for item in items:
                        img_id = item.get("imageid") or item.get("id")
                        if img_id and img_id not in seen_ids:
                            seen_ids.add(img_id)
                            collected_images.append(item)
                            if len(collected_images) >= limit:
                                break
            except Exception as e:
                print(f"[ImagesCollector] Recent feed fetch note: {e}")

        # Save to disk
        out_filename = f"{rover.lower()}_raw_images.json"
        out_path = os.path.join(self.storage_dir, out_filename)
        payload = {
            "rover": rover,
            "category": category,
            "source_url": f"https://mars.nasa.gov/{category}/multimedia/raw-images/",
            "collected_count": len(collected_images),
            "images": collected_images,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        checksum = compute_sha256(out_path)
        return {
            "dest_path": out_path,
            "count": len(collected_images),
            "checksum": checksum,
            "source_url": payload["source_url"],
            "raw_payload": payload,
        }
