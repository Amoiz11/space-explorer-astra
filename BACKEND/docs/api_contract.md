# Space Explorer API Contract
NASA Space Apps 2026 — Team Astra Motion

This document defines the REST API contract between **Backend A** (Core Platform, Data Pipeline & APIs), **Backend B** (Lunar Astrodynamics & Terrain Calculations), and the **Frontend**.

---

## 1. System Health & Metadata (Backend A)

### `GET /`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "message": "Welcome to Space Explorer API",
    "docs": "/docs",
    "health": "/health",
    "api_v1": "/api/v1",
    "is_placeholder": false
  }
  ```

### `GET /health`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "status": "ok",
    "app": "Space Explorer API",
    "version": "0.1.0",
    "environment": "development",
    "database": "sqlite",
    "is_placeholder": false
  }
  ```

### `GET /api/v1/status`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "status": "online",
    "api_version": "v1",
    "service": "Space Explorer Core API",
    "timestamp": "2026-11-14T12:00:00Z",
    "is_placeholder": false
  }
  ```

---

## 2. Celestial Bodies (Backend A)

### `GET /api/v1/bodies`
- **Owner:** Backend A
- **Query Parameters:**
  - `limit` (integer, default: 50, max: 100)
  - `offset` (integer, default: 0)
- **Response Example:**
  ```json
  {
    "items": [
      {
        "id": "mars",
        "name": "Mars",
        "body_type": "planet",
        "reference_system": "IAU_MARS_2000",
        "is_placeholder": true,
        "created_at": "2026-11-14T10:00:00Z"
      },
      {
        "id": "moon",
        "name": "Moon",
        "body_type": "moon",
        "reference_system": "MOON_ME_DE421",
        "is_placeholder": true,
        "created_at": "2026-11-14T10:00:00Z"
      }
    ],
    "total": 2,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
  ```

### `GET /api/v1/bodies/{body_id}`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "id": "moon",
    "name": "Moon",
    "body_type": "moon",
    "reference_system": "MOON_ME_DE421",
    "is_placeholder": true,
    "created_at": "2026-11-14T10:00:00Z"
  }
  ```

---

## 3. Missions (Backend A)

### `GET /api/v1/missions`
- **Owner:** Backend A
- **Query Parameters:**
  - `body_id` (string, optional: e.g. `mars`, `moon`)
  - `status` (string, optional: e.g. `active`, `ended`)
  - `limit` (integer, default: 50)
  - `offset` (integer, default: 0)
- **Response Example:**
  ```json
  {
    "items": [
      {
        "id": "mars-2020",
        "body_id": "mars",
        "name": "Mars 2020",
        "launch_date": "2020-07-30T11:50:00Z",
        "landing_date": "2021-02-18T20:55:00Z",
        "end_date": null,
        "status": "active",
        "label": "Unknown",
        "source_label": "NASA Mission Archive",
        "is_placeholder": true,
        "created_at": "2026-11-14T10:00:00Z"
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
  ```

### `GET /api/v1/missions/{mission_id}`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "id": "mars-2020",
    "body_id": "mars",
    "name": "Mars 2020",
    "launch_date": "2020-07-30T11:50:00Z",
    "landing_date": "2021-02-18T20:55:00Z",
    "end_date": null,
    "status": "active",
    "label": "Unknown",
    "source_label": "NASA Mission Archive",
    "is_placeholder": true,
    "created_at": "2026-11-14T10:00:00Z"
  }
  ```

---

## 4. Explorers & Rovers (Backend A)

### `GET /api/v1/rovers`
- **Owner:** Backend A
- **Query Parameters:**
  - `mission_id` (string, optional)
  - `explorer_type` (string, optional: `rover`, `lander`, `orbiter`, `probe`)
  - `status` (string, optional)
  - `limit` (integer, default: 50)
  - `offset` (integer, default: 0)
- **Response Example:**
  ```json
  {
    "items": [
      {
        "id": "perseverance",
        "mission_id": "mars-2020",
        "name": "Perseverance Rover",
        "explorer_type": "rover",
        "current_status": "active",
        "label": "Unknown",
        "source_label": "NASA PDS / Mission Catalog",
        "is_placeholder": true,
        "created_at": "2026-11-14T10:00:00Z"
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
  ```

### `GET /api/v1/rovers/{rover_id}`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "id": "perseverance",
    "mission_id": "mars-2020",
    "name": "Perseverance Rover",
    "explorer_type": "rover",
    "current_status": "active",
    "label": "Unknown",
    "source_label": "NASA PDS / Mission Catalog",
    "is_placeholder": true,
    "created_at": "2026-11-14T10:00:00Z"
  }
  ```

---

## 5. Locations & Trajectory (Backend A)

### `GET /api/v1/rovers/{rover_id}/locations`
- **Owner:** Backend A
- **Query Parameters:**
  - `start_date` (ISO datetime, optional)
  - `end_date` (ISO datetime, optional)
  - `limit` (integer, default: 100, max: 500)
  - `offset` (integer, default: 0)
- **Response Example:**
  ```json
  {
    "items": [
      {
        "explorer_id": "perseverance",
        "position_status": "estimated",
        "label": "Estimated",
        "observed_at": "2021-02-18T20:44:27.444000+00:00",
        "sol": 0,
        "sclk": "666952977",
        "coordinates": {
          "values": [18.4446, 77.4508],
          "units": "deg",
          "coordinate_frame": "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. Mars body-fixed frame name not stated in the label."
        },
        "uncertainty": null,
        "position_method": "interpolated (converted from SCLK via NAIF SPICE)",
        "source_product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
        "is_placeholder": false
      }
    ],
    "total": 500,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
  ```

### `GET /api/v1/rovers/{rover_id}/latest-location`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example (Found - Latest published position):**
  ```json
  {
    "explorer_id": "perseverance",
    "position_status": "estimated",
    "label": "Estimated",
    "observed_at": "2026-06-21T23:18:43.583000Z",
    "sol": 1897,
    "sclk": "835354500",
    "coordinates": {
      "values": [18.4447, 77.4508],
      "units": "deg",
      "coordinate_frame": "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. Mars body-fixed frame name not stated in the label."
    },
    "uncertainty": null,
    "position_method": "downsampled: last localization of each sol",
    "source_product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
    "retrieved_at": "2026-11-15T12:00:00Z",
    "source_label": "NASA PDS PLACES Localization Product",
    "is_placeholder": false
  }
  ```
- **Response Example (Not Found / Unrecorded - Never fabricated):**
  ```json
  {
    "explorer_id": "curiosity",
    "position_status": "unknown",
    "label": "Unknown",
    "observed_at": null,
    "sol": null,
    "sclk": null,
    "coordinates": null,
    "uncertainty": null,
    "position_method": "unknown",
    "source_product_id": null,
    "retrieved_at": null,
    "source_label": "NASA PDS PLACES Localization Product",
    "is_placeholder": true
  }
  ```

### `GET /api/v1/rovers/{rover_id}/trajectory`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "id": 1,
    "explorer_id": "perseverance",
    "path_coordinates": [
      [18.4447, 77.4508],
      [18.4450, 77.4512],
      [18.4452, 77.4515]
    ],
    "method": "validated surface traverse segments",
    "start_time": "2021-02-18T21:00:00Z",
    "end_time": "2021-03-05T12:00:00Z",
    "product_id": "urn:nasa:pds:mars2020_rover_places:site_0001",
    "label": "Unknown",
    "source_label": "NASA PDS Trajectory Archive",
    "is_placeholder": true
  }
  ```

---

## 6. Images, Events & Health (Backend A)

### `GET /api/v1/rovers/{rover_id}/analytics`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "explorer_id": "perseverance",
    "duration_days": 2094.7,
    "distance_km": 0.15,
    "calculation_method": "Calculated from documented mission start/landing dates and verified traversed waypoints",
    "label": "Estimated",
    "source_label": "NASA Mission Analysis Archive",
    "is_placeholder": true
  }
  ```

### `GET /api/v1/rovers/{rover_id}/timeline`
- **Owner:** Backend A
- **Query Parameters:**
  - `start_date` (ISO datetime, optional)
  - `end_date` (ISO datetime, optional)
  - `limit` (integer, default: 100, max: 500)
- **Response Example:**
  ```json
  {
    "explorer_id": "perseverance",
    "total_items": 1,
    "timeline": [
      {
        "item_type": "event",
        "timestamp": "2021-02-18T20:55:00Z",
        "title": "Landing",
        "details": {"event_type": "Landing", "description": "Perseverance landed in Jezero Crater"},
        "label": "Historical",
        "source_label": "NASA Mission Operations Log",
        "is_placeholder": true
      }
    ],
    "label": "Historical",
    "source_label": "Space Explorer Correlated Timeline Engine",
    "is_placeholder": true
  }
  ```

### `GET /api/v1/rovers/{rover_id}/images`
- **Owner:** Backend A
- **Query Parameters:** `start_date`, `end_date`, `camera`, `sol`, `limit`, `offset`
- **Response Example:**
  ```json
  {
    "items": [
      {
        "id": "img-m2020-TEST_MOCK_SOL001_CAM01",
        "explorer_id": "perseverance",
        "captured_at": "2021-03-01T10:00:00Z",
        "sol": 10,
        "image_url": "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/00010/test1.jpg",
        "camera": "NAVCAM_LEFT",
        "product_id": "urn:nasa:pds:m2020_raw_images:TEST_MOCK_SOL001_CAM01",
        "label": "Verified",
        "source_label": "NASA Planetary Data System Image Archive",
        "is_placeholder": false
      }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
  ```

### `GET /api/v1/rovers/{rover_id}/events`
- **Owner:** Backend A
- **Query Parameters:** `start_date`, `end_date`, `limit`, `offset`
- **Response Example:**
  ```json
  {
    "items": [
      {
        "id": 1,
        "explorer_id": "perseverance",
        "event_date": "2021-02-18T20:55:00Z",
        "event_type": "Landing",
        "description": "Perseverance landed successfully in Jezero Crater, Mars.",
        "source_id": "urn:nasa:pds:mars2020_rover_places:site_0001",
        "label": "Unknown",
        "source_label": "NASA Mission Operations Log",
        "is_placeholder": true
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
  ```

### `GET /api/v1/rovers/{rover_id}/health`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "explorer_id": "perseverance",
    "condition": "nominal",
    "evidence": "All primary avionics and communications operational after landing.",
    "reported_at": "2021-02-19T10:00:00Z",
    "source_id": "urn:nasa:pds:mars2020_rover_places:site_0001",
    "label": "Unknown",
    "source_label": "NASA Mission Technical Reports",
    "is_placeholder": true
  }
  ```

---

## 7. Provenance & Data Sources (Backend A)

### `GET /api/v1/sources/{product_id}`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example (200 OK):**
  ```json
  {
    "product_id": "urn:nasa:pds:mars2020_rover_places:site_0001",
    "product_identifier": "urn:nasa:pds:mars2020_rover_places:site_0001",
    "version": "11.0",
    "checksum": "a1b2c3d4e5f67890123456789abcdef0",
    "source": {
      "id": "src-pds-places",
      "name": "NASA Planetary Data System (PDS) Geosciences Node",
      "source_url": "https://pds-geosciences.wustl.edu/missions/mars2020/index.htm",
      "organization": "NASA / JPL / Washington University in St. Louis",
      "is_placeholder": true
    },
    "observation_time": "2021-02-18T20:55:00Z",
    "retrieved_at": "2026-11-14T12:00:00Z",
    "coordinate_frame": "IAU_MARS_2000",
    "units": "deg",
    "processing_method": "Rover localization and traverse mesh reconstruction (PLACES)",
    "uncertainty": {
      "radius_m": 5.0,
      "confidence_level": 0.95
    },
    "label": "Unknown",
    "is_placeholder": true
  }
  ```
- **Error Response (404 Not Found):**
  ```json
  {
    "error": "Source data product 'unknown-product-id' not found",
    "detail": "Source data product 'unknown-product-id' not found",
    "status_code": 404,
    "is_placeholder": false
  }
  ```

---

## 8. Candidate Landing Sites CRUD (Backend A)

### `GET /api/v1/lunar/sites`
- **Owner:** Backend A
- **Query Parameters:** `body_id` (default: `moon`)
- **Response Example:**
  ```json
  [
    {
      "id": "site-shackleton-01",
      "name": "Shackleton Rim Candidate Area",
      "body_id": "moon",
      "coordinates": {
        "values": [-89.9, 0.0],
        "units": "deg",
        "frame": "MOON_ME_DE421"
      },
      "frame": "MOON_ME_DE421",
      "analysis_radius_m": 1000.0,
      "notes": "Placeholder candidate site for testing Backend B and Frontend integration.",
      "is_placeholder": true
    }
  ]
  ```

### `GET /api/v1/lunar/sites/{site_id}`
- **Owner:** Backend A
- **Query Parameters:** None
- **Response Example:**
  ```json
  {
    "id": "site-shackleton-01",
    "name": "Shackleton Rim Candidate Area",
    "body_id": "moon",
    "coordinates": {
      "values": [-89.9, 0.0],
      "units": "deg",
      "frame": "MOON_ME_DE421"
    },
    "frame": "MOON_ME_DE421",
    "analysis_radius_m": 1000.0,
    "semi_major_m": null,
    "semi_minor_m": null,
    "orientation_deg": null,
    "criteria": {
      "slope_threshold_deg": 15.0,
      "threshold_label": "example threshold, not an official safety criterion"
    },
    "notes": "Placeholder candidate site for testing Backend B and Frontend integration.",
    "is_placeholder": true
  }
  ```
- **Error Response (404 Not Found):**
  ```json
  {
    "detail": "Candidate lunar site 'unknown-site' not found",
    "status_code": 404,
    "is_placeholder": false
  }
  ```

### `POST /api/v1/lunar/sites`
- **Owner:** Backend A
- **Request Body Example:**
  ```json
  {
    "id": "site-test-03",
    "name": "Haworth Crater Ridge",
    "body_id": "moon",
    "coordinates": {
      "values": [-87.4, 355.0],
      "units": "deg",
      "frame": "MOON_ME_DE421"
    },
    "frame": "MOON_ME_DE421",
    "analysis_radius_m": 1200.0,
    "notes": "Testing site creation",
    "is_placeholder": true
  }
  ```
- **Response Status:** `201 Created`

### `PUT /api/v1/lunar/sites/{site_id}`
- **Owner:** Backend A
- **Request Body Example:**
  ```json
  {
    "analysis_radius_m": 1500.0,
    "notes": "Updated radius for slope calculation"
  }
  ```
- **Response Status:** `200 OK`

### `DELETE /api/v1/lunar/sites/{site_id}`
- **Owner:** Backend A
- **Response Status:** `204 No Content`

---

## 9. Backend B Endpoints (Lunar Astrodynamics & Terrain)

The following endpoints are owned and implemented by **Backend B**:

| Method | Path | Owner | Phase | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/lunar/products/{id}` | Backend B | B1a | Terrain product metadata, provenance, and hazard disclaimer |
| `GET` | `/api/v1/lunar/sites/{id}/terrain` | Backend B | B2 | Lunar DEM elevation profile, local relief, RMS roughness (LL-06, LL-08, LL-09, LL-10) |
| `GET` | `/api/v1/lunar/sites/{id}/slope` | Backend B | B2 | Slope calculation (mean, max, percentiles, histogram) from DEM (LL-07, LL-08, LL-10) |
| `GET` | `/api/v1/lunar/sites/{id}/geometry` | Backend B | B3a | Topocentric sun/earth geometry, flat-horizon visibility windows and totals (LL-11 to LL-13, LL-17) |
| `GET` | `/api/v1/lunar/compare` | Backend B | B3a | Side-by-side comparison of solar and earth visibility totals across candidate landing sites (LL-18) |
| `POST` | `/api/v1/lunar/compare` | Backend B | B5a | Multi-site, multi-window terrain-aware comparison with criteria and best_by (LL-27 to LL-30) |
| `GET` | `/api/v1/lunar/compare/{id}/export` | Backend B | B5a | Export stored comparison as JSON or CSV |
| `GET` | `/api/v1/lunar/sites/{id}/horizon` | Backend B | B3b | Topocentric local terrain horizon profile from LOLA DEM with spherical curvature drop (LL-11, LL-12) |
| `GET` | `/api/v1/lunar/sites/{id}/illumination` | Backend B | B4a | SPICE Sun disk fraction and local horizon illumination timeline and windows (LL-14 to LL-16) |
| `GET` | `/api/v1/lunar/sites/{id}/earth-visibility` | Backend B | B4a | Earth line-of-sight visibility against local horizon with obstruction status (LL-19 to LL-22) |
| `POST` | `/api/v1/lunar/sites/{id}/solar-estimate` | Backend B | B4b | Solar irradiance and power generation estimate (LL-23 to LL-26) |

### `GET /api/v1/lunar/products/{id}`
- **Owner:** Backend B (implemented in B1a)
- **Description:** Returns metadata for a registered lunar terrain product, including resolution, vertical reference, coordinate reference notes, coverage bounds, provenance source, and mandatory hazard disclaimer.
- **Path Parameters:** `id` — the `terrain_products.id` (e.g. `lola-dem-75s-240m`), **not** the PDS4 logical identifier.
- **Response Example:**
  ```json
  {
    "id": "lola-dem-75s-240m",
    "source_product_id": "urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_75s_240m",
    "resolution": "240 m/pixel (240.0 m/pix, true at south pole)",
    "vertical_reference": "Reference sphere radius: 1737.4 km (A_AXIS_RADIUS from label); OFFSET = 1737400.0 m; HEIGHT = DN * 0.5 (metres relative to reference sphere)",
    "coverage": {
      "south_latitude": -90.0,
      "north_latitude": -75.0,
      "west_longitude": "not stated in label",
      "east_longitude": "not stated in label",
      "note": "Full 360 degrees azimuth; corners extend beyond -75 deg edge"
    },
    "version": "V2.0",
    "no_data_value": null,
    "coordinate_reference_note": "MAP_PROJECTION_TYPE = POLAR STEREOGRAPHIC; CENTER_LATITUDE = -90 deg (south pole); COORDINATE_SYSTEM_NAME = MEAN EARTH/POLAR AXIS OF DE421 (MOON_ME_DE421); KEYWORD_LATITUDE_TYPE = PLANETOCENTRIC; POSITIVE_LONGITUDE_DIRECTION = EAST; sphere radius 1737.4 km; transformation from DSMAP_POLAR.CAT (NASA PDS Geosciences Node)",
    "source_name": "NASA Planetary Data System (PDS) Geosciences Node - LRO LOLA",
    "source_url": "https://pds-geosciences.wustl.edu/missions/lro/lola.htm",
    "checksum": "d031efe2611b17dfbf3c158f5e15dc04cd5719349dcbf6384bb21fd97697c490",
    "retrieved_at": "2026-11-15T00:15:30Z",
    "label": "Verified",
    "is_placeholder": false,
    "disclaimer": "DEM resolution cannot detect small rocks, boulders, or micro-hazards. This product is for regional planning support and does not certify landing safety."
  }
  ```

### DEM Pipeline (Phase B1b) — Internal Processing

**Projection:** Official DSMAP_POLAR.CAT formula (fetched from NASA PDS Geosciences Node). Parameters read exclusively from the PDS3 `.lbl` label; nothing assumed.

**Forward (pixel → lat/lon):**
```
X = (I − N/2 − 0.5) × MAP_SCALE
Y = (J − N/2 − 0.5) × MAP_SCALE × NS   [NS = −1 for south]
R = √(X² + Y²)
LON = atan2(X, Y) × 180/π
LAT = −90 + (180/π) × 2 × atan(0.5 × R / 1737400)
```

**Inverse (lat/lon → pixel):**
```
R = 2 × 1737400 × tan((90 − |LAT|) × π/360)   [positive; south sign absorbed in J]
X = R × sin(LON × π/180)
Y = R × cos(LON × π/180)
I = X / MAP_SCALE + N/2 + 0.5
J = Y / (MAP_SCALE × NS) + N/2 + 0.5          [÷ NS to restore pixel J convention]
```

**No reprojection applied.** The DEM is already in its documented native projection. The processed elevation array is saved to `storage/processed/lunar/ldem_75s_240m_elev.npy` (git-ignored).

### `GET /api/v1/lunar/sites/{id}/terrain`
- **Owner:** Backend B (implemented in B2)
- **Description:** Returns elevation and roughness metrics (min, max, mean elevation, local relief, RMS roughness) within the landing analysis footprint (circular radius or landing ellipse).
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (site latitude north of -75°S).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Derived",
    "product_id": "lola-dem-75s-240m",
    "resolution": "240 m/pixel (240.0 m/pix, true at south pole)",
    "coverage": {
      "south_latitude": -90.0,
      "north_latitude": -75.0,
      "west_longitude": "not stated in label",
      "east_longitude": "not stated in label"
    },
    "vertical_reference": "Reference sphere radius: 1737.4 km (A_AXIS_RADIUS from label); OFFSET = 1737400.0 m; HEIGHT = DN * 0.5 (metres relative to reference sphere)",
    "no_data_value": null,
    "coordinate_reference_note": "DSMAP_POLAR.CAT Polar Stereographic (center lat -90 deg, center lon 0 deg, sphere radius 1737.4 km). NOT EPSG:4326.",
    "method": "RMS elevation deviation (standard deviation) and peak-to-peak local relief",
    "units": "m",
    "pixel_count": 57,
    "elevation": {
      "min_m": 323.0,
      "max_m": 1012.5,
      "mean_m": 665.2,
      "local_relief_m": 689.5,
      "roughness_rms_m": 204.15,
      "roughness_method": "RMS elevation deviation (standard deviation) and peak-to-peak local relief",
      "vertical_reference": "reference sphere (radius 1737.4 km)"
    },
    "criteria_result": {
      "slope_threshold_deg": 15.0,
      "threshold_label": "example threshold, not an official safety criterion",
      "exceeding_pixel_count": 57,
      "total_pixel_count": 57,
      "fraction_exceeding_threshold": 1.0,
      "percentage_exceeding_threshold": 100.0,
      "site_safety_disclaimer": "Site is never labelled safe. Threshold is an illustrative user parameter."
    },
    "scale_distortion_note": "Polar stereographic scale factor k = 2 / (1 + sin(|lat|)). At -90°S k=1.000; at the -75°S boundary k=1.0173 (approx 1.73% scale expansion). The distortion is documented and not corrected; estimated slope error due to distortion is < 2% at boundary.",
    "disclaimer": "A 240 m DEM baseline cannot detect or represent slopes, boulders, or micro-hazards at scales smaller than 240 m. Terrain cannot be certified as safe for landing."
  }
  ```

### `GET /api/v1/lunar/sites/{id}/geometry`
- **Owner:** Backend B (implemented in B3a)
- **Description:** Calculates topocentric solar and terrestrial azimuth and elevation in the site's local East-North-Up (ENU) frame using SPICE kernels. Computes contiguous flat-horizon visibility windows and cumulative totals.
- **Query Parameters:**
  - `start` (required): UTC start date string (e.g. `2026-12-01` or ISO 8601).
  - `days` (optional, default `30`): simulation duration in days (minimum 1, maximum 60).
  - `step_minutes` (optional, default `30`): calculation time step in minutes (minimum 5).
  - `include_horizon` (optional, default `false`): when `true`, calculates and adds `horizon_elevation_at_sun_azimuth` and `horizon_elevation_at_earth_azimuth` to each step without changing flat-horizon windows or totals.
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (invalid date or parameter out of bounds) | `503 Service Unavailable` (kernels missing).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Modelled",
    "frame": "MOON_ME_DE421",
    "method": "SPICE geometric, flat horizon",
    "observer_elevation_m": 600.0,
    "reference_sphere_radius_km": 1737.4,
    "kernels_used": [
      "naif0012.tls",
      "de421.bsp",
      "pck00010.tpc",
      "moon_pa_de421_1900-2050.bpc",
      "moon_080317.tf",
      "moon_assoc_me.tf"
    ],
    "series": [
      {
        "timestamp": "2026-12-01T00:00:00Z",
        "sun_azimuth_deg": 190.07,
        "sun_elevation_deg": 1.39,
        "earth_azimuth_deg": 173.32,
        "earth_elevation_deg": 0.24,
        "sun_visible": true,
        "earth_visible": true,
        "joint_visible": true
      }
    ],
    "windows": {
      "sunlight": [
        {
          "start": "2026-12-01T00:00:00Z",
          "end": "2026-12-30T23:30:00Z",
          "duration_hours": 720.0,
          "steps": 1440
        }
      ],
      "earth_visibility": [
        {
          "start": "2026-12-01T00:00:00Z",
          "end": "2026-12-07T06:00:00Z",
          "duration_hours": 150.5,
          "steps": 301
        }
      ],
      "joint_visibility": [
        {
          "start": "2026-12-01T00:00:00Z",
          "end": "2026-12-07T06:00:00Z",
          "duration_hours": 150.5,
          "steps": 301
        }
      ]
    },
    "totals": {
      "sunlight_hours": 720.0,
      "earth_visible_hours": 301.0,
      "joint_sunlight_and_earth_visible_hours": 301.0,
      "total_simulation_hours": 720.0,
      "sunlight_fraction": 1.0,
      "earth_visible_fraction": 0.4181
    },
    "disclaimers": [
      "Geometric visibility is not a guaranteed radio link.",
      "Sunlight is not guaranteed electrical power.",
      "Flat horizon ignores terrain shadowing; actual visibility depends on local topography.",
      "Planning support tool, not safety certification.",
      "Sun and Earth are treated as point sources at their barycenter/center."
    ]
  }
  ```

### `GET /api/v1/lunar/compare`
- **Owner:** Backend B (implemented in B3a)
- **Description:** Returns side-by-side totals (sunlight hours, Earth-visible hours, joint hours) across multiple candidate landing sites for a given time window.
- **Query Parameters:**
  - `site_ids` (required): comma-separated site identifiers (e.g. `site-shackleton-01,site-connecting-ridge-02`).
  - `start` (required): UTC start date string (e.g. `2026-12-01`).
  - `days` (optional, default `30`): simulation duration in days (1 to 60).
  - `step_minutes` (optional, default `30`): time step in minutes (minimum 5).
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` | `503 Service Unavailable`.
- **Response Example (200 OK):**
  ```json
  {
    "label": "Modelled",
    "frame": "MOON_ME_DE421",
    "method": "SPICE geometric, flat horizon",
    "start_utc": "2026-12-01",
    "days": 30,
    "step_minutes": 30,
    "kernels_used": [
      "naif0012.tls",
      "de421.bsp",
      "pck00010.tpc",
      "moon_pa_de421_1900-2050.bpc",
      "moon_080317.tf",
      "moon_assoc_me.tf"
    ],
    "sites": [
      {
        "site_id": "site-shackleton-01",
        "site_name": "Shackleton Rim Candidate Area",
        "is_placeholder": true,
        "coordinates": [-89.9, 0.0],
        "elevation_m": 600.0,
        "totals": {
          "sunlight_hours": 720.0,
          "earth_visible_hours": 301.0,
          "joint_sunlight_and_earth_visible_hours": 301.0,
          "total_simulation_hours": 720.0,
          "sunlight_fraction": 1.0,
          "earth_visible_fraction": 0.4181
        }
      }
    ],
    "disclaimers": [
      "Geometric visibility is not a guaranteed radio link.",
      "Sunlight is not guaranteed electrical power.",
      "Flat horizon ignores terrain shadowing; actual visibility depends on local topography.",
      "Planning support tool, not safety certification.",
      "Sun and Earth are treated as point sources at their barycenter/center."
    ]
  }
  ```

### `POST /api/v1/lunar/compare`
- **Owner:** Backend B (implemented in B5a)
- **SRS References:** LL-27, LL-28, LL-29, LL-30
- **Description:** Multi-site, multi-window terrain-aware comparison. For each (site, window) pair computes: slope and elevation from the DEM; illumination hours (terrain-aware, solar disk); Earth-visible hours (terrain-aware); hours when both Sun and Earth are above the terrain horizon; optional solar energy in kWh. User-supplied criteria (each labelled **"example threshold, not an official safety criterion"**) are evaluated per row. `best_by` picks the leading row for each metric. A combined score is never computed unless the user supplies weights. No site is labelled safe.
- **Request Body (JSON):**

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `site_ids` | list of strings | yes | 1–5, no duplicates | Site identifiers |
| `windows` | list of `{start, days}` | yes | 1–4, no duplicates | Time windows; `days` 1–60 |
| `step_minutes` | integer | no | ≥ 15, default 30 | Time step in minutes |
| `observer_height_m` | number | no | ≥ 0, default 0 | Observer height above DEM in metres |
| `criteria` | list of criterion objects | no | — | Optional pass/fail thresholds |
| `panel` | panel object | no | — | Optional; enables solar energy in kWh per row |

**Criterion object fields:** `metric` (one of `max_mean_slope_deg`, `min_any_lit_hours`, `min_earth_visible_hours`, `min_both_up_hours`, `max_longest_shadow_hours`), `threshold` (number), `label` (string, default `"example threshold, not an official safety criterion"`).

*Duration & Overlap Rule:* Each sample represents its entire step interval (e.g. 24 hourly steps cover 24.0 h). Boundary refinement with linear interpolation preserves the full duration of active intervals up to the simulation boundary. Overlap (`hours_both_up`) is strictly constrained: `hours_both_up <= min(hours_any_part_lit, hours_earth_visible)`.

- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (invalid parameters, bad date, site outside DEM coverage ≥ −75°S) | `503 Service Unavailable` (SPICE kernels missing).
- **Response Example (200 OK, abbreviated):**
  ```json
  {
    "id": 1,
    "label": "Modelled",
    "method": "SPICE DE421 Sun and Earth geometry; LOLA 240 m DEM local horizon ...",
    "kernels_used": ["naif0012.tls", "de421.bsp", "pck00010.tpc", "moon_pa_de421_1900-2050.bpc", "moon_080317.tf", "moon_assoc_me.tf"],
    "settings": {
      "site_ids": ["site-shackleton-01", "site-connecting-ridge-02"],
      "windows": [{"start": "2026-12-01", "days": 30}, {"start": "2027-01-01", "days": 30}],
      "step_minutes": 30,
      "observer_height_m": 0,
      "panel": null
    },
    "rows": [
      {
        "site_id": "site-shackleton-01",
        "site_name": "Shackleton Rim Candidate Area",
        "is_placeholder": true,
        "window_start": "2026-12-01",
        "window_days": 30,
        "observer_elevation_m": 624.6,
        "illumination": {
          "hours_any_part_lit": 353.87,
          "hours_fully_lit": 315.53,
          "hours_shadow": 366.13,
          "longest_shadow_hours": 342.98,
          "number_of_lit_windows": 3
        },
        "earth": {
          "hours_earth_visible": 338.36,
          "hours_earth_blocked": 381.64,
          "number_of_earth_windows": 1
        },
        "slope": {
          "mean_slope_deg": 4.2,
          "max_slope_deg": 28.1,
          "p90_slope_deg": 9.3
        },
        "elevation": {
          "mean_elevation_m": 605.0,
          "relief_m": 320.0
        },
        "hours_both_up": 310.5,
        "energy_kwh": null,
        "criteria_results": [
          {
            "metric": "max_mean_slope_deg",
            "threshold": 10.0,
            "label": "example threshold, not an official safety criterion",
            "value": 4.2,
            "passed": true
          }
        ],
        "data_quality": {
          "dem_resolution_m": 240,
          "is_placeholder": true,
          "kernels_used": ["naif0012.tls", "de421.bsp", "pck00010.tpc", "moon_pa_de421_1900-2050.bpc", "moon_080317.tf", "moon_assoc_me.tf"],
          "horizon_type": "terrain",
          "notes": [
            "240 m DEM cannot represent sub-resolution ridges, boulders, or micro-terrain.",
            "Illuminated fraction uses circular segment geometry (uniform solar disk).",
            "Earth visibility uses geometric line-of-sight; relay satellites are not modelled.",
            "Site is never labelled safe. These metrics support planning only."
          ]
        }
      }
    ],
    "best_by": {
      "best_for_sunlight": "site-shackleton-01:2026-12-01",
      "best_for_earth_visibility": "site-connecting-ridge-02:2027-01-01",
      "lowest_slope": "site-shackleton-01:2026-12-01",
      "most_hours_both_up": "site-shackleton-01:2026-12-01"
    },
    "criteria": [
      {
        "metric": "max_mean_slope_deg",
        "threshold": 10.0,
        "label": "example threshold, not an official safety criterion"
      }
    ],
    "disclaimers": [
      "Geometric visibility is not a guaranteed radio link.",
      "Sunlight is not guaranteed electrical power.",
      "A 240 m DEM cannot represent terrain smaller than its resolution; real terrain can differ.",
      "Planning support tool, not safety certification.",
      "No site is labelled safe. These metrics support planning only."
    ]
  }
  ```

### `GET /api/v1/lunar/compare/{id}/export`
- **Owner:** Backend B (implemented in B5a)
- **Description:** Returns the criteria, thresholds, settings and results of a stored comparison (created by `POST /api/v1/lunar/compare`).
- **Path Parameters:** `id` — comparison record integer id.
- **Query Parameters:** `format` — `json` (default) or `csv`.
- **Response Status:** `200 OK` (with `Content-Disposition: attachment`) | `404 Not Found` | `422 Unprocessable Entity` (invalid format).
- **Notes:** JSON export returns the full record including nested metrics per row. CSV export flattens each row into columns: `site_id`, `site_name`, `is_placeholder`, `window_start`, `window_days`, `observer_elevation_m`, all illumination/earth/slope/elevation fields, `hours_both_up`, `energy_kwh`.

### `GET /api/v1/lunar/sites/{id}/horizon`
- **Owner:** Backend B (implemented in B3b)
- **Description:** Computes the local terrain horizon profile from the 240 m LOLA polar stereographic DEM. For each azimuth (default 1° step from North clockwise towards East), performs ray marching at 1-pixel steps up to `max_distance_km`, computing topocentric elevation angles with spherical lunar curvature drop ($\Delta z = d^2 / (2R)$). Stops rays reaching the DEM coverage boundary (75°S).
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Query Parameters:**
  - `azimuth_step` (optional, float, default `1.0`): azimuth sampling interval in degrees (allowed: `0.1` to `45.0`).
  - `max_distance_km` (optional, float, default `100.0`): maximum horizon search distance in km (allowed: `1.0` to `500.0`).
  - `observer_height_m` (optional, float, default `0.0`): observer height above DEM surface in metres ($\ge 0.0$).
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (site outside 75°S coverage or invalid query parameters).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Derived",
    "product_id": "lola-dem-75s-240m",
    "resolution": "240 m/pixel (240.0 m/pix, true at south pole)",
    "observer_coordinates": [-89.9, 0.0],
    "observer_dem_elevation_m": 624.6,
    "observer_height_m": 0.0,
    "total_observer_elevation_m": 624.6,
    "reference_sphere_radius_km": 1737.4,
    "method": "Bilinear DEM ray marching with spherical curvature drop",
    "parameters": {
      "azimuth_step_deg": 1.0,
      "max_distance_km": 100.0,
      "observer_height_m": 0.0,
      "ray_step_m": 240.0
    },
    "summary": {
      "min_horizon_elevation_deg": -2.13,
      "max_horizon_elevation_deg": 22.25,
      "mean_horizon_elevation_deg": 7.02,
      "azimuth_of_max_elevation_deg": 135.0,
      "total_azimuths": 360,
      "cut_by_coverage_count": 0
    },
    "profile": [
      {
        "azimuth_deg": 0.0,
        "horizon_elevation_deg": -0.84,
        "distance_to_blocking_pixel_km": 50.4,
        "cut_by_coverage": false
      }
    ],
    "cut_by_coverage_azimuths": [],
    "disclaimers": [
      "A 240 m DEM cannot represent ridges, boulders, or micro-terrain smaller than its resolution, so the real horizon can be higher or lower.",
      "Planning support tool, not safety certification."
    ]
  }
  ```

### `GET /api/v1/lunar/sites/{id}/illumination`
- **Owner:** Backend B (implemented in B4a)
- **Description:** Computes the solar illumination timeline and continuous lit/shadow windows taking into account the local terrain horizon profile from the 240 m LOLA DEM and finite solar angular diameter. Models the Sun as a disk (radius 696,000 km from `pck00010.tpc`), computes the fractional area above the terrain horizon via circular segment geometry, and classifies each step into "lit" (fraction = 1.0), "partial" (0.0 < fraction < 1.0), or "shadow" (fraction = 0.0). Window boundaries are refined using linear interpolation between time steps.
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Query Parameters:**
  - `start` (required): UTC start date string (e.g. `2026-12-01` or ISO 8601).
  - `days` (optional, default `30`): simulation duration in days (minimum 1, maximum 60).
  - `step_minutes` (optional, default `30`): calculation time step in minutes (minimum 5).
  - `observer_height_m` (optional, default `0.0`): instrument/mast height in metres above DEM surface.
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (invalid parameters or site outside DEM coverage) | `503 Service Unavailable` (kernels missing).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Modelled",
    "frame": "MOON_ME_DE421",
    "product_id": "lola-dem-75s-240m",
    "method": "SPICE geometric with terrain horizon from a 240 m DEM",
    "observer_elevation_m": 624.6,
    "observer_height_m": 0.0,
    "total_observer_elevation_m": 624.6,
    "kernels_used": [
      "naif0012.tls",
      "de421.bsp",
      "pck00010.tpc",
      "moon_pa_de421_1900-2050.bpc",
      "moon_080317.tf",
      "moon_assoc_me.tf"
    ],
    "series": [
      {
        "timestamp": "2026-12-01T00:00:00Z",
        "sun_azimuth": 190.07,
        "sun_elevation": 1.39,
        "horizon_elevation_at_sun_azimuth": 8.42,
        "sun_angular_radius_deg": 0.2662,
        "illuminated_fraction": 0.0,
        "status": "shadow"
      }
    ],
    "windows": {
      "any_part_lit": [
        {
          "start": "2026-12-02T14:12:00Z",
          "end": "2026-12-13T17:35:00Z",
          "duration_hours": 267.38
        }
      ],
      "fully_lit": [
        {
          "start": "2026-12-02T14:48:00Z",
          "end": "2026-12-13T17:00:00Z",
          "duration_hours": 266.2
        }
      ]
    },
    "totals": {
      "hours_any_part_lit": 353.87,
      "hours_fully_lit": 315.53,
      "hours_shadow": 366.13,
      "total_simulation_hours": 720.0,
      "number_of_windows": 3,
      "shortest_window_hours": 12.43,
      "longest_window_hours": 267.38,
      "longest_continuous_shadow_hours": 342.98,
      "boundary_refinement_method": "linear interpolation between time steps"
    },
    "disclaimers": [
      "Geometric visibility is not a guaranteed radio link.",
      "Sunlight is not guaranteed electrical power.",
      "A 240 m DEM cannot represent terrain smaller than its resolution so real shadows can differ.",
      "Planning support tool, not safety certification.",
      "Low-angle sunlight near the horizon is not the same as usable power (cosine losses, local slope tilt, and partial obscuration)."
    ]
  }
  ```

### `GET /api/v1/lunar/sites/{id}/earth-visibility`
- **Owner:** Backend B (implemented in B4a)
- **Description:** Computes direct-to-Earth line-of-sight visibility against the local terrain horizon. Offers earth disk criterion (`center` by default or `upper_limb`). Classifies each time step into `clear` (Earth above terrain horizon), `blocked_by_terrain` (Earth above 0° but below terrain horizon), or `below_horizon` (Earth below 0° and below horizon). Identifies contiguous visibility windows with mean Earth azimuth and elevation per window. Relays are explicitly stated as not modelled (LL-21).
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Query Parameters:**
  - `start` (required): UTC start date string (e.g. `2026-12-01` or ISO 8601).
  - `days` (optional, default `30`): simulation duration in days (minimum 1, maximum 60).
  - `step_minutes` (optional, default `30`): calculation time step in minutes (minimum 5).
  - `observer_height_m` (optional, default `0.0`): instrument/mast height in metres above DEM surface.
  - `earth_disk` (optional, default `center`): criterion for line-of-sight (`center` or `upper_limb`).
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (invalid parameters or site outside DEM coverage) | `503 Service Unavailable` (kernels missing).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Modelled",
    "frame": "MOON_ME_DE421",
    "product_id": "lola-dem-75s-240m",
    "method": "SPICE geometric with terrain horizon from a 240 m DEM",
    "observer_elevation_m": 624.6,
    "observer_height_m": 0.0,
    "total_observer_elevation_m": 624.6,
    "kernels_used": [
      "naif0012.tls",
      "de421.bsp",
      "pck00010.tpc",
      "moon_pa_de421_1900-2050.bpc",
      "moon_080317.tf",
      "moon_assoc_me.tf"
    ],
    "earth_disk_criterion": "center",
    "series": [
      {
        "timestamp": "2026-12-01T00:00:00Z",
        "earth_azimuth": 173.32,
        "earth_elevation": 0.24,
        "horizon_elevation_at_earth_azimuth": -1.2,
        "effective_elevation_deg": 0.24,
        "earth_angular_radius_deg": 0.9507,
        "obstruction_status": "clear",
        "earth_visible": true
      }
    ],
    "windows": [
      {
        "start": "2026-12-01T00:00:00Z",
        "end": "2026-12-15T02:22:00Z",
        "duration_hours": 338.36,
        "mean_earth_azimuth": 174.15,
        "mean_earth_elevation": 2.85
      }
    ],
    "totals": {
      "earth_visible_hours": 338.36,
      "blocked_by_terrain_hours": 0.0,
      "below_horizon_hours": 381.64,
      "total_simulation_hours": 720.0,
      "earth_visible_fraction": 0.47,
      "number_of_windows": 1,
      "boundary_refinement_method": "linear interpolation between time steps"
    },
    "relay_communication": "not modelled",
    "relay_communication_note": "Direct-to-Earth line-of-sight only. Relay satellites or orbital nodes are not modelled (LL-21).",
    "disclaimers": [
      "Geometric visibility is not a guaranteed radio link.",
      "A 240 m DEM cannot represent terrain smaller than its resolution so real shadows can differ.",
      "Planning support tool, not safety certification.",
      "Direct-to-Earth line-of-sight only. Relay satellites are not modelled."
    ]
  }
  ```

### `POST /api/v1/lunar/sites/{id}/solar-estimate`
- **Owner:** Backend B (implemented in B4b)
- **SRS References:** LL-23, LL-24, LL-25, LL-26
- **Description:** Computes per-step direct solar irradiance on a panel and total energy over a requested period, reusing the terrain-aware illumination service (SPICE geometry + local DEM horizon). When no panel inputs are supplied, returns illumination opportunity statistics only. Observer elevation is taken from bilinear DEM interpolation at the site coordinates. The Sun and Earth are treated as point bodies for azimuth/elevation; the Sun disk radius is used only for the illuminated fraction computation in the underlying illumination service. No atmosphere, reflected light, degradation, temperature effects, batteries, or loads are modelled.
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Request Body (JSON):**

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `start` | string (ISO-8601 UTC) | yes | — | — | Start UTC datetime |
| `days` | integer | yes | — | 1–60 | Duration in days |
| `step_minutes` | integer | yes | — | 1–1440 | Time step in minutes |
| `observer_height_m` | number | no | 0.0 | ≥ 0 | Additional height above DEM surface in metres |
| `solar_constant_w_m2` | number | no | 1361.0 | > 0 | Solar irradiance at 1 AU (W/m²); distance-scaled per step via SPICE |
| `panel` | object | no | null | see below | Panel specification; omit for opportunity-only mode |

**Panel object fields** (all required when `panel` is present):

| Field | Type | Constraints | Description |
|---|---|---|---|
| `panel_area_m2` | number | > 0 | Panel area in m² |
| `efficiency` | number | 0 < x ≤ 1 | Panel conversion efficiency (dimensionless) |
| `tilt_deg` | number | 0–90 | Tilt from horizontal in degrees (0 = flat, 90 = vertical) |
| `panel_azimuth_deg` | number | 0–360 | Panel face azimuth (N=0, E=90, S=180, W=270) |
| `track_sun_azimuth` | boolean | — | If true, panel rotates to face Sun azimuth at each step (tilt_deg retained) |

- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (invalid parameters, bad date, site outside DEM coverage ≥ −75°S) | `503 Service Unavailable` (SPICE kernels not loaded).
- **Response Example (200 OK, with panel):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "observer_elevation_m": 624.6,
    "start": "2026-12-01T00:00:00+00:00",
    "end": "2026-12-31T00:00:00+00:00",
    "days": 30,
    "step_minutes": 30,
    "total_steps": 1439,
    "energy_wh": 2649.39,
    "energy_kwh": 2.649,
    "mean_power_w": 0.09,
    "peak_power_w": 0.44,
    "per_day_energy": [
      {"date": "2026-12-01", "energy_wh": 85.3},
      {"date": "2026-12-02", "energy_wh": 91.2}
    ],
    "illumination_opportunity": {
      "hours_any_part_lit": 353.87,
      "hours_fully_lit": 315.53,
      "hours_shadow": 366.13,
      "fraction_any_lit": 0.491,
      "fraction_fully_lit": 0.438,
      "shadow_windows": 3,
      "longest_shadow_hours": 342.98
    },
    "shadow_periods": [
      {
        "start": "2026-12-01T12:00:00+00:00",
        "end": "2026-12-15T18:58:00+00:00",
        "duration_hours": 342.98
      }
    ],
    "assumptions": [
      "No atmosphere: vacuum propagation, no Rayleigh or Mie scattering.",
      "No reflected or scattered light: direct beam only.",
      "No panel degradation, temperature effect, or ageing.",
      "No battery, load, or maximum-power-point tracking model.",
      "Panel is treated as a point; no self-shading.",
      "Solar constant 1361.0 W/m² at 1 AU; scaled by (1 AU / Sun-Moon distance)² at each step.",
      "Illuminated fraction from Sun-disk / terrain-horizon model in illumination service (approximation applied to irradiance)."
    ],
    "uncertainty": {
      "dem_resolution": "240 m DEM cannot represent sub-resolution ridges; real horizon may be higher or lower.",
      "solar_disk_approximation": "Illuminated fraction uses circular-segment geometry for a disk at the Sun azimuth; local topography within that azimuth range is not resolved.",
      "panel_model": "Cosine response assumes ideal planar panel. Real panels have angular response losses.",
      "spice_ephemeris": "DE421 ephemeris; sub-metre position errors are negligible at the scale of this model."
    },
    "disclaimers": [
      "Planning support tool, not safety or engineering certification.",
      "240 m DEM cannot represent terrain smaller than its resolution; real shadows can differ.",
      "No atmosphere, reflected light, degradation, thermal effects, or electrical losses are modelled."
    ],
    "method": "SPICE DE421 Sun geometry + LOLA 240m DEM local horizon; direct beam cosine irradiance model",
    "dem_product_id": "lola-dem-75s-240m",
    "label": "Derived"
  }
  ```
- **Response Example (200 OK, no panel — illumination opportunity only):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "is_placeholder": true,
    "observer_elevation_m": 624.6,
    "start": "2026-12-01T00:00:00+00:00",
    "end": "2026-12-31T00:00:00+00:00",
    "days": 30,
    "step_minutes": 30,
    "total_steps": 1439,
    "energy_wh": null,
    "energy_kwh": null,
    "mean_power_w": null,
    "peak_power_w": null,
    "per_day_energy": [],
    "illumination_opportunity": {
      "hours_any_part_lit": 353.87,
      "hours_fully_lit": 315.53,
      "hours_shadow": 366.13,
      "fraction_any_lit": 0.491,
      "fraction_fully_lit": 0.438,
      "shadow_windows": 3,
      "longest_shadow_hours": 342.98
    },
    "shadow_periods": [],
    "message": "No panel inputs provided. Supply panel_area_m2, efficiency, tilt_deg, panel_azimuth_deg, and track_sun_azimuth under a 'panel' key to receive an energy estimate.",
    "assumptions": [],
    "uncertainty": {},
    "disclaimers": [],
    "method": "SPICE DE421 Sun geometry + LOLA 240m DEM local horizon",
    "dem_product_id": "lola-dem-75s-240m",
    "label": "Derived"
  }
  ```

### `GET /api/v1/lunar/sites/{id}/slope`
- **Owner:** Backend B (implemented in B2)
- **Description:** Returns slope statistics (mean, max, percentiles p50/p90/p95, 10-bin histogram) computed via Horn's (1981) 8-neighbor gradient within the landing analysis footprint.
- **Path Parameters:** `id` — candidate landing site identifier (e.g. `site-shackleton-01`).
- **Response Status:** `200 OK` | `404 Not Found` (unknown site) | `422 Unprocessable Entity` (site latitude north of -75°S).
- **Response Example (200 OK):**
  ```json
  {
    "site_id": "site-shackleton-01",
    "site_name": "Shackleton Rim Candidate Area",
    "is_placeholder": true,
    "label": "Derived",
    "product_id": "lola-dem-75s-240m",
    "resolution": "240 m/pixel (240.0 m/pix, true at south pole)",
    "coverage": {
      "south_latitude": -90.0,
      "north_latitude": -75.0,
      "west_longitude": "not stated in label",
      "east_longitude": "not stated in label"
    },
    "vertical_reference": "Reference sphere radius: 1737.4 km (A_AXIS_RADIUS from label); OFFSET = 1737400.0 m; HEIGHT = DN * 0.5 (metres relative to reference sphere)",
    "no_data_value": null,
    "coordinate_reference_note": "DSMAP_POLAR.CAT Polar Stereographic (center lat -90 deg, center lon 0 deg, sphere radius 1737.4 km). NOT EPSG:4326.",
    "method": "Horn (1981) 8-neighbor finite difference",
    "units": "deg",
    "pixel_count": 57,
    "slope": {
      "mean_deg": 21.54,
      "max_deg": 22.53,
      "min_deg": 19.82,
      "p50_deg": 21.63,
      "p90_deg": 22.19,
      "p95_deg": 22.31,
      "method": "Horn (1981) 8-neighbor finite difference",
      "pixel_spacing_m": 240.0,
      "histogram": {
        "counts": [0, 0, 0, 0, 0, 0, 11, 46, 0, 0],
        "bin_edges_deg": [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0],
        "total_pixels": 57
      }
    },
    "criteria_result": {
      "slope_threshold_deg": 15.0,
      "threshold_label": "example threshold, not an official safety criterion",
      "exceeding_pixel_count": 57,
      "total_pixel_count": 57,
      "fraction_exceeding_threshold": 1.0,
      "percentage_exceeding_threshold": 100.0,
      "site_safety_disclaimer": "Site is never labelled safe. Threshold is an illustrative user parameter."
    },
    "scale_distortion_note": "Polar stereographic scale factor k = 2 / (1 + sin(|lat|)). At -90°S k=1.000; at the -75°S boundary k=1.0173 (approx 1.73% scale expansion). The distortion is documented and not corrected; estimated slope error due to distortion is < 2% at boundary.",
    "disclaimer": "A 240 m DEM baseline cannot detect or represent slopes, boulders, or micro-hazards at scales smaller than 240 m. Terrain cannot be certified as safe for landing."
  }
  ```

---

## 10. Map Layers & MMGIS Integration (Backend A — Phase 6 / SRS Section 13)

> ⚠️ **Coordinate System Note:** All GeoJSON layers use planetary coordinates (Mars or Moon), never Earth EPSG:4326.

### `GET /api/v1/map/layers/{mission_id}`
- **Owner:** Backend A & B (lunar layers added in B5b)
- **Description:** Returns list of available geospatial layer metadata for the given planetary mission or body (`mars-2020`, `artemis-lunar`, `moon`).
- **Path Parameters:** `mission_id` — e.g. `mars-2020`, `artemis-lunar`, `moon`
- **Response Status:** `200 OK` (array) | `404 Not Found`
- **Response Example (Moon mission `moon`):**
  ```json
  [
    {
      "id": "candidate_sites",
      "name": "Candidate Lunar Landing Sites",
      "type": "vector",
      "description": "Candidate Artemis polar landing sites with footprints (circular analysis radius or landing ellipse).",
      "geojson_url": "/api/v1/map/layers/moon/candidate_sites.geojson",
      "url": "/api/v1/map/layers/moon/candidate_sites.geojson",
      "label": "Derived",
      "source": "NASA Space Apps / Artemis Mission Planning",
      "source_product_id": "urn:nasa:lunar:artemis:candidate_sites",
      "is_placeholder": true,
      "disclaimer": "Candidate landing site points and footprint polygons. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification."
    },
    {
      "id": "illumination",
      "name": "Lunar Site Illumination Summary",
      "type": "vector",
      "description": "Per-site terrain-aware solar illumination window totals and parameters.",
      "geojson_url": "/api/v1/map/layers/moon/illumination.geojson",
      "url": "/api/v1/map/layers/moon/illumination.geojson",
      "label": "Modelled",
      "source": "SPICE ephemeris (DE421) + LOLA 240m DEM local horizon",
      "source_product_id": "lola-dem-75s-240m",
      "is_placeholder": true,
      "disclaimer": "Terrain-aware illumination summary points. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification."
    },
    {
      "id": "earth_visibility",
      "name": "Lunar Site Earth Visibility Summary",
      "type": "vector",
      "description": "Per-site direct-to-Earth line-of-sight visibility window totals and parameters.",
      "geojson_url": "/api/v1/map/layers/moon/earth_visibility.geojson",
      "url": "/api/v1/map/layers/moon/earth_visibility.geojson",
      "label": "Modelled",
      "source": "SPICE ephemeris (DE421) + LOLA 240m DEM local horizon",
      "source_product_id": "lola-dem-75s-240m",
      "is_placeholder": true,
      "disclaimer": "Terrain-aware direct-to-Earth line-of-sight visibility summary points. Frame is MOON_ME_DE421, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Geometric visibility is not a guaranteed radio link."
    },
    {
      "id": "lunar_dem",
      "name": "Lunar LOLA DEM (South Polar)",
      "type": "raster",
      "description": "Downsampled LOLA polar stereographic digital elevation model (1920 m/pixel preview).",
      "geojson_url": "/api/v1/map/layers/moon/lunar_dem.json",
      "url": "/api/v1/map/layers/moon/lunar_dem.png",
      "label": "Derived",
      "source": "NASA LOLA Science Team / PDS Geosciences Node",
      "source_product_id": "lola-dem-75s-240m",
      "is_placeholder": false,
      "disclaimer": "Polar stereographic projection true at south pole (-90 deg), MOON_ME_DE421 frame, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Cannot resolve sub-resolution micro-hazards."
    },
    {
      "id": "lunar_slope",
      "name": "Lunar LOLA Slope (South Polar)",
      "type": "raster",
      "description": "Downsampled LOLA polar stereographic slope map in degrees via Horn (1981) gradient.",
      "geojson_url": "/api/v1/map/layers/moon/lunar_slope.json",
      "url": "/api/v1/map/layers/moon/lunar_slope.png",
      "label": "Derived",
      "source": "Derived from LOLA DEM via Horn (1981) 8-neighbor gradient",
      "source_product_id": "lola-dem-75s-240m",
      "is_placeholder": false,
      "disclaimer": "Horn finite-difference slope map from LOLA DEM. Polar stereographic projection true at south pole, MOON_ME_DE421 frame, planetocentric latitude, east-positive longitude. Not an Earth coordinate system. Planning support tool, not safety certification."
    }
  ]
  ```

### `GET /api/v1/map/layers/{mission_id}/{layer_id}.json`
- **Owner:** Backend B (implemented in B5b)
- **Description:** Returns JSON sidecar metadata for lunar raster layers (`lunar_dem`, `lunar_slope`), containing exact bounds, label projection parameters, pixel size, colour scale, and coordinate reference notes.
- **Path Parameters:** `mission_id` (`moon`, `artemis-lunar`), `layer_id` (`lunar_dem`, `lunar_slope`)
- **Response Status:** `200 OK` (`application/json`) | `404 Not Found`

### `GET /api/v1/map/layers/{mission_id}/{layer_id}.png`
- **Owner:** Backend B (implemented in B5b)
- **Description:** Returns downsampled 8-bit preview PNG image for lunar raster layers (`lunar_dem`, `lunar_slope`).
- **Path Parameters:** `mission_id` (`moon`, `artemis-lunar`), `layer_id` (`lunar_dem`, `lunar_slope`)
- **Response Status:** `200 OK` (`image/png`) | `404 Not Found`

### `GET /api/v1/map/layers/{mission_id}/{layer_id}.geojson`
- **Owner:** Backend A
- **Description:** Returns RFC 7946 GeoJSON FeatureCollection in planetary coordinates.
- **Path Parameters:**
  - `mission_id` — e.g. `mars-2020`, `artemis-lunar`
  - `layer_id` — e.g. `historical-positions`, `traversed-route`, `candidate-lunar-sites`
- **Response Status:** `200 OK` (`application/geo+json`) | `404 Not Found`
- **Response Example (Mars positions):**
  ```json
  {
    "type": "FeatureCollection",
    "coordinate_reference_note": "Mars planetocentric lat/lon, east-positive, body-fixed frame name not stated in the label.",
    "properties": {
      "coordinate_reference_note": "Mars planetocentric lat/lon, east-positive, body-fixed frame name not stated in the label.",
      "explorer_id": "perseverance",
      "layer": "historical-positions",
      "total_features": 500
    },
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [77.4508, 18.4446]
        },
        "properties": {
          "explorer_id": "perseverance",
          "sol": -1,
          "sclk": "0",
          "observed_at": null,
          "label": "Estimated",
          "position_method": "interpolated",
          "source_product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
          "is_placeholder": false,
          "coordinate_frame": "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. Mars body-fixed frame name not stated in the label.",
          "units": "deg",
          "feature_role": "landing_site_reference"
        }
      }
    ]
  }
  ```

**Supported mission_id values:**
| `mission_id`     | Body  | Layers Available |
|------------------|-------|------------------|
| `mars-2020`      | Mars  | `historical-positions`, `traversed-route` |
| `artemis-lunar`  | Moon  | `candidate-lunar-sites` |

**GeoJSON Feature Properties per layer type:**

| Property | Description |
|----------|-------------|
| `explorer_id` | Rover or explorer ID |
| `sol` | Mars Sol number (-1 = landing site reference) |
| `sclk` | Spacecraft clock count (string) |
| `observed_at` | UTC timestamp or null (requires SPICE kernel) |
| `label` | `Estimated`, `Verified`, or `Unknown` |
| `position_method` | `interpolated`, `localized`, etc. |
| `source_product_id` | PDS product ID — use with `/api/v1/sources/{id}` for full provenance |
| `is_placeholder` | Boolean — preserved from source |
| `coordinate_frame` | Structured coordinate frame description from label |
| `units` | `deg` |
| `feature_role` | `drive_point`, `landing_site_reference`, `traversed_route`, `candidate_landing_site` |

**Rules:**
- Rows with `sol == -1` → `feature_role: landing_site_reference`, excluded from traversed route LineString
- Interpolated points always carry `label: Estimated`
- No EPSG:4326 reference anywhere in the output
- `coordinate_reference_note` present at top level and inside `properties`


---

## 11. AI Mission Assistant (Backend A — Phase 7 / SRS Section 16)

The AI Mission Assistant implements a **Hybrid Architecture: Keyword Retrieval + LLM Provider + Deterministic Template Fallback**.

### `POST /api/v1/assistant/query`
- **Owner:** Backend A
- **Description:** Submit research queries regarding mission telemetry, planetary coordinates, candidate landing sites, and scientific accuracy rules. Grounded strictly in official archives and approved reference knowledge.
- **Rate Limit:** 60 requests per 60-second window per client IP.
- **Request Body Limits:** `question` string: 1 to 500 characters maximum.
- **Request Example:**
  ```json
  {
    "question": "Where is the latest published position of Perseverance rover?"
  }
  ```
- **Response Status:** `200 OK` | `422 Unprocessable Entity` (length > 500 chars) | `429 Too Many Requests`
- **Response Example (Evidence Found):**
  ```json
  {
    "answer": "Perseverance latest published position: coordinates [18.4446, 77.4508] deg, Sol: 0, SCLK: 666952977. Position method: interpolated, status: estimated, label: Estimated. Coordinate frame: landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. Mars body-fixed frame name not stated in the label. Source product: urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv.",
    "citations": [
      {
        "source_name": "NASA PDS PLACES Localization Archive",
        "product_id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
        "url": "https://pds-geosciences.wustl.edu/missions/mars2020/places.htm",
        "label": "Estimated",
        "id": "urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv",
        "title": "NASA PDS PLACES Localization Archive",
        "api_path": "https://pds-geosciences.wustl.edu/missions/mars2020/places.htm"
      }
    ],
    "confidence_note": "Answer grounded in 1 verified archive/knowledge evidence source(s).",
    "evidence_found": true,
    "answer_mode": "template",
    "disclaimers": [
      "Coordinates are Mars planetocentric (east-positive), not Earth EPSG:4326.",
      "Contains interpolated positions labeled as Estimated."
    ]
  }
  ```
- **Lunar Evidence Sources & Citations:**
  Retrieval covers 8 lunar sources with citations containing `id`, `title`, and `api_path`:
  - `candidate_landing_sites`: `/api/v1/lunar/sites/{id}`
  - `terrain_products`: `/api/v1/lunar/products/{id}`
  - `terrain_metrics`: `/api/v1/lunar/sites/{id}/slope`
  - `illumination_results`: `/api/v1/lunar/sites/{id}/illumination`
  - `earth_visibility_windows`: `/api/v1/lunar/sites/{id}/earth-visibility`
  - `solar_power_estimates`: `/api/v1/lunar/sites/{id}/solar-estimate`
  - `landing_site_comparisons`: `/api/v1/lunar/compare/{id}/export?format=json`
  - `data_products` (SPICE kernels): `/api/v1/sources/{id}`
- **Operational Rules:**
  - Strict grounding in retrieved evidence. If no stored result exists, responds "Data not available" and specifies the API endpoint that computes it (e.g. `GET /api/v1/lunar/sites/{id}/geometry`, `/illumination`, etc.).
  - Distinguishes Measured, Derived, and Modelled data.
  - Flags placeholder records explicitly (`is_placeholder: true`).
  - Never certifies any site as safe; candidate sites are planning-support zones; notes 240 m DEM resolution limits.
  - Geometric visibility does not guarantee an established radio link; sunlight does not guarantee electrical power.
  - Raw evidence in `<EVIDENCE>` is strictly inert data, immune to prompt injection.
- **Response Example (No Evidence Found):**
  ```json
  {
    "answer": "Data not available in the approved sources.",
    "citations": [],
    "confidence_note": "No matching verified or approved evidence found in the official archives.",
    "evidence_found": false,
    "answer_mode": "template",
    "disclaimers": []
  }
  ```

### Anti-Hallucination & Safety Policies:
1. **Source Grounding**: If no evidence matches the query in official archives or knowledge documents, the assistant immediately returns `"Data not available in the approved sources."` with `evidence_found: false` and empty citations; the LLM is never invoked.
2. **Post-Check Validation**: Model responses containing forbidden terms (`"live location"`, `"live GPS"`, `"safe landing site"`) are rejected and automatically fall back to the deterministic template answer.
3. **Citations Provenance**: Citations are derived exclusively from retrieved database and knowledge items, never from model-generated text.
4. **Prompt-Injection Defense**: User questions and database evidence are passed inside strict `<EVIDENCE>` data delimiters with explicit model instructions to ignore any embedded directives.

---

## 12. Stub Endpoints (Backend A — Phase 1 / Deferred)

> These endpoints are placeholder stubs. Auth and admin role enforcement are intentionally deferred.

### `POST /api/v1/auth/login`
- **Owner:** Backend A
- **Status:** Placeholder — deferred to auth phase
- **Response Example:**
  ```json
  {"message": "Auth will be implemented in Phase 3", "is_placeholder": true}
  ```

### `GET /api/v1/auth/me`
- **Owner:** Backend A
- **Status:** Placeholder — deferred to auth phase
- **Response Example:**
  ```json
  {"user": null, "is_placeholder": true}
  ```

### `GET /api/v1/admin/status`
- **Owner:** Backend A
- **Status:** Placeholder — deferred to auth/admin phase
- **Response Example:**
  ```json
  {"admin_status": "active", "is_placeholder": true}
  ```

---

## 13. Endpoint Index

| Method | Path | Owner | Phase | Notes |
|--------|------|-------|-------|-------|
| `GET` | `/` | A | 1 | Root welcome |
| `GET` | `/health` | A | 1 | Liveness + DB type |
| `GET` | `/api/v1/status` | A | 1 | API version status |
| `GET` | `/api/v1/bodies` | A | 1 | List celestial bodies |
| `GET` | `/api/v1/bodies/{body_id}` | A | 1 | Body detail |
| `GET` | `/api/v1/missions` | A | 1 | List missions |
| `GET` | `/api/v1/missions/{mission_id}` | A | 1 | Mission detail |
| `GET` | `/api/v1/rovers` | A | 1 | List explorers/rovers |
| `GET` | `/api/v1/rovers/{rover_id}` | A | 1 | Rover detail |
| `GET` | `/api/v1/rovers/{rover_id}/locations` | A | 2 | Paginated PLACES locations |
| `GET` | `/api/v1/rovers/{rover_id}/latest-location` | A | 2 | Latest published position |
| `GET` | `/api/v1/rovers/{rover_id}/trajectory` | A | 2 | Traverse path |
| `GET` | `/api/v1/rovers/{rover_id}/images` | A | 2 | Image archive |
| `GET` | `/api/v1/rovers/{rover_id}/events` | A | 2 | Mission events |
| `GET` | `/api/v1/rovers/{rover_id}/health` | A | 2 | Rover health report |
| `GET` | `/api/v1/rovers/{rover_id}/analytics` | A | 2 | Distance & duration |
| `GET` | `/api/v1/rovers/{rover_id}/timeline` | A | 2 | Correlated timeline |
| `GET` | `/api/v1/sources/{product_id}` | A | 2 | Full data provenance |
| `GET` | `/api/v1/lunar/products/{id}` | B | B1a | Terrain product metadata & disclaimer |
| `GET` | `/api/v1/lunar/sites/{id}/terrain` | B | B2 | Terrain elevation stats, relief, RMS roughness |
| `GET` | `/api/v1/lunar/sites/{id}/slope` | B | B2 | Horn slope stats, distribution histogram, criteria |
| `GET` | `/api/v1/lunar/sites/{id}/geometry` | B | B3a | Topocentric sun/earth geometry, visibility windows & totals |
| `GET` | `/api/v1/lunar/compare` | B | B3a | Multi-site side-by-side visibility totals comparison |
| `GET` | `/api/v1/lunar/sites/{id}/horizon` | B | B3b | Topocentric local terrain horizon profile from LOLA DEM with spherical curvature drop |
| `GET` | `/api/v1/lunar/sites/{id}/illumination` | B | B4a | Terrain-aware solar illumination timeline, finite disk fraction & lit/shadow windows |
| `GET` | `/api/v1/lunar/sites/{id}/earth-visibility` | B | B4a | Direct-to-Earth line-of-sight visibility windows & obstruction status against local horizon |
| `POST` | `/api/v1/lunar/sites/{id}/solar-estimate` | B | B4b | Direct solar irradiance, panel energy estimate & illumination opportunity (LL-23 to LL-26) |
| `POST` | `/api/v1/lunar/compare` | B | B5a | Multi-site, multi-window terrain-aware comparison with criteria and best_by (LL-27 to LL-30) |
| `GET` | `/api/v1/lunar/compare/{id}/export` | B | B5a | Export stored comparison as JSON or CSV |
| `GET` | `/api/v1/lunar/sites` | A | 3 | List candidate landing sites |
| `POST` | `/api/v1/lunar/sites` | A | 3 | Create candidate site (unprotected) |
| `GET` | `/api/v1/lunar/sites/{site_id}` | A | 3 | Site detail |
| `PUT` | `/api/v1/lunar/sites/{site_id}` | A | 3 | Update site (unprotected) |
| `DELETE` | `/api/v1/lunar/sites/{site_id}` | A | 3 | Delete site (unprotected) |
| `GET` | `/api/v1/map/layers/{mission_id}` | A/B | 6/B5b | Layer metadata list (Mars & Moon) |
| `GET` | `/api/v1/map/layers/{mission_id}/{layer_id}.geojson` | A/B | 6/B5b | GeoJSON feature collection (Mars & Moon) |
| `GET` | `/api/v1/map/layers/{mission_id}/{layer_id}.json` | B | B5b | Lunar raster layer sidecar metadata |
| `GET` | `/api/v1/map/layers/{mission_id}/{layer_id}.png` | B | B5b | Lunar raster layer downsampled preview PNG |
| `POST` | `/api/v1/assistant/query` | A | 7 | AI research assistant |
| `POST` | `/api/v1/auth/login` | A | stub | Deferred |
| `GET` | `/api/v1/auth/me` | A | stub | Deferred |
| `GET` | `/api/v1/admin/status` | A | stub | Deferred |
