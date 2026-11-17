import { Link, useParams } from 'react-router-dom'
import { getMission } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate, orUnknown } from '../../utils/format'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHeader from '../../components/PageHeader'
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
  const date = (v: string | null) => {
    if (!v) return 'Unknown'
    if (v.startsWith('Sol')) return v
    return formatDate(v)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={d.name}
        subtitle={d.summary}
        chip={<><StatusChip status={d.status} />{d.types.map((t, i) => <Chip key={`${t}-${i}`} label={t} />)}</>}
        actions={<>
          <Link to={`/explorers/${d.explorer_id}/map`} className="btn btn-primary">Map</Link>
          <Link to={`/explorers/${d.explorer_id}/gallery`} className="btn btn-secondary">Gallery</Link>
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
          {d.instruments.length ? <div className="flex flex-wrap gap-2">{d.instruments.map((i, idx) => <Chip key={`${i}-${idx}`} label={i} color="var(--text-1)" />)}</div> : <p className="text-[var(--text-2)]">Data not available.</p>}
        </GlassCard>

        <GlassCard title="Key events" className="lg:col-span-2">
          <ul className="divide-y divide-[var(--border)]">
            {d.events.map((e, i) => <li key={i} className="flex justify-between gap-3 py-2"><span>{e.title}</span><span className="mono text-xs text-[var(--text-2)]">{formatDate(e.date)}</span></li>)}
          </ul>
        </GlassCard>

        <GlassCard title="Health condition">
          {d.health ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-[var(--text-1)]">{d.health.condition}</span>
                {d.health.label && <Chip label={d.health.label} />}
              </div>
              {d.health.evidence && (
                <div>
                  <div className="text-xs text-[var(--text-2)] mb-1">Evidence</div>
                  {Array.isArray(d.health.evidence) ? (
                    <ul className="list-disc list-inside text-xs space-y-1 text-[var(--text-2)]">
                      {d.health.evidence.map((ev: string, i: number) => <li key={i}>{ev}</li>)}
                    </ul>
                  ) : (
                    <p className="text-xs text-[var(--text-2)] leading-relaxed">{d.health.evidence}</p>
                  )}
                </div>
              )}
              {d.health.reported_at && (
                <div className="text-xs text-[var(--text-2)]">
                  Reported: <span className="mono">{formatDate(d.health.reported_at)}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-2)]">Health record: <span className="mono">Unknown</span> (not available in source data)</p>
          )}
        </GlassCard>

        <GlassCard title="Sources" className="lg:col-span-2">
          <ul className="space-y-1">{d.sources.map((s, i) => <li key={`${s.name}-${i}`}><a className="text-[var(--earth)] hover:underline" href={s.url} target="_blank" rel="noreferrer">{s.name}</a></li>)}</ul>
        </GlassCard>
      </div>
    </div>
  )
}
