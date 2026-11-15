# Space Explorer Project Data Dictionary
Version: 1.0.0
Author: Team Astra Motion (NASA Space Apps)
Status: Approved Reference

## 1. Celestial Bodies
- **Mars (`mars`)**: Target planet for rover exploration missions. Coordinate frame: landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. The Mars body-fixed frame name is not stated in the label.
- **Moon (`moon`)**: Target satellite for Artemis lunar surface missions. Primary reference frame: MOON_ME_DE421 (Mean Earth/Polar Axis ephemeris).

## 2. Missions
- **Mars 2020 (`mars-2020`)**: NASA mission exploring Jezero Crater, Mars. Landed February 18, 2021. Primary rover: Perseverance (`perseverance`).
- **Mars Science Laboratory (`msl-curiosity`)**: NASA mission exploring Gale Crater, Mars. Landed August 6, 2012. Primary rover: Curiosity (`curiosity`).
- **Artemis Lunar Program (`artemis-lunar`)**: NASA human and robotic lunar exploration program focusing on South Pole candidate landing sites.

## 3. Explorers
- **Perseverance (`perseverance`)**: Active Mars rover on mission Mars 2020.
- **Curiosity (`curiosity`)**: Active Mars rover on MSL mission. Note: There is no published localization record in the database; missing data is not fabricated.

## 4. Coordinate Reference Systems & Frames
- **Mars Reference Frame**: landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. The Mars body-fixed frame name is not stated in the label.
- **SITE 1 Relative Frame**: Local rover frame relative to landing site (+X North, +Y East, +Z Down). Documented in PLACES SIS.
- **MOON_ME_DE421**: Lunar polar coordinate frame based on DE421 ephemeris. Not Earth EPSG:4326.

## 5. Position Methods & Status Labels
- **Localized (`localized`)**: Position determined by direct surface localization algorithms. Label: `Verified`.
- **Interpolated (`interpolated`)**: Position calculated between known telemetry points (e.g. PLACES `best_interp.csv`). Label: `Estimated`.
- **Derived (`derived`)**: Position calculated from secondary sensors or dead-reckoning. Label: `Estimated`.
- **Unknown (`unknown`)**: Placeholder or unconfirmed data. Label: `Unknown`.

## 6. Data Archives
- **NASA PDS Geosciences Node**: Host archive for Mars 2020 PLACES bundle (`urn:nasa:pds:mars2020_rover_places`).
- **PLACES Product (`best_interp.csv`)**: Release 16.0 rover localization table providing Sol, SCLK, and coordinates.
- **SCLK Table (`sclk_table.csv`)**: Release 16.0 ancillary correlation table mapping RMC to spacecraft clock seconds.
