import type {
  CompareResult, CompareRow, EarthWindow, IlluminationWindow, Site, SolarEstimate, SolarInputs,
  SunEarth, SunEarthSample, Terrain, Windows,
} from '../types'

const MIN = 60000
const STEP_MIN = 10
const DAY_MS = 86400000
const REF = Date.UTC(2026, 0, 1)

const FRAME = 'documented lunar frame'
export const sitesMock: Site[] = [
  { id: 'site-01', name: 'Site A', coordinates: { values: [-89.5, 120], units: 'deg', frame: FRAME }, analysis_radius_m: 1000, notes: 'Mock site' },
  { id: 'site-02', name: 'Site B', coordinates: { values: [-88.8, 15], units: 'deg', frame: FRAME }, analysis_radius_m: 1000, notes: 'Mock site' },
  { id: 'site-03', name: 'Site C', coordinates: { values: [-87.9, 310], units: 'deg', frame: FRAME }, analysis_radius_m: 800, notes: 'Mock site' },
  { id: 'site-04', name: 'Site D', coordinates: { values: [-89.1, 215.5], units: 'deg', frame: FRAME }, analysis_radius_m: 1200, notes: 'Mock site' },
  { id: 'site-05', name: 'Site E', coordinates: { values: [-86.5, 75], units: 'deg', frame: FRAME }, analysis_radius_m: 1000, notes: 'Mock site' },
]

function hash(s: string) {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  h ^= h >>> 13
  h = Math.imul(h, 0x5bd1e995)
  h ^= h >>> 15
  return h >>> 0
}
const norm360 = (a: number) => ((a % 360) + 360) % 360
const r2 = (n: number) => Math.round(n * 100) / 100

function horizonFor(siteId: string) {
  const ph = (hash(siteId) % 628) / 100
  const pts: { az: number; el: number }[] = []
  for (let az = 0; az < 360; az += 5) {
    const el = 0.55 + 0.4 * Math.sin((az * Math.PI) / 60 + ph) + 0.25 * Math.sin((az * Math.PI) / 23 + ph * 2)
    pts.push({ az, el: r2(Math.max(0, el)) })
  }
  return pts
}

function horizonAt(profile: { az: number; el: number }[], az: number) {
  if (!profile.length) return 0
  return profile[Math.floor(norm360(az) / 5) % profile.length].el
}

export function makeSunEarth(siteId: string, start: string, end: string): SunEarth {
  const h = hash(siteId)
  const seedAz = h % 360
  const ph1 = (Math.floor(h / 8) % 628) / 100
  const ph2 = (Math.floor(h / 32) % 628) / 100
  const earthBase = 0.9 + (Math.floor(h / 128) % 20) / 10
  const t0 = Date.parse(start)
  const t1 = Date.parse(end)
  const samples: SunEarthSample[] = []

  for (let t = t0; t < t1; t += STEP_MIN * MIN) {
    const days = (t - REF) / DAY_MS
    const hour = (t / 3600000) % 24
    const sunAz = norm360(seedAz + days * 12.19)
    const sunEl = 0.35 + 0.85 * Math.sin((2 * Math.PI * days) / 29.5 + ph1) + 1.1 * Math.sin((2 * Math.PI * hour) / 24 + ph2)
    const earthAz = norm360(40 + seedAz * 0.1 + 6 * Math.sin((2 * Math.PI * days) / 27.3 + ph2))
    const earthEl = earthBase + 0.6 * Math.sin((2 * Math.PI * days) / 27.3 + ph1) + 1.4 * Math.sin((2 * Math.PI * hour) / 24.8 + ph1)
    samples.push({
      t: new Date(t).toISOString(),
      sun: { az: r2(sunAz), el: r2(sunEl) },
      earth: { az: r2(earthAz), el: r2(earthEl) },
    })
  }

  return {
    site_id: siteId, start, end, step_minutes: STEP_MIN, samples,
    horizon_profile: horizonFor(siteId), method: 'modelled', source_product_id: 'mock-product',
  }
}

function runs(flags: boolean[]) {
  const out: [number, number][] = []
  let s = -1
  flags.forEach((f, i) => {
    if (f && s < 0) s = i
    if (!f && s >= 0) { out.push([s, i]); s = -1 }
  })
  if (s >= 0) out.push([s, flags.length])
  return out
}
const total = (w: { duration_h: number }[]) => r2(w.reduce((sum, x) => sum + x.duration_h, 0))

export function makeWindows(siteId: string, start: string, end: string): Windows {
  const se = makeSunEarth(siteId, start, end)
  const prof = se.horizon_profile ?? []
  const t0 = Date.parse(start)
  const iso = (i: number) => new Date(t0 + i * STEP_MIN * MIN).toISOString()
  const sunFlags = se.samples.map((s) => s.sun.el > horizonAt(prof, s.sun.az))
  const earthFlags = se.samples.map((s) => s.earth.el > horizonAt(prof, s.earth.az))

  const illum: IlluminationWindow[] = runs(sunFlags).map(([a, b]) => ({
    start: iso(a), end: iso(b), duration_h: r2(((b - a) * STEP_MIN) / 60),
  }))
  const earthW: EarthWindow[] = runs(earthFlags).map(([a, b]) => {
    const mid = se.samples[Math.floor((a + b - 1) / 2)]
    return {
      start: iso(a), end: iso(b), duration_h: r2(((b - a) * STEP_MIN) / 60),
      earth_az: mid.earth.az, earth_el: mid.earth.el, obstruction: 'clear',
    }
  })
  const hours = (se.samples.length * STEP_MIN) / 60
  const sunlit = total(illum)
  return {
    site_id: siteId,
    illumination: { windows: illum, total_sunlit_h: sunlit, illuminated_fraction: hours ? r2(sunlit / hours) : 0 },
    earth_visibility: { windows: earthW, total_visible_h: total(earthW) },
    label: 'modelled',
    uncertainty: 'Mock values. Not real scientific data.',
  }
}

export function makeTerrain(siteId: string): Terrain {
  const h = hash(siteId)
  const base = -1800 + (h % 900)
  const profile: { distance_m: number; elevation_m: number }[] = []
  for (let d = 0; d <= 1000; d += 25) {
    profile.push({
      distance_m: d,
      elevation_m: Math.round(base + 40 * Math.sin(d / 130 + h) + 22 * Math.sin(d / 47) + d * 0.05),
    })
  }
  const els = profile.map((p) => p.elevation_m)
  const bins = ['0-2', '2-5', '5-10', '10-15', '15-20', '20+']
  const raw = bins.map((_, i) => 40 / (i + 1) + ((h >> i) % 7))
  const sum = raw.reduce((a, b) => a + b, 0)
  return {
    site_id: siteId,
    elevation: { min_m: Math.min(...els), max_m: Math.max(...els), mean_m: Math.round(els.reduce((a, b) => a + b, 0) / els.length) },
    slope: {
      mean: r2(3 + (h % 40) / 10), max: r2(12 + (h % 90) / 10), units: 'deg',
      histogram: bins.map((bin, i) => ({ bin, pct: Math.round((raw[i] / sum) * 100) })),
    },
    relief_m: Math.max(...els) - Math.min(...els),
    profile,
    dem: {
      resolution: 'Mock, about 20 m per pixel',
      vertical_reference: 'Mock lunar reference sphere',
      coverage: 'Mock, full analysis radius',
      no_data: false,
    },
    label: 'derived',
  }
}

export function makeSolar(siteId: string, inputs: SolarInputs): SolarEstimate {
  const w = makeWindows(siteId, inputs.start, inputs.end)
  const sunlit = w.illumination.total_sunlit_h
  const tiltBoost = 1 + Math.min(inputs.tilt_deg, 60) / 200
  const energy = Math.round(inputs.panel_area_m2 * inputs.efficiency * 1361 * sunlit * 0.1 * tiltBoost)
  const shadows: { start: string; end: string }[] = []
  const ill = w.illumination.windows
  let cursor = Date.parse(inputs.start)
  ill.forEach((x) => {
    if (Date.parse(x.start) > cursor) shadows.push({ start: new Date(cursor).toISOString(), end: x.start })
    cursor = Date.parse(x.end)
  })
  if (cursor < Date.parse(inputs.end)) shadows.push({ start: new Date(cursor).toISOString(), end: inputs.end })
  return {
    energy, units: 'Wh',
    assumptions: [
      `Panel area ${inputs.panel_area_m2} m², efficiency ${(inputs.efficiency * 100).toFixed(0)} %`,
      `Panel tilt ${inputs.tilt_deg}°`,
      'Mock solar constant and a fixed low-elevation factor',
      'No dust, no panel degradation, no temperature effects',
    ],
    shadow_periods: shadows,
    uncertainty: 'Mock estimate. Real uncertainty comes from the backend.',
    label: 'modelled',
  }
}

export function makeCompare(siteIds: string[], dates: string[]): CompareResult {
  const rows: CompareRow[] = []
  siteIds.forEach((id) => {
    dates.forEach((d) => {
      const start = `${d}T00:00:00Z`
      const end = new Date(Date.parse(start) + DAY_MS).toISOString()
      const w = makeWindows(id, start, end)
      const t = makeTerrain(id)
      const q = w.illumination.total_sunlit_h > 12 ? 'good' : w.illumination.total_sunlit_h > 6 ? 'fair' : 'limited'
      rows.push({
        site_id: id, date: d, mean_slope: t.slope.mean, mean_elevation_m: t.elevation.mean_m,
        sunlit_h: w.illumination.total_sunlit_h, earth_visible_h: w.earth_visibility.total_visible_h,
        solar_opportunity: w.illumination.illuminated_fraction, quality: q,
      })
    })
  })
  return {
    rows,
    criteria: { sunlight: 'Hours with the Sun above the terrain horizon', earth_visibility: 'Hours with Earth above the terrain horizon' },
    settings: { step_minutes: STEP_MIN, horizon_source: 'mock profile', frame: FRAME },
  }
}
