import { useState } from 'react'
import type { Site } from '../../types'
import { getSites } from '../../services'
import { useLunarStore } from '../../store/lunar'
import { useAsync } from '../../utils/useAsync'
import { SITE_TAGLINE } from '../../config/site'
import Chip from '../../components/Chip'
import Disclaimer from '../../components/Disclaimer'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import PageHeader from '../../components/PageHeader'
import Skeleton from '../../components/Skeleton'
import Controls from './Controls'
import LunarResults from './LunarResults'
import { useLunarData } from './useLunarData'

export default function LunarPage() {
  const sites = useAsync<Site[]>(getSites, [])
  const analysis = useLunarStore((s) => s.analysis)
  const results = useLunarData(analysis)
  const [sheetOpen, setSheetOpen] = useState(false)

  const onAnalyse = () => {
    setSheetOpen(false)
    setTimeout(() => document.getElementById('lunar-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  const isPlaceholder = sites.data?.length ? sites.data.some((s) => s.is_placeholder) : false

  return (
    <div>
      <PageHeader
        title="Lunar Landing Navigator"
        subtitle={SITE_TAGLINE}
        chip={isPlaceholder ? <Chip label="Placeholder data" color="var(--est)" /> : undefined}
        actions={<a href="/lunar/compare" className="btn btn-secondary">Compare sites and dates</a>}
      />

      <div className="lg:grid lg:grid-cols-[320px_1fr] lg:items-start lg:gap-6">
        <div
          className={`fixed inset-x-0 bottom-0 z-40 max-h-[80vh] overflow-y-auto rounded-t-2xl border-t border-[var(--border)] bg-[var(--bg-1)] p-3 transition-transform duration-200 ${
            sheetOpen ? 'translate-y-0' : 'translate-y-full'
          } lg:sticky lg:top-24 lg:z-auto lg:max-h-[calc(100vh-7rem)] lg:translate-y-0 lg:rounded-none lg:border-0 lg:bg-transparent lg:p-0`}
        >
          <div className="mb-2 flex items-center justify-between px-1 lg:hidden">
            <span className="text-sm text-[var(--text-2)]">Controls</span>
            <button type="button" onClick={() => setSheetOpen(false)} className="text-sm text-[var(--earth)]">Close</button>
          </div>
          <Controls sites={sites.data} loading={sites.loading} error={sites.error} onRetry={sites.retry} onAnalyse={onAnalyse} />
        </div>

        <button type="button" onClick={() => setSheetOpen(true)} className="btn btn-primary fixed bottom-4 right-4 z-30 rounded-full shadow-lg lg:hidden">
          Controls
        </button>

        <div id="lunar-results" className="scroll-mt-24 space-y-6 pt-6 lg:pt-0">
          {!analysis ? (
            <>
              <EmptyState text="Pick a site and a date to begin." />
              <Disclaimer />
            </>
          ) : results.loading ? (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-56" /><Skeleton className="h-56" /></div>
              <Skeleton className="h-80" />
            </div>
          ) : results.error ? (
            <ErrorState message={results.error.message} onRetry={results.retry} />
          ) : results.data ? (
            <LunarResults results={results.data} sites={sites.data ?? []} analysis={analysis} />
          ) : null}
        </div>
      </div>
    </div>
  )
}
