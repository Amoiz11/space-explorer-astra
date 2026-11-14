import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Info } from 'lucide-react'
import { compareMissions, getAllMissions } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

const tip = { background: '#0A0F1C', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, fontSize: 12 }
const fmt = (v: number | string) => (typeof v === 'number' ? v.toLocaleString('en-GB') : v)

export default function ComparePage() {
  const missions = useAsync(getAllMissions, [])
  const [ids, setIds] = useState<string[]>(['perseverance', 'curiosity'])
  const openDrawer = useUI((u) => u.openDrawer)
  const cmp = useAsync(() => compareMissions(ids), [ids.join(',')])
  const toggle = (id: string) => setIds((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
  const name = (id: string) => missions.data?.find((m) => m.id === id)?.name ?? id

  return (
    <div className="space-y-6">
      <PageHero title="Mission comparison" subtitle="Pick two or more missions and compare them side by side." chips={<Chip label="Mock data" color="var(--est)" />} scene={{ body: 'earth', mode: 'side', moon: true }} />

      <GlassCard title="Missions">
        {missions.loading ? <Skeleton className="h-12" /> : missions.error ? <ErrorState message={missions.error.message} onRetry={missions.retry} /> : (
          <div className="flex flex-wrap gap-2">
            {(missions.data ?? []).map((m) => (
              <label key={m.id} className={`btn btn-secondary cursor-pointer !px-3 !py-2 ${ids.includes(m.id) ? '!border-[var(--earth)]' : ''}`}>
                <input type="checkbox" className="sr-only" checked={ids.includes(m.id)} onChange={() => toggle(m.id)} />{m.name}
              </label>
            ))}
          </div>
        )}
      </GlassCard>

      {ids.length < 2 ? <EmptyState text="Pick at least two missions to compare." />
        : cmp.loading ? <Skeleton className="h-72" />
        : cmp.error ? <ErrorState message={cmp.error.message} onRetry={cmp.retry} />
        : !cmp.data?.length ? <EmptyState text="Data not available." /> : (
        <>
          <GlassCard title="Metrics">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] text-xs text-[var(--text-2)]">
                    <th className="py-2 pr-4 font-normal">Metric</th>
                    {ids.map((id) => <th key={id} className="py-2 pr-4 font-normal">{name(id)}</th>)}
                    <th className="py-2 pr-4 font-normal">Date range</th><th className="py-2 font-normal">Method</th>
                  </tr>
                </thead>
                <tbody>
                  {cmp.data.map((m) => (
                    <tr key={m.id} className="border-b border-[var(--border)]/60 last:border-0">
                      <td className="py-3 pr-4">
                        <span className="inline-flex items-center gap-2">{m.label} <span className="text-xs text-[var(--text-2)]">({m.unit})</span>
                          <button type="button" aria-label={`Details for ${m.label}`} onClick={() => openDrawer(`metric:${m.id}`)} className="text-[var(--earth)]"><Info size={14} /></button></span>
                      </td>
                      {ids.map((id) => <td key={id} className="mono pr-4">{fmt(m.values[id] ?? 'Unknown')}</td>)}
                      <td className="pr-4 text-xs text-[var(--text-2)]">{m.range}</td>
                      <td><MethodChip method={m.method} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>

          <div className="grid gap-6 md:grid-cols-3">
            {cmp.data.filter((m) => ['duration', 'distance', 'images'].includes(m.id)).map((m) => (
              <GlassCard key={m.id} title={`${m.label} (${m.unit})`}>
                <div className="h-48" role="img" aria-label={`${m.label} by mission`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={ids.map((id) => ({ name: name(id).split(' ')[0], value: Number(m.values[id] ?? 0) }))}>
                      <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9AA4B8' }} />
                      <YAxis tick={{ fontSize: 12, fill: '#9AA4B8' }} width={48} />
                      <Tooltip contentStyle={tip} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                      <Bar dataKey="value" fill="#9AA4B8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
