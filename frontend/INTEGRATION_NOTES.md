# Frontend ↔ Backend Integration Notes

**Date:** 2026-11-15  
**Status:** Completed and verified against live backend (FastAPI on `http://localhost:8000`).  
**Mode:** Real backend exclusively (`VITE_USE_MOCK` and mockClient have been completely removed).

---

## 1. Connected Real Endpoints

All services in `frontend/src/services/` connect directly to the real backend via `api.ts`:

| Category | Endpoint | Method | Frontend Service Function | Purpose / Notes |
|---|---|---|---|---|
| **System** | `/health` | `GET` | `api.getHealth()` | Root health check reporting service status and database connectivity. |
| **Missions** | `/api/v1/missions` | `GET` | `getMissions()`, `getAllMissions()`, `getBodies()` | Real mission list filtering for Mars and Moon; derives body list and mission counts. |
| **Missions** | `/api/v1/missions/{id}` | `GET` | `getMission()` | Enriched mission metadata pulling real events, latest location, timeline, and health. |
| **Rovers** | `/api/v1/rovers` | `GET` | `api.getRovers()` | List of explorers with operational status and data labels. |
| **Rovers** | `/api/v1/rovers/{id}` | `GET` | `api.getRover()` | Detailed explorer record with mission association and explorer type. |
| **Rovers** | `/api/v1/rovers/{id}/locations` | `GET` | `getExplorerLocations()` | Historical rover localized positions with sol/sclk fallback, labels, and coordinate frames. Paginated loop fetches all 502 records. |
| **Rovers** | `/api/v1/rovers/{id}/latest-location`| `GET` | `api.getRoverLatestLocation()` | Most recent localized position record used by mission profile and map views. |
| **Rovers** | `/api/v1/rovers/{id}/trajectory` | `GET` | `api.getRoverTrajectory()` | Rover traverse segments and path coordinates. |
| **Rovers** | `/api/v1/rovers/{id}/events` | `GET` | `api.getRoverEvents()` | Operational log events for the explorer. |
| **Rovers** | `/api/v1/rovers/{id}/analytics` | `GET` | `api.getRoverAnalytics()` | Traverse analytics, verified odometer distance in km, and duration. |
| **Rovers** | `/api/v1/rovers/{id}/timeline` | `GET` | `api.getRoverTimeline()` | Unified operational event timeline. |
| **Rovers** | `/api/v1/rovers/{id}/images` | `GET` | `getExplorerImages()` | Rover image gallery with camera, sol, and date range filters. Hotlinked to real NASA CDN images. |
| **Rovers** | `/api/v1/rovers/{id}/health` | `GET` | `api.HealthRoverRaw` | Real health status (`condition`, `evidence`). |
| **Sources** | `/api/v1/sources/{product_id}` | `GET` | `getSource()` | Real rover and planetary data source provenance with coordinate frame, checksum, and uncertainty. |
| **Map** | `/api/v1/map/layers/{mission_id}` | `GET` | `getMapLayers()` | GeoJSON and metadata layers for candidate sites, route, and historical positions. |
| **Lunar Sites** | `/api/v1/lunar/sites` | `GET` | `getSites()` | Real candidate landing site list with `coordinates.values` (`[lat, lon]`) and `frame`. |
| **Lunar Terrain** | `/api/v1/lunar/sites/{id}/terrain` | `GET` | `getTerrain()` | Elevation stats, DEM resolution, reference sphere, local relief. |
| **Lunar Slope** | `/api/v1/lunar/sites/{id}/slope` | `GET` | `getTerrain()` | Horn finite difference slope stats (mean, max, p50, p90, p95) and binned histogram. |
| **Lunar Geometry** | `/api/v1/lunar/sites/{id}/illumination` | `GET` | `getSunEarth()`, `getWindows()` | SPICE geometric sunlight series, `illuminated_fraction`, lit/shadow windows. |
| **Lunar Visibility**| `/api/v1/lunar/sites/{id}/earth-visibility` | `GET` | `getSunEarth()`, `getWindows()` | Direct-to-Earth line-of-sight elevation, obstruction classification, visibility windows. |
| **Lunar Horizon** | `/api/v1/lunar/sites/{id}/horizon` | `GET` | `api.HorizonRaw` | Horizon profile with curvature drop and coverage limits. |
| **Solar Power** | `/api/v1/lunar/sites/{id}/solar-estimate` | `POST` | `estimateSolar()` | Terrain-aware solar irradiance, shadow periods, and power estimates. |
| **Comparison** | `/api/v1/lunar/compare` | `POST` | `compareSites()` | Multi-site multi-window terrain-aware landing criteria evaluation. |
| **Assistant** | `/api/v1/assistant/query` | `POST` | `askAssistant()` | Evidence-grounded Q&A with citations, product IDs, and disclaimers. |
| **Lunar Products**| `/api/v1/lunar/products/{id}` | `GET` | `getSource()` | Real provenance drawer with PDS citation, vertical reference, coordinate frame, and checksum. |

---

## 2. Cleanups & Architectural Alignment

1. **Purged Mock Infrastructure:**
   - Deleted `frontend/src/services/mockClient.ts` and `frontend/src/mocks/`.
   - Removed `VITE_USE_MOCK` branching in services and UI components.
   - Removed all mock and placeholder chips not backed by real `is_placeholder` flags.

2. **Purged Unsupported Features & Admin Mutations:**
   - Deleted Admin page (`/admin`) and removed admin links from navigation.
   - Removed candidate site creation/update/deletion forms (write operations are not exposed to the public frontend).
   - Removed `VITE_ADMIN_KEY` configuration and `x-admin-key` transmission.
   - Removed top-nav Mission Compare link (`/compare`); preserved multi-site comparison inside the Lunar Navigator.
   - Removed ungrounded Elevation Profile chart; preserved Horn finite difference slope histogram and stats.
   - Replaced live power/battery cards with real Health condition and evidence reporting.
   - Removed AI per-sentence confidence icons; preserved grounded citations and source provenance drawer.

3. **Rover Real Images Pipeline (FR-15 to FR-18):**
   - Implemented real Mars 2020 raw image import pipeline from `mars.nasa.gov` raw images feed.
   - 100 images imported into database with `sol`, `camera`, `captured_at`, `image_url`, `product_id`, and `is_placeholder=False`.
   - Gallery renders real NASA CDN hotlinks with fallback neutral tiles on error.

4. **Time Machine & Map Alignments:**
   - Dynamic explorer ID resolution mapping missions to rovers via `/rovers`.
   - Sol-driven scrub on Time Machine when `observed_at` is null (preserving PLACES SCLK telemetry).
   - Plain coordinate plot for Mars locations (East Longitude horizontal, Planetocentric Latitude vertical, IAU 2000). Route line connects traverse points; landing reference is rendered separately.

5. **Lunar Timeline Formatting:**
   - Simulation day window end timestamps ending at midnight format as `24:00` instead of ambiguous `00:00`.
