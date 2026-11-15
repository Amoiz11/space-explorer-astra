# Scientific Accuracy and Anti-Hallucination Rules
Reference: Space Explorer SRS Section 7 & Backend A Implementation Plan
Status: Mandatory Architectural Rules

## Rule 1: Source Provenance Requirement
Every factual data point in Space Explorer (coordinates, sol, telemetry, dates) must trace back to an approved NASA PDS archive, SPICE kernel, or officially registered data product. Data products are identified by a unique `product_id` (e.g., `urn:nasa:pds:mars2020_rover_places:data_localizations:best_interp.csv`).

## Rule 2: Prohibition of Fabricated Data
Under no circumstances should the system invent, guess, or synthesize planetary telemetry or positions. If data is absent (such as missing Curiosity current localization), the system must explicitly declare `position_status: "unknown"` and return `coordinates: null`. Missing data must never be filled with approximations unless explicitly labeled as `Estimated`.

## Rule 3: Strict Status Labeling
- **Verified**: Assigned exclusively to data taken directly and unmanipulated from verified mission products.
- **Estimated**: Assigned to interpolated, smoothed, or reconstructed traverses (e.g. `best_interp.csv` rows).
- **Historical**: Assigned to historical mission telemetry logs without active telemetry state.
- **Unknown**: Assigned to any baseline placeholder or unconfirmed data.

## Rule 4: Placeholder Flag Preservation
Any record created as a synthetic development baseline must have `is_placeholder: true` and `label: "Unknown"`. The system must never label a placeholder as `Verified` or `Estimated`.

## Rule 5: Strict Coordinate Frame Separation
Planetary coordinate systems are body-fixed frames specific to each celestial body. Mars coordinates are planetocentric (east-positive) or SITE relative. Lunar coordinates are MOON_ME_DE421. They must never be labeled, transformed into, or treated as Earth WGS84 (`EPSG:4326`).

## Rule 6: Spacecraft Clock (SCLK) to UTC Conversion
Converting SCLK seconds to UTC calendar time requires mission-specific SPICE SCLK/SCET kernels (`.tsc`). An SCLK count cannot be converted to UTC by linear scaling or guessing. If the kernel is unavailable, `observed_at` must remain null, while preserving `sol` and `sclk` for scientific fidelity.
