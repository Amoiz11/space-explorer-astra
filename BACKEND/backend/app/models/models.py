import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class CelestialBody(Base):
    __tablename__ = "celestial_bodies"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    body_type = Column(String(50), nullable=False)  # planet, moon, asteroid
    reference_system = Column(String(100), nullable=False)
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    missions = relationship("Mission", back_populates="body")
    candidate_sites = relationship("CandidateLandingSite", back_populates="body")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(String(50), primary_key=True, index=True)
    body_id = Column(String(50), ForeignKey("celestial_bodies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    launch_date = Column(DateTime(timezone=True), nullable=True)
    landing_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False)  # active, completed, ended
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    body = relationship("CelestialBody", back_populates="missions")
    explorers = relationship("Explorer", back_populates="mission")


class Explorer(Base):
    __tablename__ = "explorers"

    id = Column(String(50), primary_key=True, index=True)
    mission_id = Column(String(50), ForeignKey("missions.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    explorer_type = Column(String(50), nullable=False)  # rover, lander, orbiter, probe
    current_status = Column(String(50), nullable=False)  # active, mission ended, inactive, unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    mission = relationship("Mission", back_populates="explorers")
    locations = relationship("Location", back_populates="explorer")
    trajectories = relationship("Trajectory", back_populates="explorer")
    images = relationship("Image", back_populates="explorer")
    telemetry = relationship("Telemetry", back_populates="explorer")
    events = relationship("MissionEvent", back_populates="explorer")
    health_reports = relationship("HealthReport", back_populates="explorer")
    status_history = relationship("StatusHistory", back_populates="explorer")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    source_url = Column(Text, nullable=True)
    organization = Column(String(100), nullable=True)
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    data_products = relationship("DataProduct", back_populates="source")


class DataProduct(Base):
    __tablename__ = "data_products"

    id = Column(String(100), primary_key=True, index=True)
    source_id = Column(String(50), ForeignKey("data_sources.id"), nullable=False, index=True)
    product_identifier = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=True)
    checksum = Column(String(128), nullable=True)
    observation_time = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    coordinate_frame = Column(String(100), nullable=True)
    units = Column(String(50), nullable=True)
    processing_method = Column(String(150), nullable=True)
    uncertainty = Column(JSON, nullable=True)
    label = Column(String(50), nullable=False, default="Verified")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)

    source = relationship("DataSource", back_populates="data_products")
    locations = relationship("Location", back_populates="data_product")
    trajectories = relationship("Trajectory", back_populates="data_product")
    images = relationship("Image", back_populates="data_product")
    telemetry = relationship("Telemetry", back_populates="data_product")
    events = relationship("MissionEvent", back_populates="data_product")
    health_reports = relationship("HealthReport", back_populates="data_product")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # Stored as original values, units and frame (Section 5.1)
    original_coordinates = Column(JSON, nullable=False)
    coordinate_frame = Column(String(100), nullable=False)
    uncertainty = Column(JSON, nullable=True)
    product_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    position_method = Column(String(50), nullable=False, default="localized")  # localized, derived, interpolated, unknown
    position_status = Column(String(50), nullable=False, default="verified")  # verified, historical, estimated, unknown
    label = Column(String(50), nullable=False, default="Verified")  # Verified, Historical, Estimated, Unknown
    retrieved_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="locations")
    data_product = relationship("DataProduct", back_populates="locations")


class Trajectory(Base):
    __tablename__ = "trajectories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    path_coordinates = Column(JSON, nullable=True)  # List of coordinate points
    method = Column(String(50), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    product_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    label = Column(String(50), nullable=False, default="Verified")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="trajectories")
    data_product = relationship("DataProduct", back_populates="trajectories")


class Image(Base):
    __tablename__ = "images"

    id = Column(String(100), primary_key=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sol = Column(Integer, nullable=True, index=True)
    image_url = Column(Text, nullable=False)
    camera = Column(String(100), nullable=True)
    product_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    label = Column(String(50), nullable=False, default="Historical")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="images")
    data_product = relationship("DataProduct", back_populates="images")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    product_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    label = Column(String(50), nullable=False, default="Verified")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="telemetry")
    data_product = relationship("DataProduct", back_populates="telemetry")


class MissionEvent(Base):
    __tablename__ = "mission_events"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    source_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    label = Column(String(50), nullable=False, default="Verified")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="events")
    data_product = relationship("DataProduct", back_populates="events")


class HealthReport(Base):
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    condition = Column(String(100), nullable=False)
    evidence = Column(Text, nullable=False)
    source_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    label = Column(String(50), nullable=False, default="Historical")  # Verified, Historical, Estimated, Unknown
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="health_reports")
    data_product = relationship("DataProduct", back_populates="health_reports")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    explorer_id = Column(String(50), ForeignKey("explorers.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    effective_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source_id = Column(String(100), ForeignKey("data_products.id"), nullable=True)
    is_placeholder = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    explorer = relationship("Explorer", back_populates="status_history")


class CandidateLandingSite(Base):
    __tablename__ = "candidate_landing_sites"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    body_id = Column(String(50), ForeignKey("celestial_bodies.id"), nullable=False, index=True)
    coordinates = Column(JSON, nullable=False)
    frame = Column(String(100), nullable=False)
    analysis_radius_m = Column(Float, nullable=False, default=1000.0)
    semi_major_m = Column(Float, nullable=True)
    semi_minor_m = Column(Float, nullable=True)
    orientation_deg = Column(Float, nullable=True)
    criteria = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    is_placeholder = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    body = relationship("CelestialBody", back_populates="candidate_sites")
    terrain_metrics = relationship("TerrainMetrics", back_populates="site", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="public")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class TerrainProduct(Base):
    __tablename__ = "terrain_products"

    id = Column(String(100), primary_key=True, index=True)
    source_product_id = Column(String(100), ForeignKey("data_products.id"), nullable=False, index=True)
    resolution = Column(String(100), nullable=False)
    vertical_reference = Column(String(255), nullable=True)
    coverage = Column(JSON, nullable=True)
    version = Column(String(50), nullable=True)
    no_data_value = Column(String(100), nullable=True)
    coordinate_reference_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    data_product = relationship("DataProduct", backref="terrain_products")


class TerrainMetrics(Base):
    __tablename__ = "terrain_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    site_id = Column(String(50), ForeignKey("candidate_landing_sites.id"), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    product_id = Column(String(100), ForeignKey("terrain_products.id"), nullable=False, index=True)
    mean_slope = Column(Float, nullable=True)
    max_slope = Column(Float, nullable=True)
    elevation_stats = Column(JSON, nullable=True)
    method = Column(String(200), nullable=True)
    is_placeholder = Column(Boolean, nullable=False, default=False)

    site = relationship("CandidateLandingSite", back_populates="terrain_metrics")
    terrain_product = relationship("TerrainProduct")


class IlluminationResult(Base):
    __tablename__ = "illumination_results"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    site_id = Column(String(50), ForeignKey("candidate_landing_sites.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    sun_azimuth = Column(Float, nullable=True)
    sun_elevation = Column(Float, nullable=True)
    illuminated_fraction = Column(Float, nullable=True)
    method = Column(String(200), nullable=True)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    site = relationship("CandidateLandingSite", backref="illumination_results")


class EarthVisibilityWindow(Base):
    __tablename__ = "earth_visibility_windows"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    site_id = Column(String(50), ForeignKey("candidate_landing_sites.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    earth_azimuth = Column(Float, nullable=True)
    earth_elevation = Column(Float, nullable=True)
    obstruction_status = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    site = relationship("CandidateLandingSite", backref="earth_visibility_windows")


class SolarPowerEstimate(Base):
    __tablename__ = "solar_power_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    site_id = Column(String(50), ForeignKey("candidate_landing_sites.id"), nullable=False, index=True)
    time_range = Column(JSON, nullable=False)
    panel_assumptions = Column(JSON, nullable=True)
    estimated_energy = Column(Float, nullable=True)
    units = Column(String(50), nullable=True, default="Wh")
    uncertainty = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    site = relationship("CandidateLandingSite", backref="solar_power_estimates")


class LandingSiteComparison(Base):
    __tablename__ = "landing_site_comparisons"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    criteria = Column(JSON, nullable=True)         # list of criterion dicts
    thresholds = Column(JSON, nullable=True)        # dict metric -> threshold
    result_metadata = Column(JSON, nullable=True)  # rows, best_by, settings, disclaimers
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


