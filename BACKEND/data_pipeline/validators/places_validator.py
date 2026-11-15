from typing import Dict, Any, List, Tuple

class PlacesValidator:
    def __init__(self):
        pass

    def validate_row(self, row: Dict[str, Any], index: int) -> Tuple[bool, str]:
        """Validate a single parsed record."""
        # Check frame type
        frame = str(row.get("frame", "")).strip().upper()
        if frame not in ("SITE", "ROVER"):
            return False, f"Row {index}: Invalid frame '{frame}', must be 'SITE' or 'ROVER'"

        # Check required coordinate values
        try:
            lat = float(row.get("planetocentric_latitude"))
        except (ValueError, TypeError):
            return False, f"Row {index}: Missing or non-numeric planetocentric_latitude"

        try:
            lon = float(row.get("longitude"))
        except (ValueError, TypeError):
            return False, f"Row {index}: Missing or non-numeric longitude"

        # Check latitude range
        if not (-90.0 <= lat <= 90.0):
            return False, f"Row {index}: planetocentric_latitude {lat} out of range [-90, 90]"

        # Check longitude range (East-positive, standard Mars 0-360)
        if not (-180.0 <= lon <= 360.0):
            return False, f"Row {index}: longitude {lon} out of range [-180, 360]"

        # Check landing site coordinates if present
        for coord_name in ("landing_x", "landing_y", "landing_z"):
            val = row.get(coord_name)
            if val is not None and str(val).strip() != "":
                try:
                    float(val)
                except ValueError:
                    return False, f"Row {index}: {coord_name} is non-numeric: {val}"

        # Check northing and easting if present
        for coord_name in ("northing", "easting"):
            val = row.get(coord_name)
            if val is not None and str(val).strip() != "":
                try:
                    float(val)
                except ValueError:
                    return False, f"Row {index}: {coord_name} is non-numeric: {val}"

        return True, "Valid"

    def validate_batch(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate a list of records. Returns (valid_records, rejected_records)."""
        valid: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for idx, row in enumerate(records):
            is_valid, reason = self.validate_row(row, idx)
            if is_valid:
                valid.append(row)
            else:
                rejected.append({
                    "row_index": idx,
                    "record": row,
                    "reason": reason,
                })

        return valid, rejected
