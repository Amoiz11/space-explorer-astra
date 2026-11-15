export type Method = 'measured' | 'derived' | 'modelled' | 'unknown'

export type Body = { id: 'mars' | 'moon'; name: string; missionCount: number }
export type Dataset = { id: string; name: string; source: string; updated: string }

export type Site = {
  id: string
  name: string
  coordinates: { values: [number, number]; units: string; frame: string } | null
  analysis_radius_m: number | null
  notes?: string
  is_placeholder?: boolean
}

export type SunEarthSample = {
  t: string
  sun: { az: number; el: number }
  earth: { az: number; el: number }
  sun_status?: 'lit' | 'partial' | 'shadow'
  sun_fraction?: number
  earth_status?: 'clear' | 'blocked_by_terrain' | 'below_horizon'
  earth_effective_el?: number
}

export type SunEarth = {
  site_id: string
  start: string
  end: string
  step_minutes: number
  samples: SunEarthSample[]
  horizon_profile: { az: number; el: number; cut_by_coverage?: boolean }[] | null
  method: Method
  source_product_id: string
  curvature_drop_deg?: number
  cut_azimuth_count?: number
  cut_azimuths?: number[]
}

export type IlluminationWindow = { start: string; end: string; duration_h: number }
export type EarthWindow = IlluminationWindow & {
  earth_az: number
  earth_el: number
  obstruction: 'clear' | 'blocked' | 'unknown'
}

export type Windows = {
  site_id: string
  illumination: {
    windows: IlluminationWindow[]
    total_sunlit_h: number
    hours_fully_lit: number
    hours_any_part_lit: number
    hours_shadow: number
    illuminated_fraction: number
  }
  earth_visibility: {
    windows: EarthWindow[]
    total_visible_h: number
    blocked_by_terrain_hours: number
    below_horizon_hours: number
    relay_communication: string
    relay_communication_note: string
  }
  label: Method
  uncertainty: string | null
}

export type SiteResult = { siteId: string; sunEarth: SunEarth; windows: Windows }

export type Terrain = {
  site_id: string
  elevation: { min_m: number; max_m: number; mean_m: number }
  slope: { mean: number; max: number; units: 'deg' | 'percent'; histogram: { bin: string; pct: number }[] }
  relief_m: number
  profile: { distance_m: number; elevation_m: number }[]
  dem: { resolution: string; vertical_reference: string; coverage: string; no_data: boolean }
  label: Method
}

export type SolarInputs = {
  panel_area_m2: number
  efficiency: number
  tilt_deg: number
  panel_azimuth_deg?: number
  track_sun_azimuth?: boolean
  observer_height_m?: number
  start: string
  end: string
}

export type SolarEstimate = {
  energy: number
  energy_kwh?: number | null
  mean_power_w?: number | null
  peak_power_w?: number | null
  units: string
  assumptions: string[]
  shadow_periods: { start: string; end: string; duration_hours?: number }[]
  per_day_energy?: Array<{ date: string; energy_wh: number; energy_kwh: number; peak_power_w: number; mean_power_w: number }>
  illumination_opportunity?: {
    hours_any_part_lit: number
    hours_fully_lit: number
    hours_shadow: number
    fraction_of_period: number
    number_of_lit_windows: number
  } | null
  message?: string | null
  uncertainty: string
  label: Method
}

export type CompareCriterion = {
  metric: string
  threshold: number
  label: string
}

export type CompareCriterionResult = CompareCriterion & {
  value: number
  passed: boolean
}

export type CompareRow = {
  site_id: string
  site_name?: string
  date: string
  days: number
  mean_slope: number
  max_slope?: number
  mean_elevation_m: number
  relief_m?: number
  sunlit_h: number
  fully_lit_h: number
  shadow_h: number
  earth_visible_h: number
  earth_blocked_h: number
  hours_both_up: number
  energy_kwh: number | null
  solar_opportunity: number
  quality: 'good' | 'fair' | 'limited'
  criteria_results?: CompareCriterionResult[]
}

export type CompareResult = {
  id: number
  rows: CompareRow[]
  best_by: {
    best_for_sunlight?: string
    best_for_earth_visibility?: string
    lowest_slope?: string
    most_hours_both_up?: string
  }
  criteria: Record<string, string>
  criteria_list?: CompareCriterion[]
  settings: Record<string, unknown>
  disclaimers?: string[]
}

export type MissionStatus = 'active' | 'ended' | 'inactive' | 'unknown'
export type ExplorerType = 'rover' | 'lander' | 'orbiter' | 'probe'
export type Mission = {
  id: string
  body: 'mars' | 'moon'
  name: string
  explorer_id: string
  types: ExplorerType[]
  status: MissionStatus
  launch: string | null
  landing: string | null
  summary: string
  is_placeholder?: boolean
}
export type MissionProfileData = Mission & {
  status_history: { status: MissionStatus; from: string }[]
  last_communication: string | null
  last_location: string | null
  last_image: string | null
  instruments: string[]
  events: { date: string; title: string }[]
  sources: { name: string; url: string }[]
  health?: { condition: string; evidence: string; label: string; reported_at: string | null; is_placeholder: boolean } | null
  telemetry: { power_w: number | null; battery_pct: number | null } | null
}

export type PositionKind = 'measured' | 'derived' | 'interpolated' | 'unknown'
export type ExplorerPosition = {
  id: string
  date: string
  kind: PositionKind
  x: number | null
  y: number | null
  product_id: string
  label?: string
  sol?: number | null
  sclk?: string | null
  coordinate_frame?: string
  is_placeholder?: boolean
}
export type ExplorerImage = {
  id: string
  captured: string
  camera: string
  explorer: string
  product_id: string
  hue: number
  sol?: number | null
  image_url?: string
  label?: string
  source_label?: string
  is_placeholder?: boolean
}

export type CompareMetric = { id: string; label: string; unit: string; range: string; method: Method; values: Record<string, number | string> }

export type AssistantCitation = {
  source_name: string
  product_id: string
  label: string
  url?: string
}

export type AssistantAnswer = {
  answer: string
  citations: AssistantCitation[]
  evidence_found: boolean
  answer_mode: 'llm' | 'template' | string
  llm_fallback_reason: string | null
  disclaimers: string[]
  no_evidence?: boolean
}

export type MapLayer = {
  id: string
  name: string
  type: string
  description?: string
  url?: string
  label?: string
  source?: string
  is_placeholder?: boolean
  disclaimer?: string
}

export type ImportRow = { id: string; dataset: string; status: 'ok' | 'warning' | 'failed'; warnings: number; rejected: number; when: string }

export type SourceInfo = {
  name: string
  link: string
  product_id: string
  version: string
  observed: string
  retrieved: string
  frame: string
  units: string
  method: Method
  uncertainty: string
  notes: string
  confidence: 'Verified' | 'Historical' | 'Estimated' | 'Unknown'
  vertical_reference?: string
  sha256_checksum?: string
  pds_lid?: string
}
