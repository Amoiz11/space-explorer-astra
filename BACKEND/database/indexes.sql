-- Indexes for Space Explorer Database

-- Locations indexes
CREATE INDEX IF NOT EXISTS idx_locations_explorer_time ON locations (explorer_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_locations_product_id ON locations (product_id);

-- Telemetry & time-series indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_explorer_time ON telemetry (explorer_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_images_explorer_time ON images (explorer_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_events_explorer_time ON mission_events (explorer_id, event_date);
CREATE INDEX IF NOT EXISTS idx_status_history_explorer_time ON status_history (explorer_id, effective_at);

-- Candidate landing sites
CREATE INDEX IF NOT EXISTS idx_candidate_sites_body ON candidate_landing_sites (body_id);
CREATE INDEX IF NOT EXISTS idx_candidate_sites_placeholder ON candidate_landing_sites (is_placeholder);

-- Data products & sources
CREATE INDEX IF NOT EXISTS idx_data_products_identifier ON data_products (product_identifier);
