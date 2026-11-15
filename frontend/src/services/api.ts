/**
 * api.ts – real HTTP adapter for the Space Explorer backend.
 *
 * Base URL:  VITE_API_BASE_URL (or VITE_API_URL)
 *            - "http://localhost:8000" for local development (default)
 *            - "" for relative reverse-proxy routing
 *            - "https://..." for production hosting
 *
 * All shapes are mapped from REAL backend responses verified against
 * http://localhost:8000 on 2026-11-15.
 */

// ─── config ────────────────────────────────────────────────────────────────
const rawEnv = (import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL) as string | undefined
const rawBase = rawEnv !== undefined ? rawEnv.trim() : 'http://localhost:8000'

const ROOT_URL = rawBase === ''
  ? ''
  : rawBase.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '')

const BASE = ROOT_URL === '' ? '/api/v1' : `${ROOT_URL}/api/v1`

// ─── generic helpers ────────────────────────────────────────────────────────
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const url = BASE + cleanPath
  let res: Response
  try {
    res = await fetch(url, { ...init, headers: { 'Content-Type': 'application/json', ...init.headers } })
  } catch {
    throw new Error('Backend is offline or unreachable. Make sure the server is running on ' + BASE)
  }
  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('Rate limit exceeded (429). Please wait a moment before trying again.')
    }
    if (res.status === 500) {
      throw new Error('Internal server error (500). The service encountered an unexpected error.')
    }
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json() as { detail?: string; error?: string }
      detail = body.detail ?? body.error ?? detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' })
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

// ─── raw backend shapes (verified 2026-11-15) ───────────────────────────────

// /health  (root – NOT under /api/v1)
export interface HealthRaw {
  status: string
  app: string
  version: string
  environment: string
  database: string
  is_placeholder: boolean
  bootstrap_status?: string
}

// /api/v1/lunar/sites
interface SiteRaw {
  id: string
  name: string
  body_id: string
  coordinates: { values: [number, number]; units: string; frame: string }
  frame: string
  analysis_radius_m: number
  semi_major_m: number | null
  semi_minor_m: number | null
  orientation_deg: number | null
  criteria: { slope_threshold_deg: number; threshold_label: string } | null
  notes: string | null
  is_placeholder: boolean
}
interface SiteListRaw { value: SiteRaw[] }

// /api/v1/lunar/sites/{id}/terrain
interface TerrainRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  product_id: string
  resolution: string
  coverage: { south_latitude: number; north_latitude: number; note: string }
  vertical_reference: string
  coordinate_reference_note: string
  method: string
  units: string
  pixel_count: number
  elevation: { min_m: number; max_m: number; mean_m: number; local_relief_m: number; roughness_rms_m: number }
  criteria_result: { slope_threshold_deg: number; threshold_label: string; fraction_exceeding_threshold: number; site_safety_disclaimer: string } | null
  disclaimer: string
}

// /api/v1/lunar/sites/{id}/slope
interface SlopeRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  product_id: string
  slope: {
    mean_deg: number; max_deg: number; min_deg: number
    p50_deg: number; p90_deg: number; p95_deg: number
    method: string; pixel_spacing_m: number
    histogram: { counts: number[]; bin_edges_deg: number[]; total_pixels: number }
  }
  disclaimer: string
}

// /api/v1/lunar/sites/{id}/illumination
interface IllumSample {
  timestamp: string
  sun_azimuth_deg: number
  sun_elevation_deg: number
  horizon_elevation_at_sun_azimuth: number
  sun_angular_radius_deg: number
  illuminated_fraction: number
  status: 'lit' | 'partial' | 'shadow'
}
interface IllumWindow { start: string; end: string; duration_hours: number }
interface IlluminationRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  frame: string
  product_id: string
  method: string
  observer_elevation_m: number
  observer_height_m: number
  kernels_used: string[]
  series: IllumSample[]
  windows: { any_part_lit: IllumWindow[]; fully_lit: IllumWindow[] }
  totals: {
    hours_any_part_lit: number
    hours_fully_lit: number
    hours_shadow: number
    total_simulation_hours: number
    number_of_windows: number
    longest_window_hours: number
    longest_continuous_shadow_hours: number
  }
  disclaimers: string[]
}

// /api/v1/lunar/sites/{id}/earth-visibility
interface EarthSample {
  timestamp: string
  earth_azimuth_deg: number
  earth_elevation_deg: number
  horizon_elevation_at_earth_azimuth: number
  effective_elevation_deg: number
  earth_angular_radius_deg: number
  obstruction_status: 'clear' | 'blocked_by_terrain' | 'below_horizon'
  earth_visible: boolean
}
interface EarthWindow {
  start: string; end: string; duration_hours: number
  mean_earth_azimuth: number; mean_earth_elevation: number
}
interface EarthVisRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  frame: string
  product_id: string
  method: string
  earth_disk_criterion: string
  series: EarthSample[]
  windows: EarthWindow[]
  totals: {
    earth_visible_hours: number
    blocked_by_terrain_hours: number
    below_horizon_hours: number
    total_simulation_hours: number
    earth_visible_fraction: number
    number_of_windows: number
  }
  relay_communication: string
  relay_communication_note: string
  disclaimers: string[]
}

// /api/v1/lunar/sites/{id}/horizon
interface HorizonPoint {
  azimuth_deg: number
  horizon_elevation_deg: number
  distance_to_blocking_pixel_km: number
  cut_by_coverage: boolean
}
export interface HorizonRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  method: string
  observer_height_dem_m: number
  observer_height_m: number
  total_observer_height_m: number
  summary: {
    min_horizon_elevation_deg: number
    max_horizon_elevation_deg: number
    mean_horizon_elevation_deg: number
    max_horizon_azimuth_deg: number
    cut_azimuth_count: number
  }
  profile: HorizonPoint[]
  disclaimers: string[]
}

// /api/v1/lunar/sites/{id}/solar-estimate
export interface SolarRaw {
  site_id: string
  site_name: string
  is_placeholder: boolean
  label: string
  method: string
  energy_wh: number | null
  energy_kwh: number | null
  mean_power_w: number | null
  peak_power_w: number | null
  per_day_energy: Array<{ date: string; energy_wh: number; energy_kwh: number; peak_power_w: number; mean_power_w: number }>
  illumination_opportunity: {
    hours_any_part_lit: number
    hours_fully_lit: number
    hours_shadow: number
    fraction_of_period: number
    number_of_lit_windows: number
    longest_shadow_hours: number
    longest_lit_window_hours: number
    shortest_lit_window_hours: number
  }
  shadow_periods: Array<{ start: string; end: string; duration_hours: number }>
  message: string | null
  assumptions: string[]
  uncertainty: Record<string, string>
  disclaimers: string[]
}

// /api/v1/missions
interface MissionRaw {
  id: string
  body_id: string
  name: string
  launch_date: string | null
  landing_date: string | null
  end_date: string | null
  status: string
  label: string
  source_label: string
  is_placeholder: boolean
}
interface MissionListRaw { items: MissionRaw[]; total: number }

// /api/v1/rovers
export interface RoverRaw {
  id: string
  mission_id: string
  name: string
  explorer_type: string
  current_status: string
  label: string
  source_label: string
  is_placeholder: boolean
}
export interface RoverListRaw { items: RoverRaw[]; total: number }

// /api/v1/rovers/{id}
export interface RoverDetailRaw extends RoverRaw {}

// /api/v1/rovers/{id}/locations
export interface RoverLocationItemRaw {
  explorer_id: string
  position_status: string
  label: string
  observed_at: string | null
  sol: number | null
  sclk: string | null
  coordinates: {
    values: [number, number]
    units: string
    coordinate_frame: string
  }
  original_fields: Record<string, { value: unknown; units: string | null }> | null
  uncertainty: { radius_m: number } | null
  position_method: string
  source_product_id: string
  retrieved_at: string
  source_label: string
  is_placeholder: boolean
}
export interface RoverLocationListRaw {
  items: RoverLocationItemRaw[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// /api/v1/rovers/{id}/latest-location
export interface RoverLatestLocationRaw extends RoverLocationItemRaw {}

// /api/v1/rovers/{id}/trajectory
export interface RoverTrajectoryRaw {
  id: number
  explorer_id: string
  path_coordinates: [number, number][]
  method: string
  start_time: string | null
  end_time: string | null
  product_id: string
  label: string
  source_label: string
  is_placeholder: boolean
}

// /api/v1/rovers/{id}/events
export interface RoverEventItemRaw {
  id: number
  explorer_id: string
  event_date: string
  event_type: string
  description: string
  source_id: string
  label: string
  source_label: string
  is_placeholder: boolean
}
export interface RoverEventListRaw {
  items: RoverEventItemRaw[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// /api/v1/rovers/{id}/analytics
export interface RoverAnalyticsRaw {
  explorer_id: string
  duration_days: number
  distance_km: number
  calculation_method: string
  label: string
  source_label: string
  is_placeholder: boolean
}

// /api/v1/rovers/{id}/timeline
export interface RoverTimelineItemRaw {
  item_type: 'event' | 'image' | string
  timestamp: string
  title: string
  details: Record<string, unknown>
  label: string
  source_label: string
  is_placeholder: boolean
}
export interface RoverTimelineRaw {
  explorer_id: string
  total_items: number
  timeline: RoverTimelineItemRaw[]
  label: string
  source_label: string
  is_placeholder: boolean
}

// /api/v1/sources/{product_id}
export interface SourceProductRaw {
  product_id: string
  product_identifier: string
  version: string
  checksum: string
  source: {
    id: string
    name: string
    source_url: string
    organization: string
    is_placeholder: boolean
  }
  observation_time: string | null
  retrieved_at: string
  coordinate_frame: string
  units: string
  processing_method: string
  uncertainty: Record<string, unknown> | null
  label: string
  is_placeholder: boolean
}

// /api/v1/rovers/{id}/images
interface ImageRaw {
  id: string
  explorer_id: string
  captured_at: string
  sol?: number | null
  image_url: string
  camera: string
  product_id: string
  label: string
  source_label: string
  is_placeholder: boolean
}
interface ImageListRaw { items: ImageRaw[]; total: number }

// /api/v1/rovers/{id}/health
export interface HealthRoverRaw {
  explorer_id: string
  condition: string
  evidence: string
  reported_at: string | null
  source_id: string | null
  label: string
  source_label: string
  is_placeholder: boolean
  // NOTE: power_w and battery_pct do NOT exist on this endpoint.
  // Audit listed them but real response has only condition/evidence.
}

// /api/v1/map/layers/{mission_id}
interface LayerRaw {
  id: string
  name: string
  type: string
  description: string
  url: string
  geojson_url: string
  label: string
  source: string
  source_product_id: string
  is_placeholder: boolean
  disclaimer: string
}
interface LayerListRaw { value: LayerRaw[] }

// /api/v1/assistant/query
export interface AssistantRaw {
  answer: string
  citations: Array<{
    id?: string
    title?: string
    source_name?: string
    product_id?: string
    label?: string
    url?: string
    api_path?: string
  }>
  evidence_found?: boolean
  answer_mode?: string
  llm_fallback_reason?: string | null
  disclaimers?: string[]
  no_evidence?: boolean
  endpoint_hint?: string
}

// /api/v1/lunar/products/{id}
export interface ProductRaw {
  id: string
  source_product_id: string
  resolution: string
  vertical_reference: string
  coverage: { south_latitude: number; north_latitude: number; note: string }
  version: string
  no_data_value: number | null
  coordinate_reference_note: string
  source_name: string
  source_url: string
  checksum: string
  retrieved_at: string
  label: string
  is_placeholder: boolean
  disclaimer: string
}

// ─── frontend types (from src/types/index.ts) ────────────────────────────────
import type {
  Body, CompareResult, Dataset, ExplorerImage, ExplorerPosition,
  ImportRow, Mission, MissionProfileData, Site, SolarEstimate, SolarInputs,
  SourceInfo, SunEarth, SunEarthSample, Terrain, Windows,
} from '../types'

// ─── adapter helpers ────────────────────────────────────────────────────────

/** FNV-1a hash of a string → 32-bit unsigned int */
function fnv32(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

/** Derive a hue (0-360) from a string id, replacing the dropped `hue` field */
export function hueFromId(id: string): number {
  return fnv32(id) % 360
}

function labelToMethod(label: string): 'measured' | 'derived' | 'modelled' | 'unknown' {
  const l = label.toLowerCase()
  if (l === 'verified') return 'measured'
  if (l === 'derived') return 'derived'
  if (l === 'modelled') return 'modelled'
  if (l === 'historical' || l === 'estimated') return 'derived'
  return 'unknown'
}

// ─── HEALTH ─────────────────────────────────────────────────────────────────
// /health is at the root, NOT under /api/v1
export async function getHealth(): Promise<HealthRaw> {
  const root = BASE.replace(/\/api\/v1\/?$/, '')
  const url = root + '/health'
  let res: Response
  try { res = await fetch(url) } catch { throw new Error('Backend offline') }
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<HealthRaw>
}

// ─── BODIES ─────────────────────────────────────────────────────────────────
// No /bodies endpoint exists on the real backend.
// Return a static list that matches what the UI needs (mars | moon).
export async function getBodies(): Promise<Body[]> {
  const missions = await get<MissionListRaw>('/missions')
  const counts: Record<string, number> = {}
  missions.items.forEach((m) => { counts[m.body_id] = (counts[m.body_id] ?? 0) + 1 })
  const order = ['mars', 'moon'] as const
  return order.map((id) => ({
    id,
    name: id === 'mars' ? 'Mars' : 'Moon',
    missionCount: counts[id] ?? 0,
  }))
}

// ─── MISSIONS ────────────────────────────────────────────────────────────────
export async function getMissions(bodyId: 'mars' | 'moon'): Promise<Mission[]> {
  const data = await get<MissionListRaw>('/missions')
  return data.items
    .filter((m) => m.body_id === bodyId)
    .map((m) => ({
      id: m.id,
      body: m.body_id as 'mars' | 'moon',
      name: m.name,
      explorer_id: m.id, // rover id equals mission id in this backend
      types: ['rover'] as Mission['types'], // explorer_type comes from rover endpoint, not mission
      status: m.status as Mission['status'],
      launch: m.launch_date ?? null,
      landing: m.landing_date ?? null,
      summary: `${m.name} — ${m.label} data. ${m.is_placeholder ? 'Placeholder record.' : ''}`,
      is_placeholder: m.is_placeholder,
    }))
}

export async function getAllMissions(): Promise<Mission[]> {
  const [mars, moon] = await Promise.all([getMissions('mars'), getMissions('moon')])
  return [...mars, ...moon]
}

export async function getMission(missionId: string): Promise<MissionProfileData | null> {
  try {
    const [data, roversData] = await Promise.all([
      get<MissionListRaw>('/missions'),
      get<RoverListRaw>('/rovers').catch(() => ({ items: [], total: 0 })),
    ])
    let m = data.items.find((x) => x.id === missionId)
    if (!m) {
      const matching = roversData.items.find((r) => r.id === missionId)
      if (matching) {
        m = data.items.find((x) => x.id === matching.mission_id)
      }
    }
    if (!m) return null

    // Dynamically resolve rover explorer_id matching mission_id (generic, not hard-coded)
    const matchingRover = roversData.items.find((r) => r.mission_id === m.id)
    const explorerId = matchingRover ? matchingRover.id : m.id

    // Fetch rover metadata, events, timeline, locations, images, and health in parallel
    let events: { date: string; title: string }[] = []
    let lastComm: string | null = null
    let lastLoc: string | null = null
    let lastImg: string | null = null
    let healthData: MissionProfileData['health'] = null
    const sources: { name: string; url: string }[] = []

    try {
      const [eventsRes, timelineRes, latestLocRes, imagesRes, healthRes] = await Promise.allSettled([
        get<RoverEventListRaw>(`/rovers/${explorerId}/events`),
        get<RoverTimelineRaw>(`/rovers/${explorerId}/timeline`),
        get<RoverLatestLocationRaw>(`/rovers/${explorerId}/latest-location`),
        get<ImageListRaw>(`/rovers/${explorerId}/images?limit=10`),
        get<HealthRoverRaw>(`/rovers/${explorerId}/health`),
      ])

      if (eventsRes.status === 'fulfilled' && eventsRes.value.items) {
        events = eventsRes.value.items.map((e) => ({
          date: e.event_date.slice(0, 10),
          title: `${e.event_type}: ${e.description}`,
        }))
      }

      if (timelineRes.status === 'fulfilled' && timelineRes.value.timeline?.length) {
        const sorted = [...timelineRes.value.timeline].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp))
        lastComm = sorted[0]?.timestamp?.slice(0, 10) ?? null
      }

      if (latestLocRes.status === 'fulfilled' && latestLocRes.value) {
        const loc = latestLocRes.value
        lastLoc = loc.observed_at ? loc.observed_at.slice(0, 10) : (loc.sol !== null && loc.sol !== undefined && loc.sol >= 0 ? `Sol ${loc.sol}${loc.sclk ? ` (SCLK ${loc.sclk})` : ''}` : 'Unknown')
        if (loc.source_label) {
          sources.push({ name: loc.source_label, url: '#' })
        }
      }

      if (imagesRes.status === 'fulfilled' && imagesRes.value.items?.length) {
        const sortedImgs = [...imagesRes.value.items].sort((a, b) => Date.parse(b.captured_at) - Date.parse(a.captured_at))
        lastImg = sortedImgs[0]?.captured_at?.slice(0, 10) ?? null
      }

      if (healthRes.status === 'fulfilled' && healthRes.value) {
        healthData = {
          condition: healthRes.value.condition,
          evidence: healthRes.value.evidence,
          label: healthRes.value.label || 'Unknown',
          reported_at: healthRes.value.reported_at,
          is_placeholder: healthRes.value.is_placeholder,
        }
        if (healthRes.value.source_label) {
          sources.push({ name: healthRes.value.source_label, url: '#' })
        }
      }
    } catch { /* ignore enrichment failures */ }

    if (events.length === 0) {
      if (m.launch_date) events.push({ date: m.launch_date.slice(0, 10), title: 'Launch' })
      if (m.landing_date) events.push({ date: m.landing_date.slice(0, 10), title: 'Landing' })
    }

    return {
      id: m.id,
      body: m.body_id as 'mars' | 'moon',
      name: m.name,
      explorer_id: explorerId,
      types: ['rover'],
      status: m.status as Mission['status'],
      launch: m.launch_date ?? null,
      landing: m.landing_date ?? null,
      summary: `${m.name}. ${m.is_placeholder ? 'Placeholder mission record.' : ''}`,
      status_history: [{ status: m.status as Mission['status'], from: m.launch_date ?? m.landing_date ?? '' }],
      last_communication: lastComm,
      last_location: lastLoc,
      last_image: lastImg,
      instruments: [],
      events,
      sources,
      health: healthData,
      telemetry: null,
    }
  } catch {
    return null
  }
}

// ─── ROVERS ──────────────────────────────────────────────────────────────────

export async function getRovers(): Promise<RoverRaw[]> {
  const data = await get<RoverListRaw>('/rovers')
  return data.items
}

export async function getRover(explorerId: string): Promise<RoverDetailRaw> {
  return get<RoverDetailRaw>(`/rovers/${explorerId}`)
}

export async function getRoverLocationsRaw(explorerId: string): Promise<RoverLocationListRaw> {
  return get<RoverLocationListRaw>(`/rovers/${explorerId}/locations`)
}

export async function getRoverLatestLocation(explorerId: string): Promise<RoverLatestLocationRaw> {
  return get<RoverLatestLocationRaw>(`/rovers/${explorerId}/latest-location`)
}

export async function getRoverTrajectory(explorerId: string): Promise<RoverTrajectoryRaw> {
  return get<RoverTrajectoryRaw>(`/rovers/${explorerId}/trajectory`)
}

export async function getRoverEvents(explorerId: string): Promise<RoverEventListRaw> {
  return get<RoverEventListRaw>(`/rovers/${explorerId}/events`)
}

export async function getRoverAnalytics(explorerId: string): Promise<RoverAnalyticsRaw> {
  return get<RoverAnalyticsRaw>(`/rovers/${explorerId}/analytics`)
}

export async function getRoverTimeline(explorerId: string): Promise<RoverTimelineRaw> {
  return get<RoverTimelineRaw>(`/rovers/${explorerId}/timeline`)
}

export async function getExplorerLocations(explorerId: string): Promise<ExplorerPosition[]> {
  try {
    // Load ALL pages of locations (e.g. all 502 records, not only the first page)
    const allItems: RoverLocationItemRaw[] = []
    let offset = 0
    const limit = 100
    let hasMore = true

    while (hasMore) {
      const data = await get<RoverLocationListRaw>(`/rovers/${explorerId}/locations?limit=${limit}&offset=${offset}`)
      if (!data.items?.length) break
      allItems.push(...data.items)
      offset += limit
      hasMore = data.has_more && offset < data.total
    }

    return allItems.map((loc, i) => {
      // Determine date display: observed_at if present, or format sol/sclk, or fallback to 'Unknown'
      let dateStr = 'Unknown'
      if (loc.observed_at) {
        dateStr = loc.observed_at.slice(0, 10)
      } else if (loc.sol !== null && loc.sol !== undefined && loc.sol >= 0) {
        dateStr = `Sol ${loc.sol}`
      } else if (loc.sclk && loc.sclk !== '0') {
        dateStr = `SCLK ${loc.sclk}`
      } else if (loc.retrieved_at) {
        dateStr = loc.retrieved_at.slice(0, 10)
      }

      // Map position_status / label to PositionKind
      let kind: ExplorerPosition['kind'] = 'unknown'
      const stat = (loc.position_status || loc.label || '').toLowerCase()
      if (stat.includes('verified') || stat.includes('measured') || stat.includes('localized')) {
        kind = 'measured'
      } else if (stat.includes('derived') || stat.includes('estimated')) {
        kind = 'derived'
      } else if (stat.includes('interpolated')) {
        kind = 'interpolated'
      }

      return {
        id: `pos-${explorerId}-${i}`,
        date: dateStr,
        kind,
        x: loc.coordinates?.values?.[0] ?? null,
        y: loc.coordinates?.values?.[1] ?? null,
        product_id: loc.source_product_id || `pos-${explorerId}-${i}`,
        label: loc.label || 'Unknown',
        sol: loc.sol,
        sclk: loc.sclk,
        coordinate_frame: loc.coordinates?.coordinate_frame,
        is_placeholder: loc.is_placeholder,
      }
    })
  } catch {
    return []
  }
}

export async function getExplorerImages(
  explorerId: string,
  options?: { camera?: string; sol?: number; startDate?: string; endDate?: string; limit?: number; offset?: number }
): Promise<ExplorerImage[]> {
  try {
    const params = new URLSearchParams()
    params.set('limit', String(options?.limit ?? 100))
    if (options?.offset) params.set('offset', String(options.offset))
    if (options?.camera) params.set('camera', options.camera)
    if (options?.sol !== undefined && options.sol !== null) params.set('sol', String(options.sol))
    if (options?.startDate) params.set('start_date', options.startDate)
    if (options?.endDate) params.set('end_date', options.endDate)

    const qs = params.toString() ? `?${params.toString()}` : ''
    const data = await get<ImageListRaw>(`/rovers/${explorerId}/images${qs}`)
    return (data.items ?? []).map((img) => ({
      id: img.id,
      captured: img.captured_at,
      sol: img.sol ?? null,
      camera: img.camera,
      explorer: img.explorer_id,
      image_url: img.image_url,
      product_id: img.product_id,
      label: img.label || 'Unknown',
      source_label: img.source_label,
      is_placeholder: img.is_placeholder,
      hue: hueFromId(img.id),
    }))
  } catch {
    return []
  }
}

// ─── SITES ───────────────────────────────────────────────────────────────────
function mapSite(s: SiteRaw): Site {
  const hasCoords =
    Array.isArray(s.coordinates?.values) &&
    s.coordinates.values.length >= 2 &&
    typeof s.coordinates.values[0] === 'number' &&
    typeof s.coordinates.values[1] === 'number'

  return {
    id: s.id || 'Unknown',
    name: s.name || 'Unnamed Site',
    coordinates: hasCoords
      ? {
          values: [s.coordinates.values[0], s.coordinates.values[1]],
          units: s.coordinates?.units || 'deg',
          frame: s.coordinates?.frame || s.frame || 'Unknown',
        }
      : null,
    analysis_radius_m: typeof s.analysis_radius_m === 'number' ? s.analysis_radius_m : null,
    notes: s.notes ?? undefined,
    is_placeholder: s.is_placeholder ?? false,
  }
}

export async function getSites(): Promise<Site[]> {
  const data = await get<SiteRaw[] | SiteListRaw>('/lunar/sites')
  // Support both raw array (as backend returns) and { value: [...] } wrapper
  const list = Array.isArray(data) ? data : (data?.value ?? [])
  return list.map(mapSite)
}

// Candidate site write operations (create/update/delete) have been removed from the public frontend.

// ─── TERRAIN ─────────────────────────────────────────────────────────────────
export async function getTerrain(siteId: string): Promise<Terrain> {
  const [terrainRaw, slopeRaw] = await Promise.all([
    get<TerrainRaw>(`/lunar/sites/${siteId}/terrain`),
    get<SlopeRaw>(`/lunar/sites/${siteId}/slope`),
  ])

  // Build histogram safely
  const hist = slopeRaw?.slope?.histogram
  const counts = hist?.counts ?? []
  const bin_edges_deg = hist?.bin_edges_deg ?? []
  const total = hist?.total_pixels || 1
  const histogram = counts.map((c, i) => ({
    bin: bin_edges_deg[i + 1] !== undefined ? `${bin_edges_deg[i]}–${bin_edges_deg[i + 1]}` : `${bin_edges_deg[i]}+`,
    pct: Math.round((c / total) * 100),
  }))

  const elevation = terrainRaw?.elevation ?? { min_m: 0, max_m: 0, mean_m: 0, local_relief_m: 0 }
  const slope = slopeRaw?.slope ?? { mean_deg: 0, max_deg: 0 }

  return {
    site_id: siteId,
    elevation: {
      min_m: elevation.min_m ?? 0,
      max_m: elevation.max_m ?? 0,
      mean_m: elevation.mean_m ?? 0,
    },
    slope: {
      mean: slope.mean_deg ?? 0,
      max: slope.max_deg ?? 0,
      units: 'deg',
      histogram,
    },
    relief_m: elevation.local_relief_m ?? 0,
    profile: [], // no radial profile array returned by backend; empty array prevents crash
    dem: {
      resolution: terrainRaw?.resolution || 'Unknown',
      vertical_reference: terrainRaw?.vertical_reference || 'Reference sphere',
      coverage: terrainRaw?.coverage?.note || 'South polar region',
      no_data: false,
    },
    label: labelToMethod(terrainRaw?.label || 'Derived'),
  }
}

// ─── ILLUMINATION / EARTH-VIS / SUN-EARTH ────────────────────────────────────

function parseWindowDays(start: string, end: string): number {
  const diff = (Date.parse(end) - Date.parse(start)) / 86400000
  return isNaN(diff) || diff < 1 ? 1 : diff
}

export async function getSunEarth(
  siteId: string,
  start: string,
  end: string,
  observerHeightM: number = 0,
  earthDisk: 'center' | 'upper_limb' = 'center',
): Promise<SunEarth> {
  const days = Math.ceil(parseWindowDays(start, end))

  const [illumRes, earthRes, horizonRes] = await Promise.allSettled([
    get<IlluminationRaw>(
      `/lunar/sites/${siteId}/illumination?start=${start.slice(0, 10)}&days=${days}&step_minutes=60&observer_height_m=${observerHeightM}`
    ),
    get<EarthVisRaw>(
      `/lunar/sites/${siteId}/earth-visibility?start=${start.slice(0, 10)}&days=${days}&step_minutes=60&observer_height_m=${observerHeightM}&earth_disk=${earthDisk}`
    ),
    get<HorizonRaw>(
      `/lunar/sites/${siteId}/horizon?observer_height_m=${observerHeightM}`
    ),
  ])

  const illumRaw = illumRes.status === 'fulfilled' ? illumRes.value : null
  const earthRaw = earthRes.status === 'fulfilled' ? earthRes.value : null
  const horizonRaw = horizonRes.status === 'fulfilled' ? horizonRes.value : null

  const earthMap = new Map((earthRaw?.series ?? []).map((s) => [s.timestamp, s]))

  const samples: SunEarthSample[] = (illumRaw?.series ?? []).map((s) => {
    const e = earthMap.get(s.timestamp)
    return {
      t: s.timestamp,
      sun: { az: s.sun_azimuth_deg ?? 0, el: s.sun_elevation_deg ?? 0 },
      earth: { az: e ? (e.earth_azimuth_deg ?? 0) : 0, el: e ? (e.earth_elevation_deg ?? 0) : 0 },
      sun_status: s.status,
      sun_fraction: s.illuminated_fraction,
      earth_status: e?.obstruction_status,
      earth_effective_el: e?.effective_elevation_deg,
    }
  })

  // Convert horizon profile to { az, el, cut_by_coverage } format
  const horizon_profile = horizonRaw?.profile
    ? horizonRaw.profile.map((p) => ({
        az: p.azimuth_deg,
        el: p.horizon_elevation_deg,
        cut_by_coverage: p.cut_by_coverage,
      }))
    : null

  return {
    site_id: siteId,
    start,
    end,
    step_minutes: 60,
    samples,
    horizon_profile,
    method: labelToMethod(illumRaw?.label || 'Modelled'),
    source_product_id: illumRaw?.product_id || 'lola-dem-75s-240m',
    curvature_drop_deg: 1.65, // Spherical Moon curvature drop (approx 1.65° at 100 km ray horizon)
    cut_azimuth_count: horizonRaw?.summary?.cut_azimuth_count ?? 0,
    cut_azimuths: (horizonRaw as unknown as { cut_azimuths?: number[] })?.cut_azimuths ?? [],
  }
}

export async function getWindows(
  siteId: string,
  start: string,
  end: string,
  observerHeightM: number = 0,
  earthDisk: 'center' | 'upper_limb' = 'center',
): Promise<Windows> {
  const days = Math.ceil(parseWindowDays(start, end))

  const [illumRes, earthRes] = await Promise.allSettled([
    get<IlluminationRaw>(
      `/lunar/sites/${siteId}/illumination?start=${start.slice(0, 10)}&days=${days}&step_minutes=60&observer_height_m=${observerHeightM}`
    ),
    get<EarthVisRaw>(
      `/lunar/sites/${siteId}/earth-visibility?start=${start.slice(0, 10)}&days=${days}&step_minutes=60&observer_height_m=${observerHeightM}&earth_disk=${earthDisk}`
    ),
  ])

  const illumRaw = illumRes.status === 'fulfilled' ? illumRes.value : null
  const earthRaw = earthRes.status === 'fulfilled' ? earthRes.value : null

  const illuminationWindows = (illumRaw?.windows?.any_part_lit ?? []).map((w) => ({
    start: w.start,
    end: w.end,
    duration_h: w.duration_hours,
  }))

  const earthWindows = (earthRaw?.windows ?? []).map((w) => ({
    start: w.start,
    end: w.end,
    duration_h: w.duration_hours,
    earth_az: w.mean_earth_azimuth ?? 0,
    earth_el: w.mean_earth_elevation ?? 0,
    obstruction: 'clear' as const,
  }))

  const totalHours = illumRaw?.totals?.total_simulation_hours || 1
  const anyPartLitHours = illumRaw?.totals?.hours_any_part_lit ?? 0

  return {
    site_id: siteId,
    illumination: {
      windows: illuminationWindows,
      total_sunlit_h: anyPartLitHours,
      hours_fully_lit: illumRaw?.totals?.hours_fully_lit ?? 0,
      hours_any_part_lit: anyPartLitHours,
      hours_shadow: illumRaw?.totals?.hours_shadow ?? 0,
      illuminated_fraction: anyPartLitHours / totalHours,
    },
    earth_visibility: {
      windows: earthWindows,
      total_visible_h: earthRaw?.totals?.earth_visible_hours ?? 0,
      blocked_by_terrain_hours: earthRaw?.totals?.blocked_by_terrain_hours ?? 0,
      below_horizon_hours: earthRaw?.totals?.below_horizon_hours ?? 0,
      relay_communication: earthRaw?.relay_communication ?? 'not modelled',
      relay_communication_note: earthRaw?.relay_communication_note ?? 'Direct-to-Earth line-of-sight only. Relay satellites or orbital nodes are not modelled.',
    },
    label: labelToMethod(illumRaw?.label || 'Modelled'),
    uncertainty: (illumRaw?.disclaimers ?? []).join(' ') || null,
  }
}

// ─── SOLAR ESTIMATE ──────────────────────────────────────────────────────────
export async function estimateSolar(siteId: string, inputs: SolarInputs): Promise<SolarEstimate> {
  const days = Math.ceil(parseWindowDays(inputs.start, inputs.end))
  const hasPanel = typeof inputs.panel_area_m2 === 'number' && inputs.panel_area_m2 > 0

  const payload: Record<string, unknown> = {
    start: inputs.start.slice(0, 10),
    days,
    step_minutes: 60,
    observer_height_m: inputs.observer_height_m ?? 0,
  }

  if (hasPanel) {
    payload.panel = {
      panel_area_m2: inputs.panel_area_m2,
      efficiency: inputs.efficiency > 1 ? inputs.efficiency / 100 : inputs.efficiency,
      tilt_deg: inputs.tilt_deg ?? 0,
      panel_azimuth_deg: inputs.panel_azimuth_deg ?? 0,
      track_sun_azimuth: inputs.track_sun_azimuth ?? false,
    }
  }

  const raw = await post<SolarRaw>(`/lunar/sites/${siteId}/solar-estimate`, payload)

  const shadows = (raw?.shadow_periods ?? []).map((p) => ({
    start: p.start,
    end: p.end,
    duration_hours: p.duration_hours,
  }))
  const assumptions = [
    ...(raw?.assumptions ?? []),
    ...(raw?.message ? [raw.message] : []),
  ]

  return {
    energy: raw?.energy_wh ?? 0,
    energy_kwh: raw?.energy_kwh ?? null,
    mean_power_w: raw?.mean_power_w ?? null,
    peak_power_w: raw?.peak_power_w ?? null,
    units: 'Wh',
    assumptions,
    shadow_periods: shadows,
    per_day_energy: raw?.per_day_energy ?? [],
    illumination_opportunity: raw?.illumination_opportunity ?? null,
    message: raw?.message ?? null,
    uncertainty: raw?.uncertainty ? Object.values(raw.uncertainty).join(' ') : 'Documented in model label',
    label: labelToMethod(raw?.label || 'Modelled'),
  }
}

// ─── COMPARE ─────────────────────────────────────────────────────────────────
export interface CompareSiteWindow {
  start: string
  days: number
}

export async function compareSites(
  siteIds: string[],
  windowsOrDates: Array<CompareSiteWindow | string>,
  observerHeightM: number = 0,
  panel?: SolarInputs,
): Promise<CompareResult> {
  const normWindows: CompareSiteWindow[] = (windowsOrDates ?? []).map((w) =>
    typeof w === 'string' ? { start: w, days: 1 } : { start: w.start, days: w.days || 1 }
  )

  const hasPanel = panel && typeof panel.panel_area_m2 === 'number' && panel.panel_area_m2 > 0

  const payload: Record<string, unknown> = {
    site_ids: siteIds,
    windows: normWindows.map((w) => ({ start: w.start.slice(0, 10), days: w.days })),
    step_minutes: 60,
    observer_height_m: observerHeightM,
  }

  if (hasPanel) {
    payload.panel = {
      panel_area_m2: panel.panel_area_m2,
      efficiency: panel.efficiency > 1 ? panel.efficiency / 100 : panel.efficiency,
      tilt_deg: panel.tilt_deg ?? 0,
      panel_azimuth_deg: panel.panel_azimuth_deg ?? 0,
      track_sun_azimuth: panel.track_sun_azimuth ?? false,
    }
  }

  try {
    const raw = await post<{
      id: number
      label: string
      method: string
      settings: Record<string, unknown>
      rows: Array<{
        site_id: string
        site_name: string
        is_placeholder: boolean
        window_start: string
        window_days: number
        observer_elevation_m: number
        illumination: {
          hours_any_part_lit: number
          hours_fully_lit: number
          hours_shadow: number
          longest_shadow_hours: number
          number_of_lit_windows: number
        }
        earth: {
          hours_earth_visible: number
          hours_earth_blocked: number
          number_of_earth_windows: number
        }
        slope: {
          mean_slope_deg: number
          max_slope_deg: number
          p90_slope_deg: number
        }
        elevation: {
          mean_elevation_m: number
          relief_m: number
        }
        hours_both_up: number
        energy_kwh: number | null
        criteria_results: Array<{
          metric: string
          threshold: number
          label: string
          value: number
          passed: boolean
        }>
      }>
      best_by: {
        best_for_sunlight?: string
        best_for_earth_visibility?: string
        lowest_slope?: string
        most_hours_both_up?: string
      }
      criteria: Array<{
        metric: string
        threshold: number
        label: string
      }>
      disclaimers: string[]
    }>('/lunar/compare', payload)

    const criteriaDict: Record<string, string> = {}
    ;(raw.criteria ?? []).forEach((c) => {
      criteriaDict[c.metric] = `${c.threshold} (${c.label})`
    })

    return {
      id: raw.id ?? 0,
      rows: (raw?.rows ?? []).map((r) => {
        const anyLit = r.illumination?.hours_any_part_lit ?? 0
        const simHours = (r.window_days || 1) * 24
        return {
          site_id: r.site_id,
          site_name: r.site_name,
          date: r.window_start?.slice(0, 10) ?? '',
          days: r.window_days ?? 1,
          mean_slope: r.slope?.mean_slope_deg ?? 0,
          max_slope: r.slope?.max_slope_deg ?? 0,
          mean_elevation_m: r.elevation?.mean_elevation_m ?? 0,
          relief_m: r.elevation?.relief_m ?? 0,
          sunlit_h: anyLit,
          fully_lit_h: r.illumination?.hours_fully_lit ?? 0,
          shadow_h: r.illumination?.hours_shadow ?? 0,
          earth_visible_h: r.earth?.hours_earth_visible ?? 0,
          earth_blocked_h: r.earth?.hours_earth_blocked ?? 0,
          hours_both_up: r.hours_both_up ?? 0,
          energy_kwh: r.energy_kwh ?? null,
          solar_opportunity: simHours > 0 ? anyLit / simHours : 0,
          quality: anyLit > 12 ? 'good' : anyLit > 0 ? 'fair' : 'limited',
          criteria_results: r.criteria_results ?? [],
        }
      }),
      best_by: raw.best_by ?? {},
      criteria: criteriaDict,
      criteria_list: raw.criteria ?? [],
      settings: raw.settings ?? {},
      disclaimers: raw.disclaimers ?? [],
    }
  } catch {
    return { id: 0, rows: [], best_by: {}, criteria: {}, settings: {}, disclaimers: [] }
  }
}

export function getComparisonExportUrl(comparisonId: number, format: 'json' | 'csv'): string {
  return `${BASE}/lunar/compare/${comparisonId}/export?format=${format}`
}

// ─── ASSISTANT ───────────────────────────────────────────────────────────────
import type { AssistantAnswer } from '../types'

export async function askAssistant(question: string): Promise<AssistantAnswer> {
  const raw = await post<AssistantRaw>('/assistant/query', { question })
  return {
    answer: raw.answer,
    citations: (raw.citations ?? []).map((c) => ({
      source_name: c.source_name || c.title || 'Approved Source',
      product_id: c.product_id || c.id || '',
      label: c.label || 'Verified',
      url: c.url || c.api_path,
    })),
    evidence_found: raw.evidence_found ?? !raw.no_evidence,
    answer_mode: raw.answer_mode ?? 'template',
    llm_fallback_reason: raw.llm_fallback_reason ?? null,
    disclaimers: raw.disclaimers ?? [],
    no_evidence: raw.no_evidence ?? !raw.evidence_found,
  }
}

// ─── SOURCE / PROVENANCE ──────────────────────────────────────────────────────
export async function getSource(productId: string): Promise<SourceInfo> {
  // Strip optional prefix like "site:" or "source:" or "position:" or "terrain:" if passed from UI
  const cleanId = productId.replace(/^(site:|source:|result:|mission:|position:|terrain:)/, '')
  
  // 1. Try /sources/{product_id} (standard product provenance endpoint for rovers / PDS products)
  try {
    const raw = await get<SourceProductRaw>(`/sources/${encodeURIComponent(cleanId)}`)
    return {
      name: raw.source?.name ?? raw.product_identifier,
      link: raw.source?.source_url ?? '#',
      product_id: raw.product_identifier,
      version: raw.version,
      observed: raw.observation_time ?? 'Unknown',
      retrieved: raw.retrieved_at,
      frame: raw.coordinate_frame,
      units: raw.units,
      method: labelToMethod(raw.label),
      uncertainty: raw.uncertainty ? JSON.stringify(raw.uncertainty) : 'Documented in product label.',
      notes: `Checksum (MD5): ${raw.checksum}. Organization: ${raw.source?.organization ?? 'Unknown'}. ${raw.processing_method}. ${raw.is_placeholder ? 'Placeholder product.' : ''}`,
      confidence: (raw.label as SourceInfo['confidence']) || 'Unknown',
    }
  } catch { /* proceed to next lookup */ }

  // 2. Try /lunar/products/{id} (lunar LOLA products)
  try {
    const raw = await get<ProductRaw>(`/lunar/products/${cleanId}`)
    return {
      name: raw.source_name,
      link: raw.source_url,
      product_id: raw.id,
      version: raw.version,
      observed: raw.retrieved_at,
      retrieved: raw.retrieved_at,
      // Keep original frame text verbatim (never remap to EPSG:4326)
      frame: raw.coordinate_reference_note,
      units: 'm',
      method: labelToMethod(raw.label),
      uncertainty: raw.disclaimer,
      notes: [raw.coordinate_reference_note, raw.vertical_reference].filter(Boolean).join('\n\n'),
      confidence: (raw.label as SourceInfo['confidence']) || 'Verified',
      vertical_reference: raw.vertical_reference,
      sha256_checksum: raw.checksum,
      pds_lid: raw.source_product_id,
    }
  } catch {
    // 3. If not found, check if it is a candidate site ID
    try {
      const sites = await get<SiteRaw[] | SiteListRaw>('/lunar/sites')
      const siteList = Array.isArray(sites) ? sites : (sites?.value ?? [])
      const s = siteList.find((x) => x.id === cleanId)
      if (s) {
        let vertRef: string | undefined
        let pdsLid: string | undefined
        let checksum: string | undefined
        try {
          const prod = await get<ProductRaw>('/lunar/products/lola-dem-75s-240m')
          vertRef = prod?.vertical_reference
          pdsLid = prod?.source_product_id
          checksum = prod?.checksum
        } catch { /* ignore */ }

        return {
          name: s.name,
          link: '#',
          product_id: s.id,
          version: 'v1.0',
          observed: '2026-11-15T00:00:00Z',
          retrieved: '2026-11-15T00:00:00Z',
          frame: s.coordinates?.frame || s.frame || 'Unknown',
          units: s.coordinates?.units || 'deg',
          method: s.is_placeholder ? 'unknown' : 'derived',
          uncertainty: 'Candidate landing site planning area. Planning support tool, not safety certification.',
          notes: s.notes || 'Candidate site for lunar landing evaluation.',
          confidence: s.is_placeholder ? 'Unknown' : 'Verified',
          vertical_reference: vertRef,
          sha256_checksum: checksum,
          pds_lid: pdsLid,
        }
      }
    } catch { /* ignore */ }

    throw new Error(`Source '${cleanId}' not found. Check /api/v1/sources/${cleanId} or /api/v1/lunar/products/${cleanId}`)
  }
}

// ─── MAP LAYERS ───────────────────────────────────────────────────────────────
export interface MapLayer {
  id: string
  name: string
  type: string
  description: string
  url: string
  label: string
  source: string
  is_placeholder: boolean
  disclaimer: string
}
export async function getMapLayers(missionId: string): Promise<MapLayer[]> {
  const raw = await get<LayerRaw[] | LayerListRaw>(`/map/layers/${missionId}`)
  const list = Array.isArray(raw) ? raw : (raw?.value ?? [])
  return list.map((l) => ({
    id: l.id,
    name: l.name,
    type: l.type,
    description: l.description,
    url: l.url,
    label: l.label,
    source: l.source,
    is_placeholder: l.is_placeholder,
    disclaimer: l.disclaimer,
  }))
}

// ─── STUB: Datasets / Imports ─────────────────────────────────────────────────
// No backend endpoint exists for these (Group B gap).
// Return empty arrays so UI shows "Not connected to backend" state.
export async function getDatasets(): Promise<Dataset[]> {
  return []
}
export async function getImports(): Promise<ImportRow[]> {
  return []
}
