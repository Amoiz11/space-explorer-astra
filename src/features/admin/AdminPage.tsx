import { useState } from 'react'
import { deleteSite, getDatasets, getImports, getSites, updateSite } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate, formatDateTime } from '../../utils/format'
import { useRole } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import Skeleton from '../../components/Skeleton'
import AddSiteForm from '../lunar/AddSiteForm'

const tabs = ['Data imports', 'Datasets', 'Candidate sites', 'Calculation settings'] as const
type Tab = (typeof tabs)[number]
const statusColor = { ok: 'var(--ok)', warning: 'var(--text-1)', failed: 'var(--blocked)' }
const statusText = { ok: 'OK', warning: 'Warnings', failed: 'Failed' }

function Imports() {
  const r = useAsync(getImports, [])
  if (r.loading) return <Skeleton className="h-40" />
  if (r.error) return <ErrorState message={r.error.message} onRetry={r.retry} />
  return (
    <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm">
      <thead><tr className="border-b border-[var(--border)] text-xs text-[var(--text-2)]"><th className="py-2 font-normal">Dataset</th><th className="font-normal">Status</th><th className="font-normal">Warnings</th><th className="font-normal">Rejected</th><th className="font-normal">When (UTC)</th></tr></thead>
      <tbody>{(r.data ?? []).map((i) => (
        <tr key={i.id} className="border-b border-[var(--border)]/60"><td className="py-2">{i.dataset}</td><td><Chip label={statusText[i.status]} color={statusColor[i.status]} /></td><td className="mono">{i.warnings}</td><td className="mono">{i.rejected}</td><td className="mono text-xs">{formatDateTime(i.when)}</td></tr>
      ))}</tbody>
    </table></div>
  )
}

function Datasets() {
  const r = useAsync(getDatasets, [])
  if (r.loading) return <Skeleton className="h-40" />
  if (r.error) return <ErrorState message={r.error.message} onRetry={r.retry} />
  return <ul className="divide-y divide-[var(--border)]">{(r.data ?? []).map((d) => <li key={d.id} className="flex justify-between gap-3 py-3 text-sm"><span>{d.name} <span className="text-[var(--text-2)]">({d.source})</span></span><span className="mono text-xs text-[var(--text-2)]">{formatDate(d.updated)}</span></li>)}</ul>
}

function Sites() {
  const r = useAsync(getSites, [])
  const [busy, setBusy] = useState(false)
  if (r.loading && !r.data) return <Skeleton className="h-40" />
  if (r.error && !r.data) return <ErrorState message={r.error.message} onRetry={r.retry} />
  const rename = async (id: string) => {
    const s = r.data?.find((x) => x.id === id)
    const name = window.prompt('New site name', s?.name ?? '')
    if (!s || !name?.trim()) return
    setBusy(true)
    try { await updateSite({ ...s, name: name.trim() }); r.retry() } finally { setBusy(false) }
  }
  const remove = async (id: string) => {
    if (!window.confirm('Delete this site?')) return
    setBusy(true)
    try { await deleteSite(id); r.retry() } finally { setBusy(false) }
  }
  return (
    <div>
      <ul className="divide-y divide-[var(--border)]">
        {(r.data ?? []).map((s) => (
          <li key={s.id} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
            <span>{s.name} <span className="mono text-xs text-[var(--text-2)]">{s.coordinates.values.join(', ')} {s.coordinates.units}</span></span>
            <span className="flex gap-2"><button disabled={busy} onClick={() => void rename(s.id)} className="btn btn-secondary !px-3 !py-1.5">Edit</button><button disabled={busy} onClick={() => void remove(s.id)} className="btn btn-secondary !px-3 !py-1.5 text-[var(--blocked)]">Delete</button></span>
          </li>
        ))}
      </ul>
      <AddSiteForm onCreated={r.retry} />
    </div>
  )
}

function Settings() {
  const [saved, setSaved] = useState(false)
  return (
    <form className="grid max-w-md gap-3" onSubmit={(e) => { e.preventDefault(); setSaved(true) }}>
      <div><label htmlFor="st" className="mb-1 block text-xs text-[var(--text-2)]">Step (minutes)</label><input id="st" className="field" defaultValue="10" /></div>
      <div><label htmlFor="hz" className="mb-1 block text-xs text-[var(--text-2)]">Horizon source</label><input id="hz" className="field" defaultValue="mock profile" /></div>
      <div><label htmlFor="fr" className="mb-1 block text-xs text-[var(--text-2)]">Default coordinate frame</label><input id="fr" className="field" defaultValue="documented lunar frame" /></div>
      <button className="btn btn-primary w-fit" type="submit">Save settings</button>
      {saved && <p className="text-xs text-[var(--text-2)]">Saved in the template only. The backend team connects this form.</p>}
    </form>
  )
}

export default function AdminPage() {
  const role = useRole()
  const [tab, setTab] = useState<Tab>('Data imports')

  if (role !== 'Admin') {
    return <GlassCard title="Admin only"><p className="text-[var(--text-2)]">This area is for administrators. Open it with <span className="mono">?role=admin</span> in the template.</p></GlassCard>
  }
  return (
    <div className="space-y-6">
      <h1 className="text-3xl">Admin</h1>
      <div className="flex flex-wrap gap-2" role="tablist">
        {tabs.map((t) => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} className={`btn btn-secondary !px-4 !py-2 ${tab === t ? '!border-[var(--earth)]' : ''}`}>{t}</button>)}
      </div>
      <GlassCard title={tab}>
        {tab === 'Data imports' && <Imports />}
        {tab === 'Datasets' && <Datasets />}
        {tab === 'Candidate sites' && <Sites />}
        {tab === 'Calculation settings' && <Settings />}
      </GlassCard>
    </div>
  )
}
