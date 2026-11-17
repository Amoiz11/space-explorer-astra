import { useState } from 'react'
import { getSites } from '../../services'
import { useAsync } from '../../utils/useAsync'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHeader from '../../components/PageHeader'
import SiteChip from '../../components/SiteChip'
import Skeleton from '../../components/Skeleton'
import ComparisonSection from './ComparisonSection'

export default function LunarComparePage() {
  const sites = useAsync(getSites, [])
  const [picked, setPicked] = useState<string[]>(['site-shackleton-01', 'site-connecting-ridge-02'])
  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : p.length < 5 ? [...p, id] : p))
  const isPlaceholder = sites.data?.length ? sites.data.some((s) => s.is_placeholder) : false

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compare sites and dates"
        subtitle="See which site has more sunlight and more Earth visibility."
        chip={isPlaceholder ? <Chip label="Placeholder data" color="var(--est)" /> : undefined}
      />
      {sites.loading ? <Skeleton className="h-24" /> : sites.error ? <ErrorState message={sites.error.message} onRetry={sites.retry} /> : (
        <GlassCard title="Sites">
          <div className="flex flex-wrap gap-2">
            {(sites.data ?? []).map((s, i) => (
              <label key={s.id} className={`btn btn-secondary cursor-pointer !px-3 !py-2 ${picked.includes(s.id) ? '!border-[var(--earth)]' : ''}`}>
                <input type="checkbox" className="sr-only" checked={picked.includes(s.id)} onChange={() => toggle(s.id)} />
                <SiteChip index={i} />{s.name}
              </label>
            ))}
          </div>
        </GlassCard>
      )}
      <ComparisonSection key={picked.join(',')} siteIds={picked} sites={sites.data ?? []} initialDate="2026-12-25" standalone />
    </div>
  )
}
