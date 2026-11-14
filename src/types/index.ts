export type Method = 'measured' | 'derived' | 'modelled' | 'unknown'

export type Body = { id: 'mars' | 'moon'; name: string; missionCount: number }
export type Dataset = { id: string; name: string; source: string; updated: string }

export type Site = {
  id: string
  name: string
  coordinates: { values: [number, number]; units: string; frame: string }
  analysis_radius_m: number
  notes?: string
}

export type SunEarthSample = { t: string; sun: { az: number; el: number }; earth: { az: number; el: number } }

export type SunEarth = {
  site_id: string
  start: string
  end: string
  step_minutes: number
  samples: SunEarthSample[]
  horizon_profile: { az: number; el: number }[] | null
  method: Method
  source_product_id: string
}

export type IlluminationWindow = { start: string; end: string; duration_h: number }
export type EarthWindow = IlluminationWindow & {
  earth_az: number
  earth_el: number
  obstruction: 'clear' | 'blocked' | 'unknown'
}

export type Windows = {
  site_id: string
  illumination: { windows: IlluminationWindow[]; total_sunlit_h: number; illuminated_fraction: number }
  earth_visibility: { windows: EarthWindow[]; total_visible_h: number }
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

export type SolarInputs = { panel_area_m2: number; efficiency: number; tilt_deg: number; start: string; end: string }
export type SolarEstimate = {
  energy: number
  units: string
  assumptions: string[]
  shadow_periods: { start: string; end: string }[]
  uncertainty: string
  label: Method
}

export type CompareRow = {
  site_id: string
  date: string
  mean_slope: number
  mean_elevation_m: number
  sunlit_h: number
  earth_visible_h: number
  solar_opportunity: number
  quality: 'good' | 'fair' | 'limited'
}
export type CompareResult = { rows: CompareRow[]; criteria: Record<string, string>; settings: Record<string, string | number> }

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
}
export type MissionProfileData = Mission & {
  status_history: { status: MissionStatus; from: string }[]
  last_communication: string | null
  last_location: string | null
  last_image: string | null
  instruments: string[]
  events: { date: string; title: string }[]
  sources: { name: string; url: string }[]
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
}
export type ExplorerImage = { id: string; captured: string; camera: string; explorer: string; product_id: string; hue: number }

export type CompareMetric = { id: string; label: string; unit: string; range: string; method: Method; values: Record<string, number | string> }

export type AssistantAnswer = {
  answer: string
  statements: { text: string; kind: 'measured' | 'estimated' }[]
  citations: { label: string; product_id: string }[]
  no_evidence: boolean
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
}
