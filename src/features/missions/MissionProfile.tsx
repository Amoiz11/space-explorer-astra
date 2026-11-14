import { Link, useParams } from 'react-router-dom'
import { getMission } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate, orUnknown } from '../../utils/format'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'
import StatusChip from '../../components/StatusChip'

export default function MissionProfile() {
  const { missionId = '' } = useParams()
  const m = useAsync(() => getMission(missionId), [missionId])
  const openDrawer = useUI((u) => u.openDrawer)

  if (m.loading) return <div className="space-y-4"><Skeleton className="h-72" /><Skeleton className="h-48" /></div>
  if (m.error) return <ErrorState message={m.error.message} onRetry={m.retry} />
  const d = m.data
  if (!d) return <GlassCard title="Mission not found"><p className="text-[var(--text-2)]">There is no mission with this ID. <Link className="text-[var(--earth)] hover:underline" to="/missions">Back to missions</Link></p></GlassCard>
  const date = (v: string | null) => (v ? formatDate(v) : 'Unknown')

  return (
    <div className="space-y-6">
      <PageHero
        title={d.name}
        subtitle={d.summary}
        chips={<><StatusChip status={d.status} />{d.types.map((t) => <Chip key={t} label={t} />)}</>}
        scene={{ body: d.body, mode: 'rise' }}
        actions={<>
          <Link to={`/explorers/${d.explorer_id}/map`} className="btn btn-primary">Map</Link>
          <Link to={`/explorers/${d.explorer_id}/gallery`} className="btn btn-secondary">Gallery</Link>
          <Link to={`/time-machine?explorer=${d.explorer_id}`} className="btn btn-secondary">Time Machine</Link>
        </>}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Dates" className="lg:col-span-1">
          <dl className="space-y-4">
            <div><dt className="text-xs text-[var(--text-2)]">Launch</dt><dd className="mono">{date(d.launch)}</dd></div>
            <div><dt className="text-xs text-[var(--text-2)]">Landing</dt><dd className="mono">{d.landing ? formatDate(d.landing) : 'Not applicable'}</dd></div>
            <div><dt className="text-xs text-[var(--text-2)]">Last communication</dt><dd className="mono">{date(d.last_communication)}</dd></div>
            <div><dt className="text-xs text-[var(--text-2)]">Latest published position</dt><dd className="mono">{date(d.last_location)}</dd></div>
            <div><dt className="text-xs text-[var(--text-2)]">Last image</dt><dd className="mono">{date(d.last_image)}</dd></div>
          </dl>
          <button type="button" onClick={() => openDrawer(`mission:${d.id}`)} className="mt-4 text-xs text-[var(--earth)] hover:underline">Details</button>
        </GlassCard>

        <GlassCard title="Status history" className="lg:col-span-2">
          <ol className="relative space-y-5 border-l border-[var(--border)] pl-6">
            {d.status_history.map((h, i) => (
              <li key={i} className="relative">
                <span aria-hidden className="absolute -left-[31px] top-1 h-2.5 w-2.5 rounded-full bg-[var(--earth)]" />
                <div className="flex flex-wrap items-center gap-3"><StatusChip status={h.status} /><span className="mono text-xs text-[var(--text-2)]">from {orUnknown(h.from) === 'Unknown' ? 'Unknown' : formatDate(h.from)}</span></div>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-xs text-[var(--text-2)]">Loss of communication does not mean the explorer is dead. Communication status and mission status are kept separate.</p>
        </GlassCard>

        <GlassCard title="Instruments">
          {d.instruments.length ? <div className="flex flex-wrap gap-2">{d.instruments.map((i) => <Chip key={i} label={i} color="var(--text-1)" />)}</div> : <p className="text-[var(--text-2)]">Data not available.</p>}
        </GlassCard>

        <GlassCard title="Key events" className="lg:col-span-2">
          <ul className="divide-y divide-[var(--border)]">
            {d.events.map((e, i) => <li key={i} className="flex justify-between gap-3 py-2"><span>{e.title}</span><span className="mono text-xs text-[var(--text-2)]">{formatDate(e.date)}</span></li>)}
          </ul>
        </GlassCard>

        {d.telemetry && (
          <GlassCard title="Telemetry">
            <dl className="grid grid-cols-2 gap-4">
              {d.telemetry.power_w !== null && <div><dt className="text-xs text-[var(--text-2)]">Power</dt><dd className="mono text-xl">{d.telemetry.power_w} W</dd></div>}
              {d.telemetry.battery_pct !== null && <div><dt className="text-xs text-[var(--text-2)]">Battery</dt><dd className="mono text-xl">{d.telemetry.battery_pct} %</dd></div>}
            </dl>
          </GlassCard>
        )}

        <GlassCard title="Sources" className={d.telemetry ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <ul className="space-y-1">{d.sources.map((s) => <li key={s.url}><a className="text-[var(--earth)] hover:underline" href={s.url} target="_blank" rel="noreferrer">{s.name}</a></li>)}</ul>
        </GlassCard>
      </div>
    </div>
  )
}
