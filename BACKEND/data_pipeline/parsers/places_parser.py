import os
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple

try:
    import pds4_tools
except ImportError:
    pds4_tools = None

PLACES_STRUCTURED_COORDINATE_FRAME = (
    "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
    "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
    "Mars body-fixed frame name not stated in the label."
)

class PlacesParser:
    def __init__(self, xml_label_path: str, csv_path: str = None):
        self.xml_label_path = xml_label_path
        self.csv_path = csv_path or xml_label_path.replace(".xml", "")
        self.metadata: Dict[str, Any] = {}

    def parse_label(self) -> Dict[str, Any]:
        """Parse PDS4 XML label to extract product metadata and field definitions."""
        if not os.path.exists(self.xml_label_path):
            raise FileNotFoundError(f"Label file not found: {self.xml_label_path}")

        tree = ET.parse(self.xml_label_path)
        root = tree.getroot()

        # Helper to find tag ignoring namespace
        def find_text_any(parent, tag_name: str, default: str = None) -> str:
            for elem in parent.iter():
                if elem.tag.split("}")[-1] == tag_name:
                    return elem.text.strip() if elem.text else default
            return default

        logical_id = find_text_any(root, "logical_identifier", "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv")
        version_id = find_text_any(root, "version_id", "16.0")
        title = find_text_any(root, "title", "Mars 2020 Rover PLACES")
        start_time = find_text_any(root, "start_date_time", None)
        stop_time = find_text_any(root, "stop_date_time", None)

        # Coordinate frame from Geometry_Lander
        geom_state = find_text_any(root, "geometry_state", "Telemetry")
        geom_desc = find_text_any(root, "description", "Geometry as reported by the spacecraft in telemetry")
        geom_id = find_text_any(root, "local_identifier", "geom_telemetry_state")

        # Fields metadata
        fields = []
        for elem in root.iter():
            if elem.tag.split("}")[-1] == "Field_Delimited":
                name = find_text_any(elem, "name", "")
                data_type = find_text_any(elem, "data_type", "")
                unit = find_text_any(elem, "unit", None)
                desc = find_text_any(elem, "description", "")
                fields.append({
                    "name": name,
                    "data_type": data_type,
                    "unit": unit,
                    "description": desc,
                })

        self.metadata = {
            "logical_identifier": logical_id,
            "version_id": version_id,
            "title": title,
            "start_time": start_time,
            "stop_time": stop_time,
            "coordinate_frame": PLACES_STRUCTURED_COORDINATE_FRAME,
            "coordinate_description": geom_desc,
            "geometry_state": geom_state,
            "units": "deg, m",
            "fields": fields,
        }
        return self.metadata

    def parse_data(self, limit: int = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse table data either via pds4_tools or direct CSV reading guided by label."""
        if not self.metadata:
            self.parse_label()

        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Data file not found: {self.csv_path}")

        records: List[Dict[str, Any]] = []

        # Try pds4_tools first if available
        parsed_via_pds4 = False
        if pds4_tools is not None:
            try:
                structures = pds4_tools.read(self.xml_label_path, quiet=True)
                table = structures[0]
                col_names = table.fields()
                for i in range(len(table)):
                    if limit is not None and i >= limit:
                        break
                    row = {col: table[col][i] for col in col_names}
                    records.append(row)
                parsed_via_pds4 = True
            except Exception:
                parsed_via_pds4 = False

        if not parsed_via_pds4:
            # Fallback to standard CSV parser
            with open(self.csv_path, mode="r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit is not None and i >= limit:
                        break
                    records.append(row)

        return self.metadata, records
