import { useState } from 'react'
import { ArrowDownUp, Download, Plus } from 'lucide-react'
import type { CompareRow, Site } from '../../types'
import { compareSites } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import SiteChip from '../../components/SiteChip'
import Skeleton from '../../components/Skeleton'

type Props = { siteIds: string[]; sites: Site[]; initialDate: string; standalone?: boolean }
type Key = 'name' | 'date' | 'mean_slope' | 'mean_elevation_m' | 'sunlit_h' | 'earth_visible_h' | 'solar_opportunity' | 'quality'

const qualityColor = { good: 'var(--ok)', fair: 'var(--text-1)', limited: 'var(--unknown)' }
const qualityLabel = { good: 'Good', fair: 'Fair', limited: 'Limited' }

export default function ComparisonSection({ siteIds, sites, initialDate, standalone }: Props) {
  const [dates, setDates] = useState<string[]>([initialDate])
  const [newDate, setNewDate] = useState(initialDate)
  const [sort, setSort] = useState<{ key: Key; dir: 1 | -1 } | null>(null)
  const openDrawer = useUI((u) => u.openDrawer)
  const cmp = useAsync(() => compareSites(siteIds, dates), [siteIds.join(','), dates.join(',')])

  const nameOf = (id: string) => sites.find((s) => s.id === id)?.name ?? id
  const idxOf = (id: string) => Math.max(sites.findIndex((s) => s.id === id), 0)
  const rows: CompareRow[] = cmp.data?.rows ?? []

  const best = (k: 'sunlit_h' | 'earth_visible_h' | 'solar_opportunity' | 'mean_slope') => {
    if (!rows.length) return null
    const f = k === 'mean_slope' ? Math.min : Math.max
    return f(...rows.map((r) => r[k]))
  }
  const bSun = best('sunlit_h'), bEarth = best('earth_visible_h'), bSolar = best('solar_opportunity'), bSlope = best('mean_slope')

  const sorted = [...rows].sort((a, b) => {
    if (!sort) return 0
    const get = (r: CompareRow) => (sort.key === 'name' ? nameOf(r.site_id) : r[sort.key as keyof CompareRow])
    const x = get(a), y = get(b)
    return (x < y ? -1 : x > y ? 1 : 0) * sort.dir
  })

  const th = (key: Key, label: string) => (
    <th className="py-2 pr-4 font-normal">
      <button type="button" className="inline-flex items-center gap-1 hover:text-white" onClick={() => setSort((s) => ({ key, dir: s?.key === key && s.dir === 1 ? -1 : 1 }))}>
        {label}<ArrowDownUp size={12} />
      </button>
    </th>
  )
  const hi = (on: boolean) => (on ? 'bg-white/[0.07] rounded-md' : '')

  const exportJson = () => {
    const blob = new Blob([JSON.stringify({ site_ids: siteIds, dates, criteria: cmp.data?.criteria ?? {}, settings: cmp.data?.settings ?? {} }, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'comparison-criteria.json'
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <GlassCard id="compare" title="Site and date comparison">
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor={`cmp-date-${standalone ? 's' : 'p'}`} className="mb-1 block text-xs text-[var(--text-2)]">Add another date (UTC)</label>
          <input id={`cmp-date-${standalone ? 's' : 'p'}`} type="date" className="field" value={newDate} onChange={(e) => setNewDate(e.target.value)} />
        </div>
        <button type="button" className="btn btn-secondary" disabled={!newDate || dates.includes(newDate) || dates.length >= 4}
          onClick={() => setDates((d) => [...d, newDate])}><Plus size={14} /> Add date</button>
        <button type="button" className="btn btn-secondary" onClick={exportJson}><Download size={14} /> Export criteria and settings (JSON)</button>
        {dates.length > 1 && <button type="button" className="btn text-[var(--text-2)]" onClick={() => setDates([initialDate])}>Reset dates</button>}
      </div>

      {!siteIds.length ? <p className="text-[var(--text-2)]">Choose at least one site to compare.</p>
        : cmp.loading ? <Skeleton className="h-48" />
        : cmp.error ? <ErrorState message={cmp.error.message} onRetry={cmp.retry} />
        : !rows.length ? <p className="text-[var(--text-2)]">Data not available.</p> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-xs text-[var(--text-2)]">
                {th('name', 'Site')}{th('date', 'Date')}{th('mean_slope', 'Mean slope (deg)')}{th('mean_elevation_m', 'Elevation (m)')}
                {th('sunlit_h', 'Sunlit hours')}{th('earth_visible_h', 'Earth visible hours')}{th('solar_opportunity', 'Solar opportunity')}{th('quality', 'Data quality')}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => (
                <tr key={`${r.site_id}-${r.date}`} className="border-b border-[var(--border)]/60 last:border-0">
                  <td className="py-3 pr-4"><button type="button" className="flex items-center gap-2 hover:underline" onClick={() => openDrawer(`result:${r.site_id}`)}><SiteChip index={idxOf(r.site_id)} />{nameOf(r.site_id)}</button></td>
                  <td className="mono pr-4">{formatDate(r.date)}</td>
                  <td className="pr-4"><div className={`mono inline-block px-1.5 ${hi(r.mean_slope === bSlope)}`}>{r.mean_slope}{r.mean_slope === bSlope && <span className="ml-2 font-[family-name:var(--font-body)] text-[11px] text-[var(--text-2)]">Lowest slope</span>}</div></td>
                  <td className="mono pr-4">{r.mean_elevation_m}</td>
                  <td className="pr-4"><div className={`mono inline-block px-1.5 text-[var(--sun)] ${hi(r.sunlit_h === bSun)}`}>{r.sunlit_h} h{r.sunlit_h === bSun && <span className="ml-2 font-[family-name:var(--font-body)] text-[11px] text-[var(--text-1)]">Best for sunlight</span>}</div></td>
                  <td className="pr-4"><div className={`mono inline-block px-1.5 text-[var(--earth)] ${hi(r.earth_visible_h === bEarth)}`}>{r.earth_visible_h} h{r.earth_visible_h === bEarth && <span className="ml-2 font-[family-name:var(--font-body)] text-[11px] text-[var(--text-1)]">Best for Earth visibility</span>}</div></td>
                  <td className="pr-4"><div className={`mono inline-block px-1.5 ${hi(r.solar_opportunity === bSolar)}`}>{Math.round(r.solar_opportunity * 100)} %</div></td>
                  <td><Chip label={qualityLabel[r.quality]} color={qualityColor[r.quality]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="mt-4 text-xs text-[var(--text-2)]">Best values are highlighted for planning comparison only. This tool does not certify any site as safe.</p>
    </GlassCard>
  )
}
