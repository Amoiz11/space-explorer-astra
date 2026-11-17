# Integration Notes

## Frontend Architecture (post UI-polish batch 2)

### Routes

| Path | Component | Notes |
|---|---|---|
| `/` | `HomePage` | Compact hero; stats; modules |
| `/lunar` | `LunarPage` | Site analyser; compact header |
| `/lunar/compare` | `LunarComparePage` | Multi-site comparison |
| `/missions` | `MissionsPage` | Body selector + mission list |
| `/missions/:id` | `MissionProfile` | Profile + map/gallery links |
| `/explorers/:id/map` | `MapPage` | SVG dot map |
| `/explorers/:id/gallery` | `GalleryPage` | Filtered image grid |
| `/assistant` | redirect | Opens AI drawer, stays on `/` |
| `/time-machine` | redirect → `/` | **Page removed** (backend untouched) |
| `*` | redirect → `/` | Catch-all |

> [!IMPORTANT]
> `/time-machine` now redirects to `/`. The backend endpoints that served the time machine (positions, mission events) are **not removed** — they remain and are still used by other pages (MissionProfile, Map).

### Background Scene

A single `<BackgroundScene />` is mounted in `Layout` with `position: fixed; inset: 0; z-index: 0; pointer-events: none`. It replaces per-page hero `<HeroScene>` / `<Planet3D>` blocks.

- Particle count: 25 (< 480 px), 45 (< 768 px), 80 (desktop)
- Device-pixel-ratio capped at 1.5
- Animation pauses when `document.hidden` is true
- `prefers-reduced-motion` → static stars, no rAF loop
- Route tint fades via CSS transition (700 ms)

### PageHeader vs PageHero

`PageHeader` is a compact heading block (title + subtitle + chip + actions) with no embedded 3D scene. All pages that previously used `PageHero` now use `PageHeader`. `PageHero` and `HeroScene` are kept in source but no longer used by any route.

### Navigation

Nav links: **Home, Lunar Navigator, Missions, Gallery** + "Ask AI" button (opens drawer).

### Smoke Test (`frontend/scripts/smoke.mjs`)

Covers:
1. Home (desktop)
2. Missions (desktop)
3. Mission Profile – mars-2020 (desktop)
4. Time Machine Redirect – asserts `/time-machine` → `/` (desktop)
5. Gallery – perseverance (desktop)
6. Map – perseverance (desktop)
7. Lunar Navigator – Shackleton + analyse (desktop)
8. Lunar Compare (desktop)
9. AI Assistant Drawer (desktop)
10. Home (mobile 390 × 844)
11. Lunar Navigator (mobile 390 × 844)

Screenshots saved to `frontend/qa-screenshots/`.

### Environment Variables (frontend)

Frontend reads `VITE_API_BASE` (defaults to `/api`) for the backend base URL. No other frontend env vars.
