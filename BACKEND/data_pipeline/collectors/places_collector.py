import os
import hashlib
import certifi
import httpx
from typing import Dict, Any, List

PLACES_BASE_URL = "https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_rover_places"

DEFAULT_FILES = [
    {
        "url": f"{PLACES_BASE_URL}/data_localizations/best_interp.csv",
        "relative_path": "places/best_interp.csv",
    },
    {
        "url": f"{PLACES_BASE_URL}/data_localizations/best_interp.csv.xml",
        "relative_path": "places/best_interp.csv.xml",
    },
    {
        "url": f"{PLACES_BASE_URL}/data_ancillary/sclk_table.csv",
        "relative_path": "places/sclk_table.csv",
    },
    {
        "url": f"{PLACES_BASE_URL}/data_ancillary/sclk_table.csv.xml",
        "relative_path": "places/sclk_table.csv.xml",
    },
]

def compute_sha256(filepath: str) -> str:
    """Compute sha256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class PlacesCollector:
    def __init__(self, storage_dir: str = "storage/raw"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def download_file(self, url: str, dest_path: str, max_retries: int = 2) -> Dict[str, Any]:
        """Download a file with retry outside sandbox."""
        full_dest = os.path.join(self.storage_dir, dest_path)
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)

        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(verify=certifi.where(), timeout=60.0) as client:
                    with client.stream("GET", url, headers={"User-Agent": "SpaceExplorer-Pipeline/1.0"}) as response:
                        if response.status_code != 200:
                            raise RuntimeError(f"HTTP {response.status_code} fetching {url}")
                        with open(full_dest, "wb") as f:
                            for chunk in response.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                checksum = compute_sha256(full_dest)
                file_size = os.path.getsize(full_dest)
                return {
                    "url": url,
                    "dest_path": full_dest,
                    "checksum": checksum,
                    "file_size": file_size,
                    "status": "downloaded",
                }
            except Exception as e:
                if attempt == max_retries:
                    raise RuntimeError(f"Failed to download {url} after {max_retries} attempts: {e}")

    def collect(self, files: List[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Collect all required PLACES archive files."""
        files_to_download = files or DEFAULT_FILES
        results = []
        for file_info in files_to_download:
            full_dest = os.path.join(self.storage_dir, file_info["relative_path"])
            if os.path.exists(full_dest) and os.path.getsize(full_dest) > 0:
                results.append({
                    "url": file_info["url"],
                    "dest_path": full_dest,
                    "checksum": compute_sha256(full_dest),
                    "file_size": os.path.getsize(full_dest),
                    "status": "cached",
                })
            else:
                res = self.download_file(file_info["url"], file_info["relative_path"])
                results.append(res)
        return results
