import re
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple

ALLOWED_NASA_DOMAINS = [
    "mars.nasa.gov",
    "nasa.gov",
    "jpl.nasa.gov",
    "photojournal.jpl.nasa.gov",
]


class ImagesValidator:
    """
    Validates parsed rover image metadata records.
    Ensures secure HTTPS URLs from official NASA domains and complete temporal metadata.
    """

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        # 1. Identifier
        img_id = record.get("id")
        if not img_id or not str(img_id).strip():
            errors.append("Missing or empty image identifier (id)")

        # 2. Image URL
        img_url = record.get("image_url")
        if not img_url:
            errors.append("Missing image_url")
        else:
            parsed = urlparse(img_url)
            if parsed.scheme.lower() != "https":
                errors.append(f"Insecure URL scheme '{parsed.scheme}'; must be https")
            domain_match = any(parsed.netloc.lower() == d or parsed.netloc.lower().endswith("." + d) for d in ALLOWED_NASA_DOMAINS)
            if not domain_match:
                errors.append(f"Image host '{parsed.netloc}' is not an approved NASA domain")

        # 3. Captured datetime
        captured_at = record.get("captured_at")
        if captured_at is None:
            errors.append("Missing or invalid captured_at timestamp")

        # 4. Camera
        camera = record.get("camera")
        if not camera or not str(camera).strip():
            errors.append("Missing or empty camera instrument name")

        # 5. Sol (if present, must be non-negative)
        sol = record.get("sol")
        if sol is not None and sol < 0:
            errors.append(f"Invalid negative sol value: {sol}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_batch(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        valid: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for r in records:
            ok, errs = self.validate_record(r)
            if ok:
                valid.append(r)
            else:
                rejected.append({"record": r, "reasons": errs})

        return valid, rejected
