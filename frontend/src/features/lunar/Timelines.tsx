import { useState } from 'react'
import type { EarthWindow, IlluminationWindow, Site, SiteResult, SunEarthSample } from '../../types'
import { addDaysIso } from '../../utils/dates'
import { formatTime, formatWindowEnd } from '../../utils/format'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import SiteChip from '../../components/SiteChip'
import WindowsTable from './WindowsTable'

type Props = { results: SiteResult[]; sites: Site[]; start: string; days: number; day: number; setDay: (n: number) => void }

const DAY = 86400000

const clip = <T extends { start: string; end: string }>(w: T, d0: number): (T & { cs: string; ce: string; ch: number }) | null => {
  const s = Math.max(Date.parse(w.start), d0)
  const e = Math.min(Date.parse(w.end), d0 + DAY)
  if (e <= s) return null
  return { ...w, cs: new Date(s).toISOString(), ce: new Date(e).toISOString(), ch: Math.round(((e - s) / 3600000) * 100) / 100 }
}

function DayPicker({ days, day, setDay }: { days: number; day: number; setDay: (n: number) => void }) {
  if (days <= 1) return null
  return (
    <label className="flex items-center gap-2 text-xs text-[var(--text-2)]">
      Day
      <select className="field !w-auto !py-1" value={day} onChange={(e) => setDay(Number(e.target.value))} aria-label="Day of the range">
        {Array.from({ length: days }, (_, i) => <option key={i} value={i}>{i + 1} of {days}</option>)}
      </select>
    </label>
  )
}

function SunStateTimeline({ samples, d0 }: { samples: SunEarthSample[]; d0: number }) {
  const [hover, setHover] = useState<string | null>(null)
  const daySamples = samples.filter((s) => {
    const t = Date.parse(s.t)
    return t >= d0 && t < d0 + DAY
  })

  if (!daySamples.length) {
    return <p className="text-xs text-[var(--text-2)]">No simulation data for this date.</p>
  }

  const stepPct = 100 / daySamples.length

  return (
    <div>
      <div className="relative flex h-9 overflow-hidden rounded-[10px] border border-[var(--border)] bg-black/60" role="img" aria-label="Sunlight three-state timeline">
        {daySamples.map((s, i) => {
          const status = s.sun_status || (s.sun.el > 0 ? 'lit' : 'shadow')
          const frac = typeof s.sun_fraction === 'number' ? s.sun_fraction : status === 'lit' ? 1.0 : 0.0

          let bg = 'rgba(0,0,0,0.6)'
          let label = `Shadow (${formatTime(s.t)} UTC)`
          if (status === 'lit' || frac >= 0.99) {
            bg = 'var(--sun)'
            label = `Fully lit (100% at ${formatTime(s.t)} UTC)`
          } else if (status === 'partial' || frac > 0) {
            bg = 'linear-gradient(135deg, rgba(245,158,11,0.7) 25%, rgba(217,119,6,0.5) 50%, rgba(245,158,11,0.7) 75%)'
            label = `Partial (${Math.round(frac * 100)}% lit at ${formatTime(s.t)} UTC)`
          }

          return (
            <div
              key={s.t || i}
              className="h-full cursor-pointer transition-[filter] hover:brightness-125"
              style={{ width: `${stepPct}%`, background: bg }}
              onMouseEnter={() => setHover(label)}
              onMouseLeave={() => setHover(null)}
              title={label}
            />
          )
        })}
      </div>
      <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]">
        {[0, 6, 12, 18, 24].map((h) => <span key={h}>{String(h).padStart(2, '0')}:00</span>)}
      </div>
      <p className="mt-1 h-4 text-xs text-[var(--text-2)]" aria-live="polite">{hover ?? ''}</p>
    </div>
  )
}

function EarthStateTimeline({ samples, d0 }: { samples: SunEarthSample[]; d0: number }) {
  const [hover, setHover] = useState<string | null>(null)
  const daySamples = samples.filter((s) => {
    const t = Date.parse(s.t)
    return t >= d0 && t < d0 + DAY
  })

  if (!daySamples.length) {
    return <p className="text-xs text-[var(--text-2)]">No simulation data for this date.</p>
  }

  const stepPct = 100 / daySamples.length

  return (
    <div>
      <div className="relative flex h-9 overflow-hidden rounded-[10px] border border-[var(--border)] bg-black/60" role="img" aria-label="Earth visibility three-state timeline">
        {daySamples.map((s, i) => {
          const status = s.earth_status || (s.earth.el > 0 ? 'clear' : 'below_horizon')

          let bg = 'rgba(239,68,68,0.35)'
          let label = `Below horizon (${formatTime(s.t)} UTC)`
          if (status === 'clear') {
            bg = 'var(--ok)'
            label = `Clear line-of-sight (${formatTime(s.t)} UTC)`
          } else if (status === 'blocked_by_terrain') {
            bg = '#F97316'
            label = `Blocked by terrain (${formatTime(s.t)} UTC)`
          }

          return (
            <div
              key={s.t || i}
              className="h-full cursor-pointer transition-[filter] hover:brightness-125"
              style={{ width: `${stepPct}%`, background: bg }}
              onMouseEnter={() => setHover(label)}
              onMouseLeave={() => setHover(null)}
              title={label}
            />
          )
        })}
      </div>
      <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]">
        {[0, 6, 12, 18, 24].map((h) => <span key={h}>{String(h).padStart(2, '0')}:00</span>)}
      </div>
      <p className="mt-1 h-4 text-xs text-[var(--text-2)]" aria-live="polite">{hover ?? ''}</p>
    </div>
  )
}

export function SunlightTimeline({ results, sites, start, days, day, setDay }: Props) {
  const dayStart = addDaysIso(start, day)
  const d0 = Date.parse(dayStart)

  return (
    <GlassCard id="sunlight" title="Illumination timeline" action={<DayPicker days={days} day={day} setDay={setDay} />}>
      {/* Legend */}
      <div className="mb-4 flex flex-wrap items-center gap-4 text-xs text-[var(--text-2)]" aria-label="Illumination state legend">
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[var(--sun)]" /> Fully lit</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[#D97706]" /> Partial (penumbra/disk fraction)</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded border border-white/20 bg-black/60" /> Shadow</span>
      </div>

      <div className="space-y-6">
        {results.map((r) => {
          const idx = sites.findIndex((s) => s.id === r.siteId)
          const rows = r.windows.illumination.windows.map((w) => clip<IlluminationWindow>(w, d0)).filter((w) => w !== null)

          return (
            <div key={r.siteId}>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? r.siteId}</h3>
                <div className="flex items-center gap-2">
                  <span className="mono text-xs text-[var(--text-2)]">
                    Any lit: <span className="text-[var(--sun)]">{r.windows.illumination.hours_any_part_lit.toFixed(1)}h</span> | Fully lit: {r.windows.illumination.hours_fully_lit.toFixed(1)}h | Shadow: {r.windows.illumination.hours_shadow.toFixed(1)}h
                  </span>
                  <MethodChip method={r.windows.label} />
                </div>
              </div>

              <SunStateTimeline samples={r.sunEarth.samples} d0={d0} />

              <WindowsTable
                rows={rows}
                empty="No continuous lit window on this day."
                columns={[
                  { header: 'Start (UTC)', cell: (w) => formatTime(w.cs) },
                  { header: 'End (UTC)', cell: (w) => formatWindowEnd(w.ce, w.cs) },
                  { header: 'Duration', cell: (w) => `${w.ch} h`, align: 'right' },
                ]}
              />
            </div>
          )
        })}
      </div>
    </GlassCard>
  )
}

export function EarthTimeline({ results, sites, start, days, day, setDay }: Props) {
  const dayStart = addDaysIso(start, day)
  const d0 = Date.parse(dayStart)

  return (
    <GlassCard id="earth" title="Direct-to-Earth Communication timeline" action={<DayPicker days={days} day={day} setDay={setDay} />}>
      <p className="mb-3 rounded-[10px] border border-[var(--border)] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-2)]">
        Geometric visibility only. Not a guaranteed radio link.
      </p>

      {/* Legend */}
      <div className="mb-4 flex flex-wrap items-center gap-4 text-xs text-[var(--text-2)]" aria-label="Earth visibility state legend">
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[var(--ok)]" /> Clear line-of-sight</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[#F97316]" /> Blocked by terrain</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[rgba(239,68,68,0.5)]" /> Below horizon</span>
      </div>

      <div className="space-y-6">
        {results.map((r) => {
          const idx = sites.findIndex((s) => s.id === r.siteId)
          const rows = r.windows.earth_visibility.windows.map((w) => clip<EarthWindow>(w, d0)).filter((w) => w !== null)

          return (
            <div key={r.siteId}>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? r.siteId}</h3>
                <div className="flex items-center gap-2">
                  <span className="mono text-xs text-[var(--text-2)]">
                    Clear: <span className="text-[var(--ok)]">{r.windows.earth_visibility.total_visible_h.toFixed(1)}h</span> | Blocked: {r.windows.earth_visibility.blocked_by_terrain_hours.toFixed(1)}h | Below: {r.windows.earth_visibility.below_horizon_hours.toFixed(1)}h
                  </span>
                  <MethodChip method={r.windows.label} />
                </div>
              </div>

              <EarthStateTimeline samples={r.sunEarth.samples} d0={d0} />

              <WindowsTable
                rows={rows}
                empty="Earth is not visible on this day."
                columns={[
                  { header: 'Start (UTC)', cell: (w) => formatTime(w.cs) },
                  { header: 'End (UTC)', cell: (w) => formatWindowEnd(w.ce, w.cs) },
                  { header: 'Duration', cell: (w) => `${w.ch} h`, align: 'right' },
                  { header: 'Earth azimuth', cell: (w) => `${w.earth_az}°`, align: 'right' },
                  { header: 'Earth elevation', cell: (w) => `${w.earth_el}°`, align: 'right' },
                  { header: 'Obstruction', cell: (w) => (w.obstruction === 'clear' ? 'Clear' : w.obstruction === 'blocked' ? 'Blocked' : 'Unknown') },
                ]}
              />
            </div>
          )
        })}
      </div>

      <div className="mt-6 rounded-[12px] border border-[var(--border)] bg-white/[0.02] p-4">
        <h3 className="text-[15px] font-medium text-[var(--text-1)]">Relay satellite communication</h3>
        <p className="mt-1 text-sm text-[var(--text-2)]">
          Relay satellite communication is not modelled. Direct-to-Earth line-of-sight only. Relay satellites or orbital nodes are not modelled (LL-21).
        </p>
      </div>
    </GlassCard>
  )
}
