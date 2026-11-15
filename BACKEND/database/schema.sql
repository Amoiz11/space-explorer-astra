-- Space Explorer Database Schema
-- Extension for PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Celestial Bodies
CREATE TABLE IF NOT EXISTS celestial_bodies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    body_type VARCHAR(50) NOT NULL,
    reference_system VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Missions
CREATE TABLE IF NOT EXISTS missions (
    id VARCHAR(50) PRIMARY KEY,
    body_id VARCHAR(50) NOT NULL REFERENCES celestial_bodies(id),
    name VARCHAR(100) NOT NULL,
    launch_date TIMESTAMP WITH TIME ZONE,
    landing_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Explorers (rovers, landers, orbiters, probes)
CREATE TABLE IF NOT EXISTS explorers (
    id VARCHAR(50) PRIMARY KEY,
    mission_id VARCHAR(50) NOT NULL REFERENCES missions(id),
    name VARCHAR(100) NOT NULL,
    explorer_type VARCHAR(50) NOT NULL, -- rover, lander, orbiter, probe
    current_status VARCHAR(50) NOT NULL, -- active, mission ended, inactive, unknown
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Data Sources
CREATE TABLE IF NOT EXISTS data_sources (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    source_url TEXT,
    organization VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Data Products
CREATE TABLE IF NOT EXISTS data_products (
    id VARCHAR(100) PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL REFERENCES data_sources(id),
    product_identifier VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    checksum VARCHAR(128),
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Locations
CREATE TABLE IF NOT EXISTS locations (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    original_coordinates JSONB NOT NULL, -- original values and units
    coordinate_frame VARCHAR(100) NOT NULL,
    geometry geometry(Geometry, 0), -- Planetary SRID or null until defined
    uncertainty JSONB,
    product_id VARCHAR(100) REFERENCES data_products(id),
    position_method VARCHAR(50) NOT NULL, -- localized, derived, interpolated, unknown
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Trajectories
CREATE TABLE IF NOT EXISTS trajectories (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    path_geometry geometry(Geometry, 0),
    method VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Images
CREATE TABLE IF NOT EXISTS images (
    id VARCHAR(100) PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    image_url TEXT NOT NULL,
    camera VARCHAR(100),
    product_id VARCHAR(100) REFERENCES data_products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Telemetry
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metric VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50) NOT NULL,
    product_id VARCHAR(100) REFERENCES data_products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Mission Events
CREATE TABLE IF NOT EXISTS mission_events (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    source_id VARCHAR(100) REFERENCES data_products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Health Reports
CREATE TABLE IF NOT EXISTS health_reports (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL,
    condition VARCHAR(100) NOT NULL,
    evidence TEXT NOT NULL,
    source_id VARCHAR(100) REFERENCES data_products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Status History
CREATE TABLE IF NOT EXISTS status_history (
    id BIGSERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) NOT NULL REFERENCES explorers(id),
    status VARCHAR(50) NOT NULL,
    effective_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source_id VARCHAR(100) REFERENCES data_products(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. Candidate Landing Sites (Created by A, used by B and Frontend)
CREATE TABLE IF NOT EXISTS candidate_landing_sites (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    body_id VARCHAR(50) NOT NULL REFERENCES celestial_bodies(id),
    coordinates JSONB NOT NULL, -- {values: [...], units: 'deg', frame: '...'}
    frame VARCHAR(100) NOT NULL,
    analysis_radius_m DOUBLE PRECISION NOT NULL DEFAULT 1000.0,
    notes TEXT,
    is_placeholder BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. Users (Role-based access: public, researcher, admin)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'public',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
