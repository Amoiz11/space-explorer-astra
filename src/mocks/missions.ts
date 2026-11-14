import type {
  AssistantAnswer, CompareMetric, ExplorerImage, ExplorerPosition, Mission, MissionProfileData, SourceInfo,
} from '../types'

export const missionsMock: Mission[] = [
  { id: 'perseverance', body: 'mars', name: 'Perseverance', explorer_id: 'perseverance', types: ['rover'], status: 'active', launch: '2020-07-30', landing: '2021-02-18', summary: 'Rover exploring Jezero crater.' },
  { id: 'curiosity', body: 'mars', name: 'Curiosity', explorer_id: 'curiosity', types: ['rover'], status: 'active', launch: '2011-11-26', landing: '2012-08-06', summary: 'Rover climbing Mount Sharp.' },
  { id: 'insight', body: 'mars', name: 'InSight', explorer_id: 'insight', types: ['lander'], status: 'ended', launch: '2018-05-05', landing: '2018-11-26', summary: 'Lander that studied the interior of Mars.' },
  { id: 'mro', body: 'mars', name: 'Mars Reconnaissance Orbiter', explorer_id: 'mro', types: ['orbiter'], status: 'active', launch: '2005-08-12', landing: null, summary: 'Orbiter imaging the surface of Mars.' },
  { id: 'lro', body: 'moon', name: 'Lunar Reconnaissance Orbiter', explorer_id: 'lro', types: ['orbiter'], status: 'active', launch: '2009-06-18', landing: null, summary: 'Orbiter mapping the Moon, including the poles.' },
  { id: 'chandrayaan-3', body: 'moon', name: 'Chandrayaan-3', explorer_id: 'chandrayaan-3', types: ['lander', 'rover'], status: 'inactive', launch: '2023-07-14', landing: '2023-08-23', summary: 'Lander and rover near the lunar south pole.' },
]

const INSTR: Record<string, string[]> = {
  perseverance: ['Mastcam-Z', 'SuperCam', 'PIXL', 'SHERLOC'],
  curiosity: ['Mastcam', 'ChemCam', 'SAM', 'CheMin'],
  insight: ['SEIS', 'HP3', 'RISE'],
  mro: ['HiRISE', 'CRISM', 'SHARAD'],
  lro: ['LROC', 'LOLA', 'Diviner'],
  'chandrayaan-3': ['ChaSTE', 'ILSA', 'RAMBHA-LP'],
}

export function profileFor(id: string): MissionProfileData | null {
  const m = missionsMock.find((x) => x.id === id)
  if (!m) return null
  const ended = m.status === 'ended' || m.status === 'inactive'
  return {
    ...m,
    status_history: [
      { status: 'active', from: m.landing ?? m.launch ?? '2020-01-01' },
      ...(ended ? [{ status: m.status, from: '2023-09-22' as string }] : []),
    ],
    last_communication: ended ? '2023-09-22' : '2026-11-12',
    last_location: ended ? '2023-09-03' : '2026-11-08',
    last_image: ended ? '2023-09-04' : '2026-11-11',
    instruments: INSTR[id] ?? [],
    events: [
      { date: m.launch ?? '2020-01-01', title: 'Launch' },
      ...(m.landing ? [{ date: m.landing, title: m.body === 'moon' ? 'Landing' : 'Landing on the surface' }] : [{ date: m.launch ?? '2020-01-01', title: 'Orbit operations begin' }]),
      { date: new Date(Date.parse(m.landing ?? m.launch ?? '2020-01-01') + 30 * 86400000).toISOString().slice(0, 10), title: 'First science campaign' },
      { date: new Date(Date.parse(m.landing ?? m.launch ?? '2020-01-01') + 60 * 86400000).toISOString().slice(0, 10), title: 'Extended operations begin' },
    ],
    sources: [
      { name: 'NASA mission page', url: 'https://www.nasa.gov' },
      { name: 'NASA PDS archive', url: 'https://pds.nasa.gov' },
    ],
    telemetry: m.status === 'active' && m.id === 'perseverance' ? { power_w: 110, battery_pct: null } : null,
  }
}

export function positionsFor(explorerId: string): ExplorerPosition[] {
  const m = missionsMock.find((x) => x.explorer_id === explorerId)
  const start = Date.parse(m?.landing ?? m?.launch ?? '2023-01-01')
  const out: ExplorerPosition[] = []
  const kinds: ExplorerPosition['kind'][] = ['measured', 'measured', 'derived', 'interpolated', 'measured', 'unknown']
  for (let i = 0; i < 24; i++) {
    const kind = kinds[i % kinds.length]
    out.push({
      id: `pos-${i}`,
      date: new Date(start + i * 3 * 86400000).toISOString().slice(0, 10),
      kind,
      x: kind === 'unknown' ? null : 12 + i * 3 + Math.sin(i) * 6,
      y: kind === 'unknown' ? null : 55 + Math.cos(i / 2) * 22,
      product_id: `mock-pos-${i}`,
    })
  }
  return out
}

export function imagesFor(explorerId: string): ExplorerImage[] {
  const cams = ['Navigation camera', 'Mast camera', 'Hazard camera', 'Context camera']
  const m = missionsMock.find((x) => x.explorer_id === explorerId)
  const base = Date.parse(m?.landing ?? m?.launch ?? '2023-01-01')
  return Array.from({ length: 24 }, (_, i) => ({
    id: `img-${i}`,
    captured: new Date(base + i * 4 * 86400000 + 36000000).toISOString(),
    camera: cams[i % cams.length],
    explorer: explorerId,
    product_id: `mock-img-${String(i).padStart(3, '0')}`,
    hue: (i * 37) % 360,
  }))
}

export function compareMetrics(ids: string[]): CompareMetric[] {
  const sel = missionsMock.filter((m) => ids.includes(m.id))
  const dur = (m: Mission) => {
    const s = Date.parse(m.landing ?? m.launch ?? '2020-01-01')
    const e = m.status === 'active' ? Date.parse('2026-11-14') : Date.parse('2023-09-22')
    return Math.max(0, Math.round((e - s) / 86400000))
  }
  const num = (m: Mission, k: number) => 10 + ((m.id.length * k * 7) % 90)
  const mk = (id: string, label: string, unit: string, f: (m: Mission) => number | string, method: CompareMetric['method'], range: string): CompareMetric => ({
    id, label, unit, range, method, values: Object.fromEntries(sel.map((m) => [m.id, f(m)])),
  })
  return [
    mk('duration', 'Mission duration', 'days', dur, 'derived', 'Landing to latest status date'),
    mk('distance', 'Distance travelled', 'km', (m) => (m.types.includes('rover') ? num(m, 3) / 3 : 0), 'modelled', 'Landing to latest position'),
    mk('images', 'Image count', 'images', (m) => num(m, 11) * 1000, 'measured', 'Archive index'),
    mk('instruments', 'Instruments', 'count', (m) => (INSTR[m.id] ?? []).length, 'measured', 'Mission profile'),
    mk('events', 'Key events', 'count', () => 3, 'measured', 'Mission profile'),
  ]
}

export function answerFor(q: string): AssistantAnswer {
  const s = q.toLowerCase()
  if (s.includes('lunar') || s.includes('moon') || s.includes('sun') || s.includes('earth')) {
    return {
      answer: 'Near the lunar south pole the Sun stays close to the horizon, so shadows are long and sunlight comes in short windows.',
      statements: [
        { text: 'The Sun stays at a low elevation near the lunar south pole.', kind: 'measured' },
        { text: 'Sunlit hours for a site depend strongly on the terrain horizon.', kind: 'estimated' },
      ],
      citations: [{ label: 'Lunar illumination dataset (mock)', product_id: 'mock-ds-01' }, { label: 'SPICE ephemeris (mock)', product_id: 'mock-ds-02' }],
      no_evidence: false,
    }
  }
  if (s.includes('perseverance') || s.includes('rover') || s.includes('mars')) {
    return {
      answer: 'Perseverance is listed as active in the mock mission feed.',
      statements: [{ text: 'Perseverance landed on 18 Feb 2021.', kind: 'measured' }, { text: 'Total distance travelled is a modelled value.', kind: 'estimated' }],
      citations: [{ label: 'Mission status feed (mock)', product_id: 'mock-ds-04' }],
      no_evidence: false,
    }
  }
  return { answer: '', statements: [], citations: [], no_evidence: true }
}

export function sourceFor(target: string): SourceInfo {
  const kind = target.split(':')[0]
  return {
    name: kind === 'site' ? 'Candidate site record' : kind === 'result' ? 'Sun and Earth geometry (mock)' : 'Mock data source',
    link: 'https://www.nasa.gov',
    product_id: `mock-${target.replace(':', '-')}`,
    version: 'v0 (mock)',
    observed: '2026-11-01T00:00:00Z',
    retrieved: '2026-11-12T09:30:00Z',
    frame: 'documented lunar frame',
    units: 'degrees, hours, metres',
    method: kind === 'site' ? 'unknown' : 'modelled',
    uncertainty: 'Mock values. The backend team supplies real uncertainty.',
    notes: 'This record is placeholder data used by the front end template.',
    confidence: 'Estimated',
  }
}
