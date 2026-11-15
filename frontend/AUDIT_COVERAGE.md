# Frontend ↔ Backend Coverage Audit
**Generated:** 2026-11-15  
**Project:** NASA Lunar Landing Site Navigator  
**Backend root:** `BACKEND/`  **Frontend root:** `frontend/`

> [!IMPORTANT]
> All frontend services currently call `mockClient.ts`. **Zero real API calls are made today.**  
> This document records every gap so they can be closed systematically.

---

## Section 1 — Backend Endpoint Coverage Table

| # | Method | Path | Key query / body params | Key response fields | Frontend page / component | UI place to show it |
|---|--------|------|------------------------|--------------------|--------------------------|--------------------|
| 1 | GET | `/api/v1/health` | — | `status`, `version` | None | No |
| 2 | GET | `/api/v1/bodies` | — | `id`, `name`, `type` | None | No |
| 3 | GET | `/api/v1/bodies/{id}` | — | `id`, `name`, `radius_km`, `gm` | None | No |
| 4 | GET | `/api/v1/missions` | — | `id`, `name`, `body_id`, `status` | `MissionsPage` (mock) | Yes |
| 5 | GET | `/api/v1/missions/{id}` | — | full mission object | `MissionProfile` (mock) | Yes |
| 6 | GET | `/api/v1/rovers` | — | `id`, `name`, `mission_id`, `status` | `RoverList` (mock) | Yes |
| 7 | GET | `/api/v1/rovers/{id}` | — | full rover object | `RoverCard` (mock) | Yes |
| 8 | GET | `/api/v1/rovers/{id}/locations` | `limit`, `since` | `lat`, `lon`, `timestamp` | `MapView` (mock) | Yes |
| 9 | GET | `/api/v1/rovers/{id}/latest-location` | — | `lat`, `lon`, `timestamp` | `RoverCard` (mock) | Partly |
| 10 | GET | `/api/v1/rovers/{id}/trajectory` | `start`, `end` | `points[]` | `MapView` trajectory layer (mock) | Yes |
| 11 | GET | `/api/v1/rovers/{id}/images` | `limit`, `page` | `id`, `url`, `timestamp`, `hue` | `ImageGallery` (mock) | Yes |
| 12 | GET | `/api/v1/rovers/{id}/events` | `limit`, `type` | `id`, `type`, `description`, `ts` | `EventLog` (mock) | Yes |
| 13 | GET | `/api/v1/rovers/{id}/health` | — | `power_w`, `battery_pct`, `temp_c` | `HealthCard` (mock) | Yes |
| 14 | GET | `/api/v1/rovers/{id}/analytics` | `window` | `distance_km`, `uptime_pct` | `AnalyticsPanel` (mock) | Yes |
| 15 | GET | `/api/v1/rovers/{id}/timeline` | `start`, `end` | `events[]` | `Timeline` (mock) | Yes |
| 16 | GET | `/api/v1/map/layers/{mission_id}` | — | `layers[]` with name, type, url, source | `MapView` layer panel (mock) | Partly |
| 17 | GET | `/api/v1/sources/{product_id}` | — | `id`, `title`, `description`, `url`, `checksum` | `ProvenanceDrawer` (mock) | Partly |
| 18 | POST | `/api/v1/assistant/query` | `{question, mission_id, site_id}` | `answer`, `citations[]` | `AssistantPanel` (mock) | Partly |
| 19 | POST | `/api/v1/admin/login` | `{username, password}` | `token` | `AdminPage` (mock) | Partly |
| 20 | POST | `/api/v1/admin/ingest` | `{product_id}` + `x-admin-key` | `status` | `AdminPage` (mock) | Partly |
| 21 | GET | `/api/v1/lunar/sites` | `mission_id` | `id`, `name`, `lat`, `lon`, `is_placeholder` | `LunarPage` site list (mock) | Yes |
| 22 | POST | `/api/v1/lunar/sites` | `{name, lat, lon, ...}` + `x-admin-key` | created site | `AdminPage` create modal (mock) | Partly |
| 23 | GET | `/api/v1/lunar/sites/{id}` | — | full site object incl. labels | `LunarSiteCard` (mock) | Yes |
| 24 | PATCH | `/api/v1/lunar/sites/{id}` | `{name, notes}` + `x-admin-key` | updated site | `AdminPage` rename modal (mock) | Partly |
| 25 | DELETE | `/api/v1/lunar/sites/{id}` | `x-admin-key` header | `204` | `AdminPage` delete modal (mock) | Partly |
| 26 | GET | `/api/v1/lunar/sites/{id}/terrain` | — | `dem_resolution_m`, `is_placeholder` | `TerrainPanel` (mock) | Partly |
| 27 | GET | `/api/v1/lunar/sites/{id}/slope` | — | `mean_deg`, `max_deg`, `p90_deg`, `histogram` | `TerrainPanel` (mock) | Yes |
| 28 | GET | `/api/v1/lunar/sites/{id}/geometry` | `datetime`, `observer_height_m`, `earth_disk` | `sun_elevation`, `earth_elevation`, `illuminated_fraction` | `SunEarthPanel` (mock) | Partly |
| 29 | GET | `/api/v1/lunar/sites/{id}/horizon` | `step_az_deg`, `observer_height_m` | `profile[]`, `curvature_drop_deg`, `cut_by_coverage` | `HorizonChart` (partial mock) | Partly |
| 30 | GET | `/api/v1/lunar/sites/{id}/illumination` | `start`, `days`, `step_minutes` | `hours_lit`, `hours_full`, `hours_shadow`, `longest_shadow_h`, `windows[]` | `IlluminationCard` (mock) | Partly |
| 31 | GET | `/api/v1/lunar/sites/{id}/earth-visibility` | `start`, `days`, `step_minutes` | `hours_visible`, `hours_blocked_terrain`, `windows[]`, `status[]` | `EarthVisPanel` (mock) | Partly |
| 32 | POST | `/api/v1/lunar/sites/{id}/solar-estimate` | `{start, days, panel_area_m2, efficiency, tilt_deg, panel_azimuth_deg, track_sun_azimuth}` | `total_kwh`, `per_day[]` | `SolarCard` (mock) | Partly |
| 33 | GET | `/api/v1/lunar/compare` | `site_ids[]`, `start`, `days` | flat comparison rows | `ComparisonSection` (mock) | Partly |
| 34 | POST | `/api/v1/lunar/compare` | `{site_ids, windows:[{start,days}], step_minutes, criteria:{}, panel_inputs:{}}` | `rows[]`, `best_by{}`, `criteria_results{}` | `ComparisonSection` (mock) | Partly |
| 35 | GET | `/api/v1/lunar/compare/{id}/export` | `format=json\|csv` | file download | None | No |
| 36 | GET | `/api/v1/lunar/products/{id}` | — | `id`, `title`, `resolution_m`, `vertical_reference`, `sha256`, `pds_lid` | `ResearchSection` (mock) | Partly |

---

## Section 2 — Lunar Features Check

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 1 | **Terrain horizon profile from `/horizon` drawn on horizon chart** | **Partly** | `HorizonChart.tsx` plots `{az,el}[]` but reads it from `SunEarth` mock bundle; it never calls `/horizon` directly. Backend fields `curvature_drop_deg` and `cut_by_coverage` are not shown anywhere. |
| 2 | **`observer_height_m` input** | **No** | `Controls.tsx` has no mast-height field. Backend defaults to 0 m; every geometry/horizon call silently uses that. |
| 3 | **`earth_disk` option (`center` or `upper_limb`)** | **No** | No selector exists in the Controls or SolarCard panels. |
| 4 | **Illumination status (lit / partial / shadow) & illuminated fraction** | **Partly** | Timeline renders binary lit/shadow bands. `illuminated_fraction` (0–1) is never displayed; partial state is collapsed to either lit or shadow. |
| 5 | **Fully-lit vs any-part-lit hours** | **No** | Summary cards show only `total_sunlit_h`. `hours_full` (fully-lit) vs `hours_lit` (any-part) distinction is absent. |
| 6 | **Earth obstruction status (`clear`, `blocked_by_terrain`, `below_horizon`)** | **Partly** | Frontend TypeScript type uses `'clear' \| 'blocked' \| 'unknown'`; `blocked_by_terrain` and `below_horizon` sub-states are merged or dropped. |
| 7 | **Relay communication "not modelled" message** | **No** | No element in `LunarResults.tsx` or `Timelines.tsx` displays this planning limitation. |
| 8 | **Solar estimate inputs: `panel_azimuth_deg`, `track_sun_azimuth`, per-day energy** | **Partly** | `SolarCard.tsx` accepts `panel_area_m2`, `efficiency`, `tilt_deg` but lacks azimuth and tracking toggle. Per-day energy array `per_day[]` is never rendered. |
| 9 | **Slope percentiles and histogram** | **Yes** | `TerrainPanel.tsx` renders mean, max, p90 and a histogram. ✓ |
| 10 | **Criteria and thresholds with pass/fail and `best_by` labels in comparison** | **Partly** | `ComparisonSection.tsx` has a criteria table with pass/fail icons, but `best_by` tags (e.g. "best for sunlight") from the POST response are not shown. Criteria values are hard-coded mock. |
| 11 | **Multiple date windows (`windows:[{start,days}]`)** | **Partly** | Comparison lets users pick multiple dates but treats each as a point in time, not a window with a `days` duration. The POST body shape `windows[]` is not assembled by the frontend. |
| 12 | **Comparison export (JSON and CSV)** | **No** | No export button or trigger for `GET /compare/{id}/export`. |
| 13 | **`GET /lunar/products/{id}` details (DEM resolution, vertical reference, checksum)** | **Partly** | `ResearchSection.tsx` shows source name and description; `vertical_reference`, `sha256`, and `pds_lid` fields are never rendered. |
| 14 | **Site create, update, delete using `x-admin-key`** | **Partly** | `AdminPage.tsx` has modals for create/rename/delete but does not collect or send an `x-admin-key` header. |
| 15 | **Placeholder flags and labels (`Verified`, `Derived`, `Modelled`)** | **Yes** | `MethodChip` and `Chip` components display all three labels correctly. ✓ |
| 16 | **All required disclaimers** | **Yes** | `Disclaimer.tsx` covers planning support, radio link, electrical power, and DEM resolution. ✓ |

**Score: 3 fully covered, 8 partly, 5 missing.**

---

## Section 3 — Other Backend Features

| Feature | Status | Notes |
|---------|--------|-------|
| Map layers (`/map/layers/{mission_id}`) + layer toggles | **Partly** | `MapView` renders a toggle panel; layer URLs come from mock data, not the API. Lunar MMGIS layers (candidate_sites, illumination, lunar_dem, lunar_slope) not wired. |
| Sources / provenance drawer | **Partly** | `ProvenanceDrawer` opens when user clicks a source chip; content is mock. Fields `checksum`, `pds_lid`, `vertical_reference` never shown. |
| Rovers / locations / trajectory | **Partly** | Pages exist and render mock data; no real API call. |
| Rover images | **Partly** | Gallery renders mock. `ExplorerImage.hue` used for card gradient is a frontend-only synthetic field (see Section 4). |
| Rover events, health, analytics, timeline | **Partly** | All pages exist with mock data; not wired. |
| Assistant citations | **Partly** | `AssistantPanel` renders citation chips, but citations come from mock LLM response, not the backend's `citations[]` with `api_path`. |
| Admin ingest + login | **Partly** | `AdminPage` has login modal and ingest button; no real API call. |
| `GET /api/v1/bodies` | **No** | No page or component uses celestial body metadata. |
| `GET /api/v1/health` | **No** | No status badge or health indicator in the UI. |

---

## Section 4 — Frontend Features with NO Backend Support

| Frontend feature | Where | Notes |
|-----------------|-------|-------|
| **Live power / battery telemetry** (`power_w`, `battery_pct`) | `MissionProfile` cards | Backend `/rovers/{id}/health` returns these fields — but the frontend mock fabricates values and no field mapping exists yet. Backend field names differ (`power_w` vs mock `powerWatts`). |
| **Synthetic image hue** (`ExplorerImage.hue`) | `ImageGallery` card gradient | Backend `/rovers/{id}/images` has no `hue` field. Frontend generates a colour for card styling; a backend schema change or drop of this field is needed. |
| **Calculation settings tab** | `AdminPage` | No backend endpoint exposes or stores calculation parameters (step_minutes defaults, horizon step, etc.). |
| **Data imports audit table** | `AdminPage` "Data Imports" tab | No backend endpoint lists past ingest jobs or their status/timestamps. |
| **Confidence flags on AI statements** | `AssistantPanel` | Frontend annotates each sentence with a confidence icon; backend `citations[]` carries no per-statement confidence score. |

---

## Section 5 — Gaps List

### Group A — Backend has it, frontend lacks UI

| Priority | Gap |
|----------|-----|
| 🔴 High | `/horizon` standalone fetch: `curvature_drop_deg`, `cut_by_coverage`, metadata not shown |
| 🔴 High | `observer_height_m` input missing from all controls |
| 🔴 High | Partial illumination fraction (`illuminated_fraction`) never rendered; fully-lit vs any-part-lit hours absent |
| 🔴 High | Earth obstruction three-state (`clear`, `blocked_by_terrain`, `below_horizon`) collapsed to two states |
| 🔴 High | Solar panel azimuth (`panel_azimuth_deg`) and tracking (`track_sun_azimuth`) inputs absent; per-day energy array not rendered |
| 🔴 High | Multi-window comparison (`windows:[{start,days}]`) POST body never assembled; durations not supported |
| 🟡 Medium | `earth_disk` selector (`center` vs `upper_limb`) missing |
| 🟡 Medium | Relay satellite "not modelled" note absent |
| 🟡 Medium | `best_by` labels not shown in comparison table |
| 🟡 Medium | Comparison export buttons (JSON / CSV) missing |
| 🟡 Medium | `x-admin-key` header not collected or sent in Admin page |
| 🟡 Medium | MMGIS lunar layers not wired into map layer panel |
| 🔵 Low | `vertical_reference`, `sha256`, `pds_lid` from `/lunar/products/{id}` not shown |
| 🔵 Low | Flat-horizon GET `/lunar/compare` unused (UI always uses POST) |
| 🔵 Low | `/api/v1/health` not shown as a status badge |
| 🔵 Low | `/api/v1/bodies` metadata unused |

**Group A totals — High: 6 · Medium: 6 · Low: 4**

### Group B — Frontend has UI, backend lacks data

| Priority | Gap |
|----------|-----|
| 🟡 Medium | `ExplorerImage.hue` for card gradient — no backend field; schema addition or frontend removal needed |
| 🟡 Medium | Live power / battery field-name mismatch (`power_w` vs `powerWatts`) |
| 🔵 Low | Calculation settings tab — no backend CRUD for step parameters |
| 🔵 Low | Data imports audit table — no backend job history endpoint |
| 🔵 Low | Per-statement AI confidence flags — no backend confidence score |

**Group B totals — High: 0 · Medium: 2 · Low: 3**

---

## Section 6 — Proposed Adapter Plan (`frontend/src/services/api.ts`)

The plan is a **single drop-in adapter file** that replaces every `mockClient` call with a real `fetch`.  
No other source files change except adding one line in each service: replace `mockClient` import with `apiClient`.

### 6.1 Constants

```ts
// frontend/src/services/api.ts
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';
const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY ?? '';
```

### 6.2 Generic helper

```ts
async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(BASE + path);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown, adminKey = false): Promise<T> {
  const headers: Record<string,string> = { 'Content-Type': 'application/json' };
  if (adminKey) headers['x-admin-key'] = ADMIN_KEY;
  const res = await fetch(BASE + path, { method: 'POST', headers, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}
```

### 6.3 Callers and field mappings

| Service function | Endpoint | Backend field → Frontend field |
|-----------------|----------|-------------------------------|
| `getSites(missionId)` | `GET /lunar/sites?mission_id=…` | `is_placeholder`, `name`, `lat`, `lon` → direct |
| `getSite(id)` | `GET /lunar/sites/{id}` | direct |
| `createSite(data)` | `POST /lunar/sites` + `x-admin-key` | direct |
| `updateSite(id, data)` | `PATCH /lunar/sites/{id}` + `x-admin-key` | direct |
| `deleteSite(id)` | `DELETE /lunar/sites/{id}` + `x-admin-key` | 204 → void |
| `getHorizon(id, params)` | `GET /lunar/sites/{id}/horizon` | `profile[]`, `curvature_drop_deg`, `cut_by_coverage` → new fields in `HorizonChart` |
| `getGeometry(id, params)` | `GET /lunar/sites/{id}/geometry` | `sun_elevation`, `earth_elevation`, `illuminated_fraction` (add fraction to component) |
| `getIllumination(id, params)` | `GET /lunar/sites/{id}/illumination` | `hours_lit` (any-part), `hours_full` (fully-lit) → show both; `longest_shadow_h` → card |
| `getEarthVisibility(id, params)` | `GET /lunar/sites/{id}/earth-visibility` | `hours_visible`, `hours_blocked_terrain`, `hours_below_horizon` → three-state chip |
| `getSolarEstimate(id, body)` | `POST /lunar/sites/{id}/solar-estimate` | `total_kwh`, `per_day[]` → add per-day chart |
| `compareSites(body)` | `POST /lunar/compare` | `rows[]`, `best_by{}`, `criteria_results{}` → show best_by badges |
| `exportComparison(id, fmt)` | `GET /lunar/compare/{id}/export?format=…` | download via `<a href>` |
| `getProduct(id)` | `GET /lunar/products/{id}` | add `vertical_reference`, `sha256`, `pds_lid` to drawer |
| `getMapLayers(missionId)` | `GET /map/layers/{mission_id}` | `layers[]` → wire into MapView toggle panel |
| `getSource(productId)` | `GET /sources/{productId}` | direct → ProvenanceDrawer |
| `askAssistant(body)` | `POST /assistant/query` | `answer`, `citations[]` (each with `api_path`) → render citation chips |
| `getRoverHealth(id)` | `GET /rovers/{id}/health` | `power_w` → `powerWatts`, `battery_pct` → direct |
| `getRoverImages(id)` | `GET /rovers/{id}/images` | drop `hue`; derive gradient from `timestamp` hash client-side |
| `getMissions()` | `GET /missions` | direct |
| `getRovers()` | `GET /rovers` | direct |

### 6.4 Env vars to add to `.env.local`

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_ADMIN_KEY=<your-x-admin-key>
```

### 6.5 Rollout sequence (zero-risk)

1. Create `frontend/src/services/api.ts` with all callers above.  
2. For each service file swap `import { mockClient }` → `import * as api from './api'`.  
3. Fix the five field-name mismatches listed in Group B.  
4. Add the six missing UI controls (Group A High items) in a follow-up PR.  
5. Add `VITE_API_URL` to `frontend/.env.local` (git-ignored).

---

*End of audit. No production files were modified.*
