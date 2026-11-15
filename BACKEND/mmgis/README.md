# MMGIS Integration — Space Explorer (Phase 6 / SRS Section 13)

> **DRAFT** — All config files are draft only. They have NOT been verified against a pinned MMGIS version.  
> You MUST pin and verify an MMGIS version before using these configs in production.

---

## What is MMGIS?

[NASA-AMMOS MMGIS](https://github.com/NASA-AMMOS/MMGIS) is a web-based multi-mission geospatial information system for planetary surface operations. It runs as a **standalone Node.js service** — it is NOT part of this Python/FastAPI backend.

---

## Architecture Overview

```
[FastAPI Backend]  ──GeoJSON API──►  [MMGIS Node.js]  ──displays──►  [Browser / Frontend]
  /api/v1/map/layers/{mission_id}
  /api/v1/map/layers/{mission_id}/{layer_id}.geojson
```

MMGIS is configured to load GeoJSON layers from live URLs served by this backend.  
Each feature in the GeoJSON includes `source_product_id` so the frontend can call `/api/v1/sources/{product_id}` for full provenance.

---

## Coordinate System Warning

> ⚠️ **These are NOT Earth/EPSG:4326 coordinates.**
> - Mars layers: Mars planetocentric lat/lon, east-positive. Body-fixed frame name not stated in label.
> - Moon layers: MOON_ME_DE421 (Mean Earth/Polar Axis, DE421 ephemeris).
>
> MMGIS must be configured with the correct planetary CRS/projection for Mars or Moon, NOT the default Web Mercator or WGS84.

---

## How to Point MMGIS at the GeoJSON Layer URLs

1. **Pin an MMGIS version** in your Docker/Node setup — test against that exact version before deploying.
2. Start the FastAPI backend (default: `http://localhost:8000`).
3. In MMGIS, add a GeoJSON layer for each mission:

| Mission       | Layer ID                  | URL                                                                               |
|---------------|---------------------------|-----------------------------------------------------------------------------------|
| `mars-2020`   | `historical-positions`    | `http://<backend>/api/v1/map/layers/mars-2020/historical-positions.geojson`      |
| `mars-2020`   | `traversed-route`         | `http://<backend>/api/v1/map/layers/mars-2020/traversed-route.geojson`           |
| `artemis-lunar` | `candidate-lunar-sites` | `http://<backend>/api/v1/map/layers/artemis-lunar/candidate-lunar-sites.geojson` |

4. For the layer metadata list (id, name, type, geojson_url, label, etc.):
   - `GET /api/v1/map/layers/{mission_id}`

5. Verify MMGIS is loading planetary CRS (Mars 2000 / `ESRI:104905` or Moon 2000 / `ESRI:103882`).

---

## Directory Structure

```
mmgis/
├── README.md                          ← This file
├── config/
│   ├── mars.json                      ← DRAFT Mars map config (projection, basemap, layer refs)
│   ├── moon.json                      ← DRAFT Moon map config
│   └── layers/
│       ├── mars_positions.json        ← DRAFT Perseverance historical positions layer
│       ├── mars_route.json            ← DRAFT Perseverance traversed route layer
│       └── moon_candidate_sites.json  ← DRAFT Artemis candidate lunar sites layer
└── plugins/                           ← MMGIS plugins (future)
```

---

## Backend API Endpoints (Phase 6)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/map/layers/{mission_id}` | Layer metadata list (id, name, type, geojson_url, label, source, is_placeholder, disclaimer) |
| `GET` | `/api/v1/map/layers/{mission_id}/{layer_id}.geojson` | GeoJSON FeatureCollection for the layer |

Supported `mission_id` values: `mars-2020`, `artemis-lunar`  
Supported layer IDs (Mars): `historical-positions`, `traversed-route`  
Supported layer IDs (Moon): `candidate-lunar-sites`

---

## GeoJSON Feature Properties

Every feature includes:
- `explorer_id` / `body_id`
- `sol`, `sclk`, `observed_at`
- `label` (Estimated / Unknown / Verified)
- `position_method`
- `source_product_id` → use to call `/api/v1/sources/{source_product_id}` for provenance
- `is_placeholder`
- `coordinate_frame`
- `feature_role` (`drive_point`, `landing_site_reference`, `traversed_route`, `candidate_landing_site`)

Landing site reference rows (sol == -1) are exported as separate Point features with `feature_role: landing_site_reference` and are **excluded from the traversed route LineString**.

---

## Important Notes

- MMGIS is NOT installed in this repository. Do not run `npm install` or any MMGIS commands here.
- Config files in `mmgis/config/` are drafts for reference only.
- Always verify MMGIS version compatibility before using these configs.
- Do NOT treat planetary coordinates as EPSG:4326 in MMGIS CRS settings.
