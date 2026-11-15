import { useMemo } from 'react'
import * as d3 from 'd3'
import type { Site, SiteResult } from '../../types'
import { useLunarStore } from '../../store/lunar'
import { useWidth } from '../../utils/useSize'
import { formatHour } from '../../utils/format'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import SiteChip from '../../components/SiteChip'

type Props = { results: SiteResult[]; sites: Site[] }

const H = 280
const M = { t: 16, r: 16, b: 34, l: 40 }
const TICKS: Record<number, string> = { 0: 'N', 90: 'E', 180: 'S', 270: 'W', 360: 'N' }

function Chart({ r, index, name, yDomain }: { r: SiteResult; index: number; name: string; yDomain: [number, number] }) {
  const { ref, width } = useWidth<HTMLDivElement>()
  const time = useLunarStore((s) => s.timeOfDay)
  const iw = width - M.l - M.r
  const ih = H - M.t - M.b
  const x = useMemo(() => d3.scaleLinear().domain([0, 360]).range([0, iw]), [iw])
  const y = useMemo(() => d3.scaleLinear().domain(yDomain).range([ih, 0]), [yDomain, ih])

  const samples = r.sunEarth.samples
  const day0 = Date.parse(r.sunEarth.start)
  const idx = Math.min(samples.length - 1, Math.max(0, Math.round((time * 60) / r.sunEarth.step_minutes)))
  const cur = samples[idx]
  const prof = r.sunEarth.horizon_profile

  // trail for the first day only (az wraps at 360, so break the line there)
  const daySamples = samples.filter((s) => Date.parse(s.t) < day0 + 86400000)
  const trail = (body: 'sun' | 'earth') => {
    const segs: string[] = []
    let seg: [number, number][] = []
    let lastAz = -1
    daySamples.forEach((s) => {
      const az = s[body].az
      if (lastAz >= 0 && Math.abs(az - lastAz) > 180) { segs.push(d3.line()(seg) ?? ''); seg = [] }
      seg.push([x(az), y(s[body].el)])
      lastAz = az
    })
    if (seg.length) segs.push(d3.line()(seg) ?? '')
    return segs.join(' ')
  }

  const area = prof
    ? d3.area<{ az: number; el: number }>().x((p) => x(p.az)).y0(y(yDomain[0])).y1((p) => y(p.el)).curve(d3.curveStepAfter)(
        [...prof, { az: 360, el: prof[0].el }],
      ) ?? ''
    : null

  const stride = samples.length > 24 ? Math.ceil(samples.length / 24) : 1
  const tableRows = samples.filter((_, i) => i % stride === 0).slice(0, 24)

  const sunAbove = cur && cur.sun.el > 0
  const earthAbove = cur && cur.earth.el > 0
  const yTicks = y.ticks(6)
  const maxSunEl = samples.length ? Math.max(...samples.map((s) => s.sun.el)).toFixed(1) : 'Unknown'
  const maxEarthEl = samples.length ? Math.max(...samples.map((s) => s.earth.el)).toFixed(1) : 'Unknown'
  const summary = `Sun elevation reaches ${maxSunEl} degrees and Earth elevation reaches ${maxEarthEl} degrees on the first day for ${name}.`

  return (
    <div className="rounded-[14px] border border-[var(--border)] bg-black/20 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={index} />{name}</h3>
        <MethodChip method={r.sunEarth.method} />
      </div>
      <div ref={ref} className="w-full">
        <svg width={width} height={H} role="img" aria-label={summary}>
          <defs>
            <filter id={`glow-${index}`} x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4" /></filter>
          </defs>
          <g transform={`translate(${M.l},${M.t})`}>
            <rect x={0} y={y(0)} width={iw} height={Math.max(0, ih - y(0))} fill="rgba(0,0,0,0.45)" />
            <text x={iw - 6} y={ih - 8} textAnchor="end" fontSize="12" fill="var(--text-2)">Below horizon</text>
            {yTicks.map((t) => (
              <g key={t}>
                <line x1={0} x2={iw} y1={y(t)} y2={y(t)} stroke="rgba(255,255,255,0.06)" />
                <text x={-8} y={y(t)} dy="0.32em" textAnchor="end" fontSize="12" fill="var(--text-2)">{t}°</text>
              </g>
            ))}
            {[0, 90, 180, 270, 360].map((a) => (
              <g key={a}>
                <line x1={x(a)} x2={x(a)} y1={0} y2={ih} stroke="rgba(255,255,255,0.06)" />
                <text x={x(a)} y={ih + 20} textAnchor={a === 0 ? 'start' : a === 360 ? 'end' : 'middle'} fontSize="12" fill="var(--text-2)">{TICKS[a]}</text>
              </g>
            ))}
            {area && <path d={area} fill="rgba(160,170,190,0.22)" stroke="rgba(160,170,190,0.4)" />}
            <line x1={0} x2={iw} y1={y(0)} y2={y(0)} stroke="var(--text-1)" strokeWidth={2.5} />
            <path d={trail('sun')} fill="none" stroke="var(--sun)" strokeOpacity={0.35} strokeWidth={2} />
            <path d={trail('earth')} fill="none" stroke="var(--earth)" strokeOpacity={0.35} strokeWidth={2} />
            {cur && (
              <>
                <g transform={`translate(${x(cur.sun.az)}, ${y(cur.sun.el)})`} className="transition-transform duration-150">
                  <circle r={12} fill="var(--sun)" opacity={0.7} filter={`url(#glow-${index})`} />
                  <circle r={6} fill="var(--sun)" />
                </g>
                <g transform={`translate(${x(cur.earth.az)}, ${y(cur.earth.el)})`} className="transition-transform duration-150">
                  <circle r={9} fill="var(--earth)" opacity={0.6} filter={`url(#glow-${index})`} />
                  <circle r={5} fill="var(--earth)" />
                </g>
              </>
            )}
          </g>
        </svg>
      </div>
      {!prof && <p className="mt-1 text-xs text-[var(--text-2)]">Terrain horizon not available.</p>}
      {Boolean(r.sunEarth.cut_azimuth_count && r.sunEarth.cut_azimuth_count > 0) && (
        <div className="mt-2 rounded-[8px] border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs text-amber-200">
          ⚠️ DEM coverage boundary reached: {r.sunEarth.cut_azimuth_count} azimuth directions were cut by the DEM coverage boundary (75°S). Horizon elevation in those directions may be underestimated.
        </div>
      )}
      <div className="mt-2 text-xs text-[var(--text-2)]">
        Spherical curvature drop (Moon radius 1,737.4 km, approx {r.sunEarth.curvature_drop_deg ?? 1.65}° drop at 100 km ray horizon) applied during ray-marching. Cut by coverage: <span className="mono">{r.sunEarth.cut_azimuth_count ?? 0}</span> directions.
      </div>
      {cur ? (
        <div className="mt-2 grid gap-2 text-sm sm:grid-cols-2" aria-live="polite">
          <p className="rounded-[10px] bg-white/5 px-3 py-2">
            <span className="text-[var(--sun)]">Sun</span> at {formatHour(time)} UTC: az <span className="mono">{cur.sun.az.toFixed(1)}°</span>, el <span className="mono">{cur.sun.el.toFixed(1)}°</span>. {sunAbove ? 'Above 0° horizon' : 'Below 0° horizon'}
          </p>
          <p className="rounded-[10px] bg-white/5 px-3 py-2">
            <span className="text-[var(--earth)]">Earth</span> at {formatHour(time)} UTC: az <span className="mono">{cur.earth.az.toFixed(1)}°</span>, el <span className="mono">{cur.earth.el.toFixed(1)}°</span>. {earthAbove ? 'Above 0° horizon' : 'Below 0° horizon'}
          </p>
        </div>
      ) : (
        <p className="mt-2 text-xs text-[var(--text-2)]">No series data available for this date.</p>
      )}
      <details className="mt-2 text-xs text-[var(--text-2)]">
        <summary className="cursor-pointer">Data table ({tableRows.length} points)</summary>
        <div className="mt-2 max-h-40 overflow-auto">
          <table className="w-full text-left">
            <thead><tr><th className="py-1">Time (UTC)</th><th>Sun az</th><th>Sun el</th><th>Earth az</th><th>Earth el</th></tr></thead>
            <tbody>
              {tableRows.map((s) => (
                <tr key={s.t} className="mono"><td className="py-0.5">{s.t.slice(5, 16).replace('T', ' ')}</td><td>{s.sun.az.toFixed(1)}°</td><td>{s.sun.el.toFixed(1)}°</td><td>{s.earth.az.toFixed(1)}°</td><td>{s.earth.el.toFixed(1)}°</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}

export default function HorizonChart({ results, sites }: Props) {
  const time = useLunarStore((s) => s.timeOfDay)
  const setTime = useLunarStore((s) => s.setTime)

  const yDomain = useMemo<[number, number]>(() => {
    const allEls = results.flatMap((r) => [
      ...r.sunEarth.samples.flatMap((s) => [s.sun.el, s.earth.el]),
      ...(r.sunEarth.horizon_profile?.map((p) => p.el) ?? []),
    ])
    if (!allEls.length) return [-5, 25]
    const minVal = Math.min(...allEls)
    const maxVal = Math.max(...allEls)
    const lo = Math.min(-4, Math.floor(minVal - 1))
    const hi = Math.max(10, Math.ceil(maxVal + 2))
    return [lo, hi]
  }, [results])

  return (
    <GlassCard id="horizon" title="Sun and Earth horizon chart" glow
      action={<div className="flex items-center gap-2 text-xs text-[var(--text-2)]"><span className="inline-flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[var(--sun)]" />Sun</span><span className="inline-flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[var(--earth)]" />Earth</span></div>}>
      <div className="mb-4">
        <label htmlFor="scrub" className="mb-1 block text-xs text-[var(--text-2)]">Time scrubber (UTC): <span className="mono text-[var(--text-1)]">{formatHour(time)}</span></label>
        <input id="scrub" type="range" min={0} max={24} step={0.25} value={time} onChange={(e) => setTime(Number(e.target.value))} className="w-full accent-[var(--earth)]" />
      </div>
      <div className="space-y-4">
        {results.map((r) => {
          const idx = sites.findIndex((s) => s.id === r.siteId)
          return <Chart key={r.siteId} r={r} index={Math.max(idx, 0)} name={sites[idx]?.name ?? r.siteId} yDomain={yDomain} />
        })}
      </div>
    </GlassCard>
  )
}
