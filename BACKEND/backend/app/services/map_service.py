from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.models import Mission, Explorer, Location, CandidateLandingSite
from backend.app.schemas.map_layer import LayerMetadataResponse
from data_pipeline.exporters.geojson_exporter import GeoJSONExporter
from data_pipeline.processors.lunar_raster_processor import (
    get_sidecar_data,
    get_raster_png_path,
    generate_lunar_rasters_and_sidecars,
)


class MapService:
    def __init__(self, db: Session):
        self.db = db

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        # 1. Direct match on mission ID
        m = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if m:
            return m
        # 2. Match on body ID (e.g. /map/layers/moon or /map/layers/mars)
        m = self.db.query(Mission).filter(Mission.body_id == mission_id).first()
        if m:
            return m
        # 3. Fallback for "moon"
        if mission_id.lower() in ("moon", "luna", "lunar"):
            return Mission(
                id=mission_id,
                name="Artemis Lunar Exploration",
                body_id="moon",
                is_placeholder=True,
            )
        return None

    def get_layers_for_mission(self, mission_id: str) -> Optional[List[LayerMetadataResponse]]:
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        layers: List[LayerMetadataResponse] = []

        if mission.body_id == "mars":
            explorer = self.db.query(Explorer).filter(Explorer.mission_id == mission_id).first()
            explorer_name = explorer.name if explorer else "Perseverance"
            explorer_id = explorer.id if explorer else "perseverance"

            has_real_data = (
                self.db.query(Location)
                .filter(Location.explorer_id == explorer_id, Location.is_placeholder == False)
                .first()
                is not None
            )

            # 1. Historical Positions Layer
            layers.append(
                LayerMetadataResponse(
                    id="historical-positions",
                    name=f"Historical Positions ({explorer_name})",
                    type="point",
                    description="Historical rover position points localized from NASA PDS PLACES dataset.",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/historical-positions.geojson",
                    url=f"/api/v1/map/layers/{mission_id}/historical-positions.geojson",
                    label="Estimated",
                    source="NASA PDS Geosciences Node (PLACES Release 16.0)",
                    source_product_id="urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
                    is_placeholder=not has_real_data,
                    disclaimer="Coordinates are Mars planetocentric (east-positive), not Earth EPSG:4326. SCLK timestamps preserved without UTC conversion kernel.",
                )
            )

            # 2. Traversed Route Layer
            layers.append(
                LayerMetadataResponse(
                    id="traversed-route",
                    name=f"Traversed Route ({explorer_name})",
                    type="linestring",
                    description="Rover traverse reconstructed from supported PLACES localization segments (sol >= 0).",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/traversed-route.geojson",
                    url=f"/api/v1/map/layers/{mission_id}/traversed-route.geojson",
                    label="Estimated",
                    source="NASA PDS Geosciences Node (PLACES Release 16.0)",
                    source_product_id="urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
                    is_placeholder=not has_real_data,
                    disclaimer="Traverse route segments interpolated from best_interp telemetry. Landing site reference (sol -1) excluded from line.",
                )
            )

        elif mission.body_id == "moon":
            # Ensure rasters exist on disk
            try:
                generate_lunar_rasters_and_sidecars()
            except Exception:
                pass

            # Legacy alias included for artemis-lunar to preserve existing test compatibility
            if mission_id == "artemis-lunar":
                layers.append(
                    LayerMetadataResponse(
                        id="candidate-lunar-sites",
                        name="Candidate Lunar Landing Sites",
                        type="point",
                        description="Candidate Artemis polar landing sites and evaluation areas.",
                        geojson_url=f"/api/v1/map/layers/{mission_id}/candidate-lunar-sites.geojson",
                        url=f"/api/v1/map/layers/{mission_id}/candidate-lunar-sites.geojson",
                        label="Unknown",
                        source="NASA Space Apps / Artemis Mission Planning",
                        source_product_id="urn:nasa:lunar:artemis:candidate_sites",
                        is_placeholder=True,
                        disclaimer="Placeholder candidate areas for testing mission planning and terrain visualization. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system.",
                    )
                )

            # 1. Candidate Sites (Point per site + Polygon for analysis radius or landing ellipse)
            layers.append(
                LayerMetadataResponse(
                    id="candidate_sites",
                    name="Candidate Lunar Landing Sites",
                    type="vector",
                    description="Candidate Artemis polar landing sites with footprints (circular analysis radius or landing ellipse).",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/candidate_sites.geojson",
                    url=f"/api/v1/map/layers/{mission_id}/candidate_sites.geojson",
                    label="Derived",
                    source="NASA Space Apps / Artemis Mission Planning",
                    source_product_id="urn:nasa:lunar:artemis:candidate_sites",
                    is_placeholder=True,
                    disclaimer="Candidate landing site points and footprint polygons. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification.",
                )
            )

            # 2. Illumination summary layer
            layers.append(
                LayerMetadataResponse(
                    id="illumination",
                    name="Lunar Site Illumination Summary",
                    type="vector",
                    description="Per-site terrain-aware solar illumination window totals and parameters.",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/illumination.geojson",
                    url=f"/api/v1/map/layers/{mission_id}/illumination.geojson",
                    label="Modelled",
                    source="SPICE ephemeris (DE421) + LOLA 240m DEM local horizon",
                    source_product_id="lola-dem-75s-240m",
                    is_placeholder=True,
                    disclaimer="Terrain-aware illumination summary points. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification.",
                )
            )

            # 3. Earth visibility summary layer
            layers.append(
                LayerMetadataResponse(
                    id="earth_visibility",
                    name="Lunar Site Earth Visibility Summary",
                    type="vector",
                    description="Per-site direct-to-Earth line-of-sight visibility window totals and parameters.",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/earth_visibility.geojson",
                    url=f"/api/v1/map/layers/{mission_id}/earth_visibility.geojson",
                    label="Modelled",
                    source="SPICE ephemeris (DE421) + LOLA 240m DEM local horizon",
                    source_product_id="lola-dem-75s-240m",
                    is_placeholder=True,
                    disclaimer="Terrain-aware direct-to-Earth line-of-sight visibility summary points. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Geometric visibility is not a guaranteed radio link.",
                )
            )

            # 4. Lunar DEM raster layer
            layers.append(
                LayerMetadataResponse(
                    id="lunar_dem",
                    name="Lunar LOLA DEM (South Polar)",
                    type="raster",
                    description="Downsampled LOLA polar stereographic digital elevation model (1920 m/pixel preview).",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/lunar_dem.json",
                    url=f"/api/v1/map/layers/{mission_id}/lunar_dem.png",
                    label="Derived",
                    source="NASA LOLA Science Team / PDS Geosciences Node",
                    source_product_id="lola-dem-75s-240m",
                    is_placeholder=False,
                    disclaimer="Polar stereographic projection true at south pole (-90 deg), MOON_ME_DE421 frame, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Cannot resolve sub-resolution micro-hazards.",
                )
            )

            # 5. Lunar Slope raster layer
            layers.append(
                LayerMetadataResponse(
                    id="lunar_slope",
                    name="Lunar LOLA Slope (South Polar)",
                    type="raster",
                    description="Downsampled LOLA polar stereographic slope map in degrees via Horn (1981) gradient.",
                    geojson_url=f"/api/v1/map/layers/{mission_id}/lunar_slope.json",
                    url=f"/api/v1/map/layers/{mission_id}/lunar_slope.png",
                    label="Derived",
                    source="Derived from LOLA DEM via Horn (1981) 8-neighbor gradient",
                    source_product_id="lola-dem-75s-240m",
                    is_placeholder=False,
                    disclaimer="Horn finite-difference slope map from LOLA DEM. Polar stereographic projection true at south pole, MOON_ME_DE421 frame, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification.",
                )
            )

        return layers

    def get_geojson_layer(self, mission_id: str, layer_id: str) -> Optional[Dict[str, Any]]:
        mission = self.get_mission(mission_id)
        if not mission:
            return None

        # Normalize layer_id (strip .geojson or .json if passed in path param)
        clean_layer_id = layer_id.lower()
        if clean_layer_id.endswith(".geojson"):
            clean_layer_id = clean_layer_id[:-8]
        elif clean_layer_id.endswith(".json"):
            clean_layer_id = clean_layer_id[:-5]

        if mission.body_id == "mars":
            explorer = self.db.query(Explorer).filter(Explorer.mission_id == mission_id).first()
            explorer_id = explorer.id if explorer else "perseverance"

            locations = (
                self.db.query(Location)
                .filter(Location.explorer_id == explorer_id)
                .order_by(Location.observed_at.asc(), Location.id.asc())
                .all()
            )

            if clean_layer_id in ("historical-positions", "positions", "historical_positions"):
                return GeoJSONExporter.export_locations_feature_collection(locations, explorer_id=explorer_id)
            elif clean_layer_id in ("traversed-route", "route", "traverse", "traversed_route"):
                return GeoJSONExporter.export_traversed_route_feature_collection(locations, explorer_id=explorer_id)
            else:
                return None

        elif mission.body_id == "moon":
            sites = self.db.query(CandidateLandingSite).filter(CandidateLandingSite.body_id == "moon").all()

            if clean_layer_id in (
                "candidate_sites",
                "candidate-sites",
                "candidate_lunar_sites",
                "candidate-lunar-sites",
                "sites",
            ):
                return GeoJSONExporter.export_candidate_sites_feature_collection(
                    sites, include_polygons=True, db=self.db
                )
            elif clean_layer_id in ("illumination", "lunar_illumination", "illumination_summary"):
                return GeoJSONExporter.export_illumination_feature_collection(sites, db=self.db)
            elif clean_layer_id in (
                "earth_visibility",
                "earth-visibility",
                "lunar_earth_visibility",
                "earth_visibility_summary",
            ):
                return GeoJSONExporter.export_earth_visibility_feature_collection(sites, db=self.db)
            elif clean_layer_id in ("lunar_dem", "lunar-dem"):
                return get_sidecar_data("lunar_dem")
            elif clean_layer_id in ("lunar_slope", "lunar-slope"):
                return get_sidecar_data("lunar_slope")
            else:
                return None

        return None

    def get_raster_png(self, mission_id: str, layer_id: str) -> Optional[str]:
        """Return file path to raster PNG for lunar layers."""
        mission = self.get_mission(mission_id)
        if not mission or mission.body_id != "moon":
            return None
        return get_raster_png_path(layer_id)

    def get_raster_sidecar(self, mission_id: str, layer_id: str) -> Optional[Dict[str, Any]]:
        """Return sidecar JSON dictionary for lunar raster layers."""
        mission = self.get_mission(mission_id)
        if not mission or mission.body_id != "moon":
            return None
        return get_sidecar_data(layer_id)
