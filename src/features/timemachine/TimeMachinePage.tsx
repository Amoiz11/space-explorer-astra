import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAllMissions, getExplorerImages, getExplorerLocations, getMission } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

const DAY = 86400000
const thumb = (hue: number) => `linear-gradient(135deg, hsl(${hue} 45% 28%), hsl(${(hue + 40) % 360} 50% 12%))`

export default function TimeMachinePage() {
  const [params, setParams] = useSearchParams()
  const explorer = params.get('explorer') ?? 'perseverance'
  const missions = useAsync(getAllMissions, [])
  const data = useAsync(async () => {
    const [mission, positions, images] = await Promise.all([getMission(explorer), getExplorerLocations(explorer), getExplorerImages(explorer)])
    return { mission, positions, images }
  }, [explorer])

  const range = useMemo(() => {
    const m = data.data?.mission
    if (!m) return null
    const start = Date.parse(m.landing ?? m.launch ?? '2020-01-01')
    const end = Date.parse(m.last_communication ?? '2026-11-12')
    return { start, days: Math.max(1, Math.round((end - start) / DAY)) }
  }, [data.data])

  const [day, setDay] = useState(6)
  useEffect(() => { setDay(6) }, [explorer])

  const body = (() => {
    if (data.loading) return <Skeleton className="h-64" />
    if (data.error) return <ErrorState message={data.error.message} onRetry={data.retry} />
    if (!data.data?.mission || !range) return <p className="text-[var(--text-2)]">Data not available.</p>
    const { mission, positions, images } = data.data
    const selMs = range.start + day * DAY
    const iso = new Date(selMs).toISOString().slice(0, 10)
    const rec = positions.find((p) => p.date === iso)
    const lastBefore = [...positions].filter((p) => p.date < iso && p.kind !== 'unknown').pop()
    const events = mission.events.filter((e) => e.date <= iso).slice(-4).reverse()
    const near = images.filter((i) => Math.abs(Date.parse(i.captured) - selMs) <= 5 * DAY)
    const pct = (ms: number) => Math.min(100, Math.max(0, ((ms - range.start) / (range.days * DAY)) * 100))

    return (
      <div className="space-y-6">
        <GlassCard>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-[var(--text-2)]">Date</p>
            <p className="mono text-2xl">{formatDate(iso)}</p>
          </div>
          <div className="relative mt-4 pt-5">
            <div aria-hidden className="absolute inset-x-0 top-0 h-4">
              {mission.events.map((e, i) => <span key={i} title={e.title} className="absolute top-0 h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-[var(--sun)]" style={{ left: `${pct(Date.parse(e.date))}%` }} />)}
              {images.map((im) => <span key={im.id} className="absolute top-3 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[var(--earth)]" style={{ left: `${pct(Date.parse(im.captured))}%` }} />)}
            </div>
            <input type="range" min={0} max={range.days} value={day} onChange={(e) => setDay(Number(e.target.value))} className="w-full accent-[var(--earth)]" aria-label="Mission date" />
            <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]"><span>{formatDate(new Date(range.start).toISOString())}</span><span>{formatDate(new Date(range.start + range.days * DAY).toISOString())}</span></div>
          </div>
          <p className="mt-2 flex gap-4 text-xs text-[var(--text-2)]"><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[var(--sun)]" />Events</span><span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[var(--earth)]" />Images</span></p>
        </GlassCard>

        <div className="grid gap-6 lg:grid-cols-3">
          <GlassCard title="Map position">
            {rec && rec.kind !== 'unknown' ? (
              <>
                <svg viewBox="0 0 300 160" className="w-full rounded-[10px] bg-[#070b16]" role="img" aria-label="Position on placeholder map">
                  <circle cx={(rec.x ?? 0) * 3} cy={(rec.y ?? 0) * 1.6} r="7" fill={rec.kind === 'measured' ? 'var(--text-1)' : 'none'} stroke={rec.kind === 'interpolated' ? 'var(--est)' : 'var(--text-1)'} strokeWidth="2" strokeDasharray={rec.kind === 'interpolated' ? '3 3' : undefined} />
                </svg>
                <p className="mt-3 text-sm">Position type: <span className="text-[var(--text-1)]">{rec.kind}</span></p>
              </>
            ) : (
              <>
                <p className="text-[var(--text-1)]">No record for this date</p>
                <p className="mt-1 text-sm text-[var(--text-2)]">Nothing is filled in between records.</p>
                {lastBefore && <p className="mt-3 text-sm text-[var(--text-2)]">Last recorded position: <span className="mono text-[var(--text-1)]">{formatDate(lastBefore.date)}</span></p>}
              </>
            )}
          </GlassCard>
          <GlassCard title="Events up to this date">
            {events.length ? <ul className="divide-y divide-[var(--border)]">{events.map((e, i) => <li key={i} className="flex justify-between gap-3 py-2 text-sm"><span>{e.title}</span><span className="mono text-xs text-[var(--text-2)]">{formatDate(e.date)}</span></li>)}</ul> : <p className="text-[var(--text-2)]">No record for this date</p>}
          </GlassCard>
          <GlassCard title="Images within 5 days">
            {near.length ? <div className="grid grid-cols-3 gap-2">{near.map((im) => <div key={im.id} title={`${im.camera}, ${formatDate(im.captured)}`} className="aspect-square rounded-[10px]" style={{ background: thumb(im.hue) }} />)}</div> : <p className="text-[var(--text-2)]">No record for this date</p>}
          </GlassCard>
        </div>
      </div>
    )
  })()

  return (
    <div className="space-y-6">
      <PageHero title="Mission Time Machine" subtitle="Scrub through a mission and see what is on record." chips={<Chip label="Mock data" color="var(--est)" />} scene={{ body: 'earth', mode: 'side', moon: true }} />
      <div className="max-w-xs"><label htmlFor="tm-ex" className="mb-1 block text-xs text-[var(--text-2)]">Mission</label>
        <select id="tm-ex" className="field" value={explorer} onChange={(e) => setParams({ explorer: e.target.value })}>
          {(missions.data ?? []).map((m) => <option key={m.id} value={m.explorer_id}>{m.name}</option>)}
          {!missions.data && <option value={explorer}>{explorer}</option>}
        </select></div>
      {body}
    </div>
  )
}
