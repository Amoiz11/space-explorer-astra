import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { getBodies, getMissions } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import PageHeader from '../../components/PageHeader'
import Skeleton from '../../components/Skeleton'
import StatusChip from '../../components/StatusChip'
import TiltCard from '../../components/TiltCard'

type BodyId = 'mars' | 'moon'
const bodyArt: Record<BodyId, string> = {
  mars: 'radial-gradient(circle at 35% 30%, #E5835A, #6b2a16 55%, #1a0a07 80%)',
  moon: 'radial-gradient(circle at 35% 30%, #E8ECF4, #6c768a 55%, #10131c 80%)',
}

function MissionList({ body }: { body: BodyId }) {
  const list = useAsync(() => getMissions(body), [body])
  if (list.loading) return <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-40" /><Skeleton className="h-40" /></div>
  if (list.error) return <ErrorState message={list.error.message} onRetry={list.retry} />
  if (!list.data?.length) return <p className="text-[var(--text-2)]">No missions for this body yet.</p>
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {list.data.map((m) => (
        <TiltCard key={m.id} to={`/missions/${m.id}`} className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xl">{m.name}</h3>
            <StatusChip status={m.status} />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">{m.types.map((t) => <Chip key={t} label={t} />)}</div>
          <p className="mt-3 text-sm text-[var(--text-2)]">{m.summary}</p>
          <dl className="mono mt-4 grid grid-cols-2 gap-3 text-xs">
            <div><dt className="font-[family-name:var(--font-body)] text-[var(--text-2)]">Launch</dt><dd>{m.launch ? formatDate(m.launch) : 'Unknown'}</dd></div>
            <div><dt className="font-[family-name:var(--font-body)] text-[var(--text-2)]">Landing</dt><dd>{m.landing ? formatDate(m.landing) : 'Not applicable'}</dd></div>
          </dl>
        </TiltCard>
      ))}
    </div>
  )
}

export default function MissionsPage() {
  const bodies = useAsync(getBodies, [])
  const [body, setBody] = useState<BodyId | null>(null)

  return (
    <div className="space-y-8">
      <PageHeader
        key={body ?? 'none'}
        title="Missions"
        subtitle={body ? `Missions to ${body === 'mars' ? 'Mars' : 'the Moon'}.` : 'Choose a celestial body to browse its missions.'}
      />

      {!body ? (
        bodies.loading ? <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-56" /><Skeleton className="h-56" /></div>
        : bodies.error ? <ErrorState message={bodies.error.message} onRetry={bodies.retry} />
        : (
          <div className="grid gap-4 md:grid-cols-2">
            {(bodies.data ?? []).map((b) => (
              <button key={b.id} type="button" onClick={() => setBody(b.id)} className="text-left">
                <TiltCard className="flex items-center gap-6 p-7" glow>
                  <span aria-hidden className="h-28 w-28 shrink-0 rounded-full" style={{ background: bodyArt[b.id], boxShadow: '0 0 40px rgba(120,150,220,0.2)' }} />
                  <span>
                    <span className="block text-2xl">{b.name}</span>
                    <span className="mono mt-2 block text-sm text-[var(--text-2)]">{b.missionCount} missions</span>
                    <span className="mt-3 block text-sm text-[var(--earth)]">View missions</span>
                  </span>
                </TiltCard>
              </button>
            ))}
          </div>
        )
      ) : (
        <>
          <button type="button" className="btn btn-secondary" onClick={() => setBody(null)}><ArrowLeft size={14} /> Change body</button>
          <MissionList body={body} />
        </>
      )}
      <p className="text-xs text-[var(--text-2)]">Looking for the Moon landing tool? <Link className="text-[var(--earth)] hover:underline" to="/lunar">Open the Lunar Landing Navigator</Link>.</p>
    </div>
  )
}
