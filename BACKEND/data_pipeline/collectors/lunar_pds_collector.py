import os
import hashlib
from typing import Dict, Any, Optional
import httpx


class LunarPDSCollector:
    """
    HTTP collector for NASA PDS lunar science products.
    Downloads files with streaming, computes SHA-256 and MD5 checksums,
    and returns metadata including download timestamps and byte sizes.
    """

    def __init__(self, target_dir: str = "storage/raw/lunar"):
        self.target_dir = os.path.abspath(target_dir)
        os.makedirs(self.target_dir, exist_ok=True)

    def download_file(
        self,
        url: str,
        filename: Optional[str] = None,
        max_size_bytes: int = 200 * 1024 * 1024,  # 200 MB threshold
        skip_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Download a file from an official NASA PDS URL.
        Enforces safety size limits and computes checksums.
        """
        if not filename:
            filename = url.rstrip("/").split("/")[-1]

        local_path = os.path.join(self.target_dir, filename)

        # Check existing file
        if skip_if_exists and os.path.exists(local_path):
            size = os.path.getsize(local_path)
            if size > 0:
                md5_hash, sha256_hash = self.compute_checksums(local_path)
                return {
                    "file_path": local_path,
                    "filename": filename,
                    "url": url,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "md5": md5_hash,
                    "sha256": sha256_hash,
                    "downloaded": False,
                }

        # Check header content-length first
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            head_resp = client.head(url)
            content_length = head_resp.headers.get("content-length")
            if content_length and int(content_length) > max_size_bytes:
                raise ValueError(
                    f"Remote file size {int(content_length)} bytes exceeds safety limit {max_size_bytes} bytes (~200 MB). "
                    "Manual approval required before download."
                )

            with client.stream("GET", url) as response:
                response.raise_for_status()
                total_bytes = 0
                md5 = hashlib.md5()
                sha256 = hashlib.sha256()

                with open(local_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=65536):
                        total_bytes += len(chunk)
                        if total_bytes > max_size_bytes:
                            f.close()
                            if os.path.exists(local_path):
                                os.remove(local_path)
                            raise ValueError(
                                f"Downloaded stream exceeded safety limit of {max_size_bytes} bytes (~200 MB)."
                            )
                        f.write(chunk)
                        md5.update(chunk)
                        sha256.update(chunk)

        size = os.path.getsize(local_path)
        return {
            "file_path": local_path,
            "filename": filename,
            "url": url,
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2),
            "md5": md5.hexdigest(),
            "sha256": sha256.hexdigest(),
            "downloaded": True,
        }

    @staticmethod
    def compute_checksums(file_path: str) -> tuple[str, str]:
        """Compute MD5 and SHA-256 for a local file."""
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()
