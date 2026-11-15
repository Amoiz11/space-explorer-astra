# Backend B Status Report: Lunar Landing Site Navigator
**SRS Reference:** Section 26 (LL-01 to LL-30) & Section 31 (Acceptance Criteria)  
**Date:** 15 November 2026  
**Status Version:** v1.0

---

## 1. Lunar Landing Functional Requirements (LL-01 to LL-30)

| Requirement | Title / Scope | Status | Honest Verification Evidence |
| :--- | :--- | :---: | :--- |
| **LL-01** | Candidate landing site add, edit, select, and compare | **Done** | `POST/GET /api/v1/lunar/sites`, `PATCH/DELETE /sites/{id}`, and `POST /compare` implemented and verified. |
| **LL-02** | Site ID, name, coordinates, frame, ellipse/radius, notes | **Done** | `CandidateLandingSite` stores id, name, coordinates (lat/lon), frame `MOON_ME_DE421`, analysis radius, ellipse, and notes. |
| **LL-03** | Multiple sites map and comparison table view | **Done** | `POST /compare` returns tabular multi-site rows; `/api/v1/map/layers/lunar` exports candidate_sites GeoJSON for MMGIS. |
| **LL-04** | User-defined landing ellipse and analysis radius | **Done** | `CandidateLandingSiteBase` schema accepts `analysis_radius_m` or `semi_major_m`, `semi_minor_m`, `orientation_deg`. |
| **LL-05** | No automatic 'safe' declaration; criteria and thresholds | **Done** | Endpoints prohibit certifying safety; thresholds are explicitly labelled as user-supplied examples, not safety criteria. |
| **LL-06** | Extraction of elevation from Lunar DEM | **Done** | Bilinear interpolation of 240 m/pixel LOLA polar stereographic DEM extracts elevation and enforces 75°S boundary. |
| **LL-07** | Slope calculation from DEM with clear units | **Done** | Sobel 8-neighbour gradient slope processor computes slopes with units explicitly specified as degrees. |
| **LL-08** | Slope statistics (mean, max, percentiles, distribution) | **Done** | `GET /sites/{id}/slope` computes mean, max, p50, p90, p95, and histogram distribution over circular radius or ellipse. |
| **LL-09** | Terrain roughness and local relief extension | **Partly** | Local relief (elevation min/max difference) is computed; RMS roughness metric remains a documented placeholder. |
| **LL-10** | DEM resolution, coverage, vertical reference, no-data | **Done** | `GET /lunar/products/lola-dem-75s-240m` and `/terrain` report 240 m/pix, 75°S coverage, 1737.4 km radius, and no-data note. |
| **LL-11** | User date/time selection for site analysis | **Done** | All lunar geometry, illumination, visibility, and comparison endpoints accept UTC start, step_minutes, and days. |
| **LL-12** | SPICE solar position calculation | **Done** | `spkpos("SUN", et, "MOON_ME_DE421", "LT+S", "MOON")` using NAIF kernels calculates topocentric solar vectors. |
| **LL-13** | Sun azimuth and elevation relative to local horizon | **Done** | Topocentric azimuth (degrees clockwise from North) and elevation above horizontal plane computed in ENU basis. |
| **LL-14** | Terrain shadowing evaluation from DEM/horizon model | **Done** | `horizon_processor.py` marches rays up to 100 km over 240 m DEM accounting for lunar spherical curvature drop ($d^2 / 2R$). |
| **LL-15** | Illumination duration and shadow periods estimate | **Done** | `illumination_service.py` calculates total lit hours, shadow hours, longest continuous shadow, and discrete lit windows. |
| **LL-16** | Low-angle solar illumination and terrain blockage | **Done** | Circular segment geometry evaluates solar disk fraction ($R_\odot \approx 0.26^\circ$) above local interpolated horizon. |
| **LL-17** | Earth apparent position calculation via SPICE | **Done** | `spkpos("EARTH", et, "MOON_ME_DE421", "LT+S", "MOON")` in `lunar_geometry_service` calculates topocentric Earth vectors. |
| **LL-18** | Earth azimuth and elevation relative to local horizon | **Done** | Earth azimuth and elevation reported at every simulation time step in local topocentric ENU coordinates. |
| **LL-19** | Earth line-of-sight obstruction against terrain horizon | **Done** | Earth visibility processor evaluates Earth center/upper limb against horizon, classifying steps into `clear`, `blocked_by_terrain`, `below_horizon`. |
| **LL-20** | Direct-to-Earth visibility windows with start/end times | **Done** | Contiguous clear visibility windows reported with ISO start/end timestamps, duration hours, and mean azimuth/elevation. |
| **LL-21** | Separation of relay communication from Direct-to-Earth | **Done** | Responses explicitly include `relay_communication_note` stating orbital relays are not modelled. |
| **LL-22** | Geometric line-of-sight disclaimer vs. radio link | **Done** | Mandatory disclaimer states geometric visibility does not guarantee an established RF radio communication link. |
| **LL-23** | Solar exposure estimation over date range | **Done** | `solar_power_service.py` computes total sunlight opportunity hours, fraction of period lit, and shadow periods up to 60 days. |
| **LL-24** | Electrical energy estimate with panel assumptions | **Done** | Computes energy from panel area, efficiency, tilt, azimuth, tracking mode, and user-overridable solar constant ($1361\text{ W/m}^2$). |
| **LL-25** | Units, assumptions, shadow periods, and uncertainty | **Done** | Energy reported in Wh, lists 7 explicit physical assumptions (direct beam only, no albedo/reflections, etc.), and cites 4 uncertainty factors. |
| **LL-26** | Illumination opportunity report when panel not configured | **Done** | If panel inputs are omitted, energy is not computed; response returns sunlight opportunity hours and guidance message. |
| **LL-27** | Multiple landing date windows comparison for single site | **Done** | `POST /api/v1/lunar/compare` evaluates multiple time windows for a site and reports comparative metric rows. |
| **LL-28** | Multi-site and multi-date combined comparison | **Done** | `POST /api/v1/lunar/compare` processes up to 5 sites and 4 windows (up to 20 combinations) in a single request. |
| **LL-29** | Inclusion of slope, illumination, visibility, and quality | **Done** | Each comparison row details DEM slope (mean, max, p90), elevation stats, sunlight hours, Earth visibility, and data quality. |
| **LL-30** | Criteria, thresholds, and comparison export | **Done** | User criteria pass/fail evaluated per row, results saved to DB, and exported via `GET /compare/{id}/export?format=json|csv`. |

---

## 2. Updated Testing and Acceptance Criteria (SRS Section 31)

| Criterion | Description | Status | Honest Verification Evidence |
| :--- | :--- | :---: | :--- |
| **AC-01** | DEM/elevation output validated from reference product | **Done** | Verified against NASA LOLA 240 m product `lola-dem-75s-240m` with 1737.4 km reference sphere. |
| **AC-02** | Slope calculation verified on controlled synthetic DEM | **Done** | `test_slope_processor.py` verified flat (0°), constant 10° tilted plane, and pyramid terrain analytically. |
| **AC-03** | Sun/Earth geometry cross-checked with SPICE reference | **Done** | Independent cross-check against `spice.ilumin` across Dec 2026; max diff: Sun 0.000016°, Earth 0.000119° (< 0.05°). |
| **AC-04** | Local horizon visible and blocked scenarios tested | **Done** | `test_horizon_processor.py` tests ray marching across 360 azimuths, spherical curvature drop, and 75°S boundary cut. |
| **AC-05** | Visibility window start/end boundary cases verified | **Done** | `test_illumination_and_earth_visibility.py` verifies window transitions, partial disk rise/set boundaries, and step boundaries. |
| **AC-06** | Solar estimate accepted with documented assumptions | **Done** | `test_solar_power.py` validates energy integration in Wh, cosine projection, tracking, and explicit assumption listings. |
| **AC-07** | Site comparison reproducible on same inputs | **Done** | `test_validation.py` validates that submitting identical requests twice yields identical responses across all lunar endpoints. |
| **AC-08** | Map layers show source, resolution, version, coverage | **Done** | MMGIS config files and `/api/v1/map/layers/lunar` document source product, 240 m resolution, version, and coverage. |
| **AC-09** | System does not make definitive 'safe site' claims | **Done** | Disclaimers enforced across schemas, APIs, system prompts, and template answers; safety certification prohibited. |

---

## 3. Summary of Status Counts

- **LL-01 to LL-30:**
  - **Done:** 29
  - **Partly:** 1 (LL-09: Local relief is computed; RMS roughness remains a documented placeholder/extension)
  - **Not done:** 0
  - **Not applicable:** 0

- **SRS Section 31 Acceptance Criteria:**
  - **Done:** 9
  - **Partly:** 0
  - **Not done:** 0
  - **Not applicable:** 0

- **Combined Total (39 items):**
  - **Done:** 38
  - **Partly:** 1
  - **Not done:** 0
  - **Not applicable:** 0
