import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

MARS_COORDINATE_REFERENCE_NOTE = (
    "Mars planetocentric lat/lon, east-positive, body-fixed frame name not stated in the label."
)

MOON_COORDINATE_REFERENCE_NOTE = (
    "Moon lunar polar coordinates (MOON_ME_DE421). Frame is not an Earth coordinate system."
)


def _get_val(field: Any) -> Any:
    """Helper to unwrap nested {'value': x, 'units': y} or return bare value."""
    if isinstance(field, dict) and "value" in field:
        return field.get("value")
    return field


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def generate_lunar_ellipse_polygon(
    lat_deg: float,
    lon_deg: float,
    radius_m: float = 1000.0,
    semi_major_m: Optional[float] = None,
    semi_minor_m: Optional[float] = None,
    orientation_deg: Optional[float] = None,
    n_points: int = 36,
) -> List[List[float]]:
    """
    Generate polygon coordinates [lon, lat] for a circular or elliptical landing footprint
    on the lunar sphere (radius 1737.4 km).
    Orientation is clockwise in degrees from North toward East.
    Returns closed ring of [lon, lat] pairs.
    """
    import math
    R = 1737400.0
    a = float(semi_major_m if semi_major_m is not None else radius_m)
    b = float(semi_minor_m if semi_minor_m is not None else radius_m)
    orient = float(orientation_deg if orientation_deg is not None else 0.0)
    orient_rad = math.radians(orient)

    lat0_rad = math.radians(lat_deg)
    lon0_rad = math.radians(lon_deg)

    ring: List[List[float]] = []
    for i in range(n_points):
        theta = 2.0 * math.pi * i / n_points
        u = a * math.cos(theta)
        v = b * math.sin(theta)

        dN = u * math.cos(orient_rad) - v * math.sin(orient_rad)
        dE = u * math.sin(orient_rad) + v * math.cos(orient_rad)

        dist = math.hypot(dE, dN)
        if dist < 1e-6:
            ring.append([round(lon_deg, 6), round(lat_deg, 6)])
            continue

        az_rad = math.atan2(dE, dN)
        delta = dist / R

        sin_lat = math.sin(lat0_rad) * math.cos(delta) + math.cos(lat0_rad) * math.sin(delta) * math.cos(az_rad)
        sin_lat = max(-1.0, min(1.0, sin_lat))
        lat_pt = math.asin(sin_lat)

        y = math.sin(az_rad) * math.sin(delta) * math.cos(lat0_rad)
        x = math.cos(delta) - math.sin(lat0_rad) * math.sin(lat_pt)
        dlon = math.atan2(y, x)
        lon_pt = lon0_rad + dlon

        lon_out = (math.degrees(lon_pt) + 180.0) % 360.0 - 180.0
        lat_out = math.degrees(lat_pt)
        ring.append([round(lon_out, 6), round(lat_out, 6)])

    if ring:
        ring.append(ring[0])
    return ring


def _fetch_site_stored_metrics(
    site_id: str, db: Optional[Any] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Fetch last stored slope, illumination, and earth visibility metrics for site."""
    if db is None:
        return None, None, None
    try:
        from backend.app.models.models import TerrainMetrics, IlluminationResult, EarthVisibilityWindow

        tm = (
            db.query(TerrainMetrics)
            .filter(TerrainMetrics.site_id == site_id)
            .order_by(TerrainMetrics.id.desc())
            .first()
        )
        slope_m = None
        if tm:
            slope_m = {
                "mean_slope_deg": tm.mean_slope,
                "max_slope_deg": tm.max_slope,
                "elevation_stats": tm.elevation_stats,
            }

        ir = (
            db.query(IlluminationResult)
            .filter(IlluminationResult.site_id == site_id)
            .order_by(IlluminationResult.id.desc())
            .first()
        )
        illum_m = None
        if ir:
            illum_m = {
                "parameters": ir.parameters,
                "sun_azimuth_deg": ir.sun_azimuth,
                "sun_elevation_deg": ir.sun_elevation,
                "illuminated_fraction": ir.illuminated_fraction,
            }

        ev = (
            db.query(EarthVisibilityWindow)
            .filter(EarthVisibilityWindow.site_id == site_id)
            .order_by(EarthVisibilityWindow.id.desc())
            .first()
        )
        earth_m = None
        if ev:
            earth_m = {
                "parameters": ev.parameters,
                "earth_azimuth_deg": ev.earth_azimuth,
                "earth_elevation_deg": ev.earth_elevation,
                "obstruction_status": ev.obstruction_status,
            }
        return slope_m, illum_m, earth_m
    except Exception:
        return None, None, None


class GeoJSONExporter:
    """
    Exports planetary explorer locations, traversed routes, and candidate sites
    as GeoJSON FeatureCollections conforming strictly to planetary frames (never EPSG:4326).
    """

    @staticmethod
    def extract_location_coordinates(loc: Any) -> Optional[Tuple[float, float]]:
        """
        Extract (longitude, latitude) from a Location object or dict.
        Returns (lon, lat) tuple in GeoJSON order [longitude, latitude], or None if invalid.
        """
        oc = _get_attr(loc, "original_coordinates") or {}
        lat, lon = None, None

        # 1. Try 'values' list [lat, lon]
        values = oc.get("values")
        if isinstance(values, (list, tuple)) and len(values) >= 2:
            try:
                lat = float(_get_val(values[0]))
                lon = float(_get_val(values[1]))
            except (ValueError, TypeError):
                lat, lon = None, None

        # 2. Try planetocentric_latitude and longitude fields
        if lat is None or lon is None:
            p_lat = _get_val(oc.get("planetocentric_latitude"))
            p_lon = _get_val(oc.get("longitude"))
            try:
                lat = float(p_lat) if p_lat is not None else None
                lon = float(p_lon) if p_lon is not None else None
            except (ValueError, TypeError):
                lat, lon = None, None

        # 3. Validation: Mars/Moon lat in [-90, 90], lon in [-180, 360]
        if lat is None or lon is None:
            return None
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 360.0):
            return None

        return lon, lat

    @staticmethod
    def extract_sol(loc: Any) -> Optional[int]:
        oc = _get_attr(loc, "original_coordinates") or {}
        sol_val = _get_val(oc.get("sol"))
        if sol_val is not None:
            try:
                return int(sol_val)
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def extract_sclk(loc: Any) -> Optional[str]:
        oc = _get_attr(loc, "original_coordinates") or {}
        sclk_val = _get_val(oc.get("sclk"))
        return str(sclk_val) if sclk_val is not None else None

    @classmethod
    def export_locations_feature_collection(
        cls,
        locations: List[Any],
        explorer_id: str = "perseverance",
    ) -> Dict[str, Any]:
        """
        Export validated locations of an explorer as a GeoJSON FeatureCollection.
        Coordinates order is [longitude, latitude].
        Rows with sol == -1 are marked as feature_role: landing_site_reference.
        Interpolated points carry label: Estimated.
        """
        features: List[Dict[str, Any]] = []

        for loc in locations:
            coords = cls.extract_location_coordinates(loc)
            if coords is None:
                continue

            lon, lat = coords
            sol = cls.extract_sol(loc)
            sclk = cls.extract_sclk(loc)

            obs = _get_attr(loc, "observed_at")
            obs_str = obs.isoformat() if hasattr(obs, "isoformat") else (str(obs) if obs else None)

            pos_method = _get_attr(loc, "position_method") or "interpolated"
            label = _get_attr(loc, "label") or "Estimated"
            if pos_method == "interpolated":
                label = "Estimated"

            prod_id = _get_attr(loc, "product_id") or "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv"
            is_placeholder = bool(_get_attr(loc, "is_placeholder", False))
            coord_frame = (
                _get_attr(loc, "coordinate_frame")
                or "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. Mars body-fixed frame name not stated in the label."
            )

            oc = _get_attr(loc, "original_coordinates") or {}
            units = oc.get("units") or "deg"

            # Placeholder rows get feature_role "placeholder" and are never treated
            # as a landing site reference regardless of their sol value.
            if is_placeholder:
                feature_role = "placeholder"
            elif sol == -1:
                feature_role = "landing_site_reference"
            else:
                feature_role = "drive_point"

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "explorer_id": _get_attr(loc, "explorer_id", explorer_id),
                    "sol": sol,
                    "sclk": sclk,
                    "observed_at": obs_str,
                    "label": label,
                    "position_method": pos_method,
                    "source_product_id": prod_id,
                    "is_placeholder": is_placeholder,
                    "coordinate_frame": coord_frame,
                    "units": units,
                    "feature_role": feature_role,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "properties": {
                "coordinate_reference_note": MARS_COORDINATE_REFERENCE_NOTE,
                "explorer_id": explorer_id,
                "layer": "historical-positions",
                "total_features": len(features),
            },
            "coordinate_reference_note": MARS_COORDINATE_REFERENCE_NOTE,
            "features": features,
        }

    @classmethod
    def export_traversed_route_feature_collection(
        cls,
        locations: List[Any],
        explorer_id: str = "perseverance",
    ) -> Dict[str, Any]:
        """
        Export traversed route as a GeoJSON FeatureCollection.
        The traversed route line (LineString) contains supported segments (sol >= 0).
        Rows with sol == -1 (landing site reference) are excluded from the traversed route line
        and exported as a separate Point feature with feature_role: landing_site_reference.
        """
        features: List[Dict[str, Any]] = []
        drive_coords: List[List[float]] = []
        landing_feature: Optional[Dict[str, Any]] = None

        common_prod_id = "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv"
        common_coord_frame = (
            "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
            "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
            "Mars body-fixed frame name not stated in the label."
        )
        is_placeholder_route = False

        for loc in locations:
            coords = cls.extract_location_coordinates(loc)
            if coords is None:
                continue

            lon, lat = coords
            sol = cls.extract_sol(loc)
            sclk = cls.extract_sclk(loc)
            prod_id = _get_attr(loc, "product_id") or common_prod_id
            common_prod_id = prod_id
            coord_frame = _get_attr(loc, "coordinate_frame") or common_coord_frame
            common_coord_frame = coord_frame
            is_placeholder_loc = bool(_get_attr(loc, "is_placeholder", False))
            if is_placeholder_loc:
                is_placeholder_route = True

            # Placeholder rows are skipped entirely from the route (neither line nor landing ref)
            if is_placeholder_loc:
                continue

            if sol == -1:
                # Real non-placeholder landing site reference: separate Point feature
                obs = _get_attr(loc, "observed_at")
                obs_str = obs.isoformat() if hasattr(obs, "isoformat") else (str(obs) if obs else None)
                landing_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                    "properties": {
                        "explorer_id": _get_attr(loc, "explorer_id", explorer_id),
                        "sol": -1,
                        "sclk": sclk,
                        "observed_at": obs_str,
                        "label": "Estimated",
                        "position_method": "interpolated",
                        "source_product_id": prod_id,
                        "is_placeholder": False,
                        "coordinate_frame": coord_frame,
                        "units": "deg",
                        "feature_role": "landing_site_reference",
                    },
                }
            else:
                # Real non-placeholder drive point on traversed route
                drive_coords.append([lon, lat])

        # If we have a landing site reference, add it as a separate feature
        if landing_feature:
            features.append(landing_feature)

        # Build LineString feature for traversed route line if drive points exist
        if drive_coords:
            route_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": drive_coords,
                },
                "properties": {
                    "explorer_id": explorer_id,
                    "feature_role": "traversed_route",
                    "label": "Estimated",
                    "position_method": "interpolated",
                    "source_product_id": common_prod_id,
                    "is_placeholder": is_placeholder_route,
                    "coordinate_frame": common_coord_frame,
                    "units": "deg",
                    "point_count": len(drive_coords),
                },
            }
            features.append(route_feature)

        return {
            "type": "FeatureCollection",
            "properties": {
                "coordinate_reference_note": MARS_COORDINATE_REFERENCE_NOTE,
                "explorer_id": explorer_id,
                "layer": "traversed-route",
                "total_features": len(features),
                "drive_points_in_line": len(drive_coords),
            },
            "coordinate_reference_note": MARS_COORDINATE_REFERENCE_NOTE,
            "features": features,
        }

    @classmethod
    def export_candidate_sites_feature_collection(
        cls,
        sites: List[Any],
        include_polygons: bool = False,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Export candidate lunar landing sites as a GeoJSON FeatureCollection.
        When include_polygons=True, generates a Point feature for the site location
        PLUS a Polygon feature for the analysis radius or landing ellipse.
        Preserves is_placeholder flags, MOON_ME_DE421 frame, and last stored metrics.
        """
        features: List[Dict[str, Any]] = []

        for site in sites:
            coords_data = _get_attr(site, "coordinates") or {}
            values = coords_data.get("values") if isinstance(coords_data, dict) else coords_data
            if not isinstance(values, (list, tuple)) or len(values) < 2:
                continue

            try:
                lat = float(values[0])
                lon = float(values[1])
            except (ValueError, TypeError):
                continue

            # Check polar/lunar range
            if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 360.0):
                continue

            site_id = _get_attr(site, "id")
            site_name = _get_attr(site, "name")
            is_placeholder = bool(_get_attr(site, "is_placeholder", True))
            frame = _get_attr(site, "frame") or "MOON_ME_DE421"
            radius_m = _get_attr(site, "analysis_radius_m", 1000.0) or 1000.0
            semi_major_m = _get_attr(site, "semi_major_m", None)
            semi_minor_m = _get_attr(site, "semi_minor_m", None)
            orientation_deg = _get_attr(site, "orientation_deg", None)

            slope_m, illum_m, earth_m = _fetch_site_stored_metrics(site_id, db=db)

            props = {
                "id": site_id,
                "name": site_name,
                "body_id": _get_attr(site, "body_id", "moon"),
                "frame": frame,
                "analysis_radius_m": radius_m,
                "semi_major_m": semi_major_m,
                "semi_minor_m": semi_minor_m,
                "orientation_deg": orientation_deg,
                "notes": _get_attr(site, "notes"),
                "label": "Unknown" if is_placeholder else "Verified",
                "is_placeholder": is_placeholder,
                "source_product_id": "urn:nasa:lunar:artemis:candidate_sites",
                "coordinate_frame": frame,
                "units": "deg",
                "feature_role": "candidate_landing_site",
                "slope_metrics": slope_m,
                "illumination_metrics": illum_m,
                "earth_visibility_metrics": earth_m,
            }

            # 1. Point feature (site location)
            point_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],  # GeoJSON order: [longitude, latitude]
                },
                "properties": dict(props, feature_role="candidate_landing_site"),
            }
            features.append(point_feature)

            # 2. Polygon feature (landing ellipse or circular footprint)
            if include_polygons:
                ring = generate_lunar_ellipse_polygon(
                    lat_deg=lat,
                    lon_deg=lon,
                    radius_m=radius_m,
                    semi_major_m=semi_major_m,
                    semi_minor_m=semi_minor_m,
                    orientation_deg=orientation_deg,
                )
                footprint_role = "landing_ellipse" if semi_major_m is not None else "analysis_radius"
                poly_props = dict(props, feature_role=footprint_role)
                poly_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [ring],
                    },
                    "properties": poly_props,
                }
                features.append(poly_feature)

        return {
            "type": "FeatureCollection",
            "properties": {
                "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
                "body_id": "moon",
                "layer": "candidate_sites",
                "total_features": len(features),
            },
            "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
            "features": features,
        }

    @classmethod
    def export_illumination_feature_collection(
        cls,
        sites: List[Any],
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Export per-site solar illumination summary as a GeoJSON FeatureCollection.
        Features represent candidate sites with stored illumination window totals and parameters.
        """
        features: List[Dict[str, Any]] = []

        for site in sites:
            coords_data = _get_attr(site, "coordinates") or {}
            values = coords_data.get("values") if isinstance(coords_data, dict) else coords_data
            if not isinstance(values, (list, tuple)) or len(values) < 2:
                continue

            try:
                lat = float(values[0])
                lon = float(values[1])
            except (ValueError, TypeError):
                continue

            site_id = _get_attr(site, "id")
            site_name = _get_attr(site, "name")
            is_placeholder = bool(_get_attr(site, "is_placeholder", True))
            frame = _get_attr(site, "frame") or "MOON_ME_DE421"

            latest_params = None
            window_count = 0
            total_lit_h = 0.0

            if db is not None:
                try:
                    from backend.app.models.models import IlluminationResult
                    recs = (
                        db.query(IlluminationResult)
                        .filter(IlluminationResult.site_id == site_id)
                        .order_by(IlluminationResult.id.asc())
                        .all()
                    )
                    if recs:
                        window_count = len(recs)
                        for r in recs:
                            if r.end_time and r.start_time:
                                total_lit_h += (r.end_time - r.start_time).total_seconds() / 3600.0
                        latest_params = recs[-1].parameters
                except Exception:
                    pass

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "id": site_id,
                    "name": site_name,
                    "is_placeholder": is_placeholder,
                    "coordinate_frame": frame,
                    "units": "deg",
                    "parameters": latest_params,
                    "window_totals": {
                        "window_count": window_count,
                        "total_lit_hours": round(total_lit_h, 2),
                    },
                    "feature_role": "site_illumination_summary",
                    "source_product_id": "lola-dem-75s-240m",
                    "label": "Modelled",
                    "disclaimer": (
                        "Terrain-aware solar illumination summary. Frame is MOON_ME_DE421, "
                        "planetocentric latitude, east-positive longitude. Not an Earth coordinate system. "
                        "Planning support tool, not safety certification."
                    ),
                },
            })

        return {
            "type": "FeatureCollection",
            "properties": {
                "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
                "body_id": "moon",
                "layer": "illumination",
                "total_features": len(features),
            },
            "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
            "features": features,
        }

    @classmethod
    def export_earth_visibility_feature_collection(
        cls,
        sites: List[Any],
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Export per-site Earth visibility summary as a GeoJSON FeatureCollection.
        Features represent candidate sites with stored Earth line-of-sight window totals and parameters.
        """
        features: List[Dict[str, Any]] = []

        for site in sites:
            coords_data = _get_attr(site, "coordinates") or {}
            values = coords_data.get("values") if isinstance(coords_data, dict) else coords_data
            if not isinstance(values, (list, tuple)) or len(values) < 2:
                continue

            try:
                lat = float(values[0])
                lon = float(values[1])
            except (ValueError, TypeError):
                continue

            site_id = _get_attr(site, "id")
            site_name = _get_attr(site, "name")
            is_placeholder = bool(_get_attr(site, "is_placeholder", True))
            frame = _get_attr(site, "frame") or "MOON_ME_DE421"

            latest_params = None
            window_count = 0
            total_vis_h = 0.0

            if db is not None:
                try:
                    from backend.app.models.models import EarthVisibilityWindow
                    recs = (
                        db.query(EarthVisibilityWindow)
                        .filter(EarthVisibilityWindow.site_id == site_id)
                        .order_by(EarthVisibilityWindow.id.asc())
                        .all()
                    )
                    if recs:
                        window_count = len(recs)
                        for r in recs:
                            if r.end_time and r.start_time:
                                total_vis_h += (r.end_time - r.start_time).total_seconds() / 3600.0
                        latest_params = recs[-1].parameters
                except Exception:
                    pass

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "id": site_id,
                    "name": site_name,
                    "is_placeholder": is_placeholder,
                    "coordinate_frame": frame,
                    "units": "deg",
                    "parameters": latest_params,
                    "window_totals": {
                        "window_count": window_count,
                        "total_visible_hours": round(total_vis_h, 2),
                    },
                    "feature_role": "site_earth_visibility_summary",
                    "source_product_id": "lola-dem-75s-240m",
                    "label": "Modelled",
                    "disclaimer": (
                        "Terrain-aware direct-to-Earth line-of-sight visibility summary. "
                        "Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. "
                        "Not an Earth coordinate system. Geometric visibility is not a guaranteed radio link."
                    ),
                },
            })

        return {
            "type": "FeatureCollection",
            "properties": {
                "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
                "body_id": "moon",
                "layer": "earth_visibility",
                "total_features": len(features),
            },
            "coordinate_reference_note": MOON_COORDINATE_REFERENCE_NOTE,
            "features": features,
        }
