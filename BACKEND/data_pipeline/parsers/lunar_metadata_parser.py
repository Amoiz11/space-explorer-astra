import os
import re
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET


class LunarMetadataParser:
    """
    Parser for Lunar PDS3 (.lbl) and PDS4 (.xml) metadata labels.
    Extracts resolution, coverage, vertical reference, coordinate reference,
    units, version, and no-data value.
    Anything not stated in the label stays None with note 'not stated in label'.
    """

    NOT_STATED = "not stated in label"

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a label file (.lbl or .xml)."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if file_path.endswith(".xml") or content.strip().startswith("<?xml"):
            return self.parse_pds4_xml(content)
        return self.parse_pds3_label(content)

    def parse_pds3_label(self, label_text: str) -> Dict[str, Any]:
        """Parse a PDS3 .lbl text string."""
        data: Dict[str, Any] = {}

        # Strip comments /* ... */
        clean_text = re.sub(r"/\*.*?\*/", "", label_text, flags=re.DOTALL)

        # Parse key = value lines with support for leading whitespace and multiline values
        lines = clean_text.splitlines()
        current_key = None
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped == "END":
                break
            m = re.match(r"^\s*([A-Za-z0-9_:\^]+)\s*=\s*(.*)$", line)
            if m:
                current_key = m.group(1).strip()
                val = m.group(2).strip()
                data[current_key] = val
            elif current_key and line_stripped:
                data[current_key] += " " + line_stripped

        # Clean string values
        for k in list(data.keys()):
            data[k] = data[k].strip('"').strip("'")

        # Extract Version
        version = data.get("PRODUCT_VERSION_ID")
        if not version or version == "'N/A'":
            version = None

        # Extract Resolution
        map_scale = data.get("MAP_SCALE")
        resolution = None
        if map_scale:
            # e.g. "240 <m/pix>" -> "240 m/pixel"
            res_val = re.search(r"([\d.]+)", map_scale)
            if res_val:
                resolution = f"{res_val.group(1)} m/pixel"
        if not resolution:
            resolution = None

        # Extract Coverage
        min_lat_raw = data.get("MINIMUM_LATITUDE")
        max_lat_raw = data.get("MAXIMUM_LATITUDE")
        west_lon_raw = data.get("WESTERNMOST_LONGITUDE")
        east_lon_raw = data.get("EASTERNMOST_LONGITUDE")

        def _parse_float_or_null(val: Optional[str]) -> Optional[float]:
            if not val or "N/A" in val.upper() or "NULL" in val.upper():
                return None
            m = re.search(r"([+-]?[\d.]+)", val)
            return float(m.group(1)) if m else None

        min_lat = _parse_float_or_null(min_lat_raw)
        max_lat = _parse_float_or_null(max_lat_raw)
        west_lon = _parse_float_or_null(west_lon_raw)
        east_lon = _parse_float_or_null(east_lon_raw)

        coverage = {
            "south_latitude": min_lat if min_lat is not None else self.NOT_STATED,
            "north_latitude": max_lat if max_lat is not None else self.NOT_STATED,
            "west_longitude": west_lon if west_lon is not None else self.NOT_STATED,
            "east_longitude": east_lon if east_lon is not None else self.NOT_STATED,
        }

        # Extract Vertical Reference
        offset = data.get("OFFSET")
        a_axis = data.get("A_AXIS_RADIUS")
        v_ref_parts = []
        if a_axis and "N/A" not in a_axis:
            v_ref_parts.append(f"Reference sphere radius: {a_axis.strip()}")
        if offset and "N/A" not in offset:
            v_ref_parts.append(f"OFFSET = {offset.strip()} m")
        if v_ref_parts:
            vertical_reference = "; ".join(v_ref_parts) + "; elevation in meters relative to reference sphere"
        else:
            vertical_reference = None

        # Extract Coordinate Reference / Projection (never assume EPSG:4326)
        proj_type = data.get("MAP_PROJECTION_TYPE")
        coord_sys_name = data.get("COORDINATE_SYSTEM_NAME")
        coord_sys_type = data.get("COORDINATE_SYSTEM_TYPE")
        lat_type = data.get("KEYWORD_LATITUDE_TYPE")
        lon_dir = data.get("POSITIVE_LONGITUDE_DIRECTION")

        coord_parts = []
        if proj_type and "N/A" not in proj_type:
            coord_parts.append(f"Projection: {proj_type}")
        if coord_sys_name and "N/A" not in coord_sys_name:
            coord_parts.append(f"Coordinate System: {coord_sys_name}")
        elif coord_sys_type and "N/A" not in coord_sys_type:
            coord_parts.append(f"Coordinate System Type: {coord_sys_type}")
        if lat_type and "N/A" not in lat_type:
            coord_parts.append(f"Latitude: {lat_type}")
        if lon_dir and "N/A" not in lon_dir:
            coord_parts.append(f"Longitude Direction: Positive {lon_dir}")

        if coord_parts:
            coordinate_reference_note = "; ".join(coord_parts)
        else:
            coordinate_reference_note = self.NOT_STATED

        # Units
        unit = data.get("UNIT")
        if unit and "N/A" not in unit:
            units = unit.strip()
        else:
            units = self.NOT_STATED

        # No-data value (check NULL, INVALID_CONSTANT, NO_DATA)
        no_data = None
        for key in ["NULL_VALUE", "INVALID_CONSTANT", "SPECIAL_CONSTANT", "NULL", "NO_DATA_VALUE", "MISSING_CONSTANT"]:
            if key in data and "N/A" not in data[key]:
                no_data = data[key]
                break

        product_id = data.get("PRODUCT_ID") or data.get("FILE_NAME")
        dataset_id = data.get("DATA_SET_ID")

        return {
            "file_name": data.get("FILE_NAME"),
            "dataset_id": dataset_id,
            "product_id": product_id,
            "version": version if version else self.NOT_STATED,
            "resolution": resolution if resolution else self.NOT_STATED,
            "coverage": coverage,
            "vertical_reference": vertical_reference if vertical_reference else self.NOT_STATED,
            "coordinate_reference_note": coordinate_reference_note,
            "units": units,
            "no_data_value": no_data if no_data else None,
            "no_data_note": "not stated in label" if no_data is None else None,
            "raw_fields": data,
        }

    def parse_pds4_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse PDS4 XML label."""
        root = ET.fromstring(xml_text)
        ns = {
            "pds": "http://pds.nasa.gov/pds4/pds/v1",
            "cart": "http://pds.nasa.gov/pds4/cart/v1",
            "disp": "http://pds.nasa.gov/pds4/disp/v1",
            "lro": "http://pds.nasa.gov/pds4/mission/lro/v1",
        }

        # Logical Identifier & Version
        lid_elem = root.find(".//pds:logical_identifier", ns)
        lid = lid_elem.text.strip() if lid_elem is not None and lid_elem.text else None

        ver_elem = root.find(".//pds:version_id", ns)
        version = ver_elem.text.strip() if ver_elem is not None and ver_elem.text else None

        # Product Version ID in LRO area if present
        lro_ver_elem = root.find(".//lro:product_version_id", ns)
        if lro_ver_elem is not None and lro_ver_elem.text:
            version = lro_ver_elem.text.strip()

        # Resolution
        res_elem = root.find(".//cart:pixel_resolution_x", ns)
        resolution = None
        if res_elem is not None and res_elem.text:
            unit = res_elem.attrib.get("unit", "m/pixel")
            resolution = f"{res_elem.text.strip()} {unit}"

        # Coverage
        w_elem = root.find(".//cart:west_bounding_coordinate", ns)
        e_elem = root.find(".//cart:east_bounding_coordinate", ns)
        n_elem = root.find(".//cart:north_bounding_coordinate", ns)
        s_elem = root.find(".//cart:south_bounding_coordinate", ns)

        def _to_float(el):
            return float(el.text.strip()) if el is not None and el.text else None

        coverage = {
            "south_latitude": _to_float(s_elem) if s_elem is not None else self.NOT_STATED,
            "north_latitude": _to_float(n_elem) if n_elem is not None else self.NOT_STATED,
            "west_longitude": _to_float(w_elem) if w_elem is not None else self.NOT_STATED,
            "east_longitude": _to_float(e_elem) if e_elem is not None else self.NOT_STATED,
        }

        # Vertical reference
        offset_elem = root.find(".//pds:value_offset", ns)
        a_elem = root.find(".//cart:a_axis_radius", ns)
        v_parts = []
        if a_elem is not None and a_elem.text:
            v_parts.append(f"Reference sphere radius: {a_elem.text.strip()} {a_elem.attrib.get('unit', 'km')}")
        if offset_elem is not None and offset_elem.text:
            v_parts.append(f"OFFSET = {offset_elem.text.strip()} {offset_elem.attrib.get('unit', 'm')}")
        vertical_reference = "; ".join(v_parts) if v_parts else None

        # Coordinate reference
        proj_elem = root.find(".//cart:map_projection_name", ns)
        cs_elem = root.find(".//cart:coordinate_system_name", ns)
        cs_type = root.find(".//cart:coordinate_system_type", ns)
        lat_elem = root.find(".//cart:latitude_type", ns)
        lon_elem = root.find(".//cart:longitude_direction", ns)

        c_parts = []
        if proj_elem is not None and proj_elem.text:
            c_parts.append(f"Projection: {proj_elem.text.strip()}")
        if cs_elem is not None and cs_elem.text:
            c_parts.append(f"Coordinate System: {cs_elem.text.strip()}")
        elif cs_type is not None and cs_type.text:
            c_parts.append(f"Coordinate System Type: {cs_type.text.strip()}")
        if lat_elem is not None and lat_elem.text:
            c_parts.append(f"Latitude: {lat_elem.text.strip()}")
        if lon_elem is not None and lon_elem.text:
            c_parts.append(f"Longitude Direction: {lon_elem.text.strip()}")
        coordinate_reference_note = "; ".join(c_parts) if c_parts else self.NOT_STATED

        # Units
        unit_elem = root.find(".//pds:unit", ns)
        units = unit_elem.text.strip() if unit_elem is not None and unit_elem.text else self.NOT_STATED

        # No-data value
        no_data = None
        special_const = root.find(".//pds:Special_Constants", ns)
        if special_const is not None:
            for child in special_const:
                if "missing" in child.tag.lower() or "null" in child.tag.lower() or "invalid" in child.tag.lower():
                    no_data = child.text.strip() if child.text else None
                    break

        return {
            "logical_identifier": lid,
            "version": version if version else self.NOT_STATED,
            "resolution": resolution if resolution else self.NOT_STATED,
            "coverage": coverage,
            "vertical_reference": vertical_reference if vertical_reference else self.NOT_STATED,
            "coordinate_reference_note": coordinate_reference_note,
            "units": units,
            "no_data_value": no_data,
            "no_data_note": "not stated in label" if no_data is None else None,
        }
