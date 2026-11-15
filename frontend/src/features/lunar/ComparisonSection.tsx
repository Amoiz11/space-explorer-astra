import { useState } from 'react'
import { ArrowDownUp, Download, Plus } from 'lucide-react'
import type { CompareRow, Site, SolarInputs } from '../../types'
import { compareSites, getComparisonExportUrl, type CompareSiteWindow } from '../../services'
import { useLunarStore } from '../../store/lunar'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import SiteChip from '../../components/SiteChip'
import Skeleton from '../../components/Skeleton'

type Props = { siteIds: string[]; sites: Site[]; initialDate: string; standalone?: boolean }
type Key = 'name' | 'date' | 'days' | 'mean_slope' | 'mean_elevation_m' | 'sunlit_h' | 'earth_visible_h' | 'hours_both_up' | 'quality'

const qualityColor = { good: 'var(--ok)', fair: 'var(--text-1)', limited: 'var(--unknown)' }
const qualityLabel = { good: 'Good', fair: 'Fair', limited: 'Limited' }

export default function ComparisonSection({ siteIds, sites, initialDate, standalone }: Props) {
  const [windows, setWindows] = useState<CompareSiteWindow[]>([{ start: initialDate, days: 1 }])
  const [newDate, setNewDate] = useState(initialDate)
  const [newDays, setNewDays] = useState(1)
  const [sort, setSort] = useState<{ key: Key; dir: 1 | -1 } | null>(null)
  const openDrawer = useUI((u) => u.openDrawer)

  const obsHeight = useLunarStore((s) => s.analysis?.observerHeightM ?? s.observerHeightM) || 0
  const panelInputs = useLunarStore((s) => s.analysis?.panel ?? s.panelInputs)

  const solarPayload: SolarInputs | undefined =
    panelInputs && Number(panelInputs.areaM2) > 0
      ? {
          panel_area_m2: Number(panelInputs.areaM2),
          efficiency: (Number(panelInputs.efficiencyPct) || 20) / 100,
          tilt_deg: Number(panelInputs.tiltDeg) || 0,
          panel_azimuth_deg: Number(panelInputs.panelAzimuthDeg) || 0,
          track_sun_azimuth: Boolean(panelInputs.trackSunAzimuth),
          observer_height_m: obsHeight,
          start: initialDate,
          end: initialDate,
        }
      : undefined

  const cmp = useAsync(
    () => compareSites(siteIds, windows, obsHeight, solarPayload),
    [
      siteIds.join(','),
      JSON.stringify(windows),
      obsHeight,
      JSON.stringify(solarPayload),
    ],
  )

  const nameOf = (id: string) => sites.find((s) => s.id === id)?.name ?? id
  const idxOf = (id: string) => Math.max(sites.findIndex((s) => s.id === id), 0)
  const rows: CompareRow[] = cmp.data?.rows ?? []
  const hasMultipleRows = rows.length >= 2

  const sorted = [...rows].sort((a, b) => {
    if (!sort) return 0
    const get = (r: CompareRow) => (sort.key === 'name' ? nameOf(r.site_id) : r[sort.key as keyof CompareRow])
    const x = get(a), y = get(b)
    if (x == null) return 1
    if (y == null) return -1
    return (x < y ? -1 : x > y ? 1 : 0) * sort.dir
  })

  const th = (key: Key, label: string) => (
    <th className="py-2 pr-4 font-normal">
      <button
        type="button"
        className="inline-flex items-center gap-1 hover:text-white"
        onClick={() => setSort((s) => ({ key, dir: s?.key === key && s.dir === 1 ? -1 : 1 }))}
      >
        {label}
        <ArrowDownUp size={12} />
      </button>
    </th>
  )

  const hi = (on: boolean) => (on ? 'bg-white/[0.07] rounded-md px-1 py-0.5' : '')

  const addWindow = () => {
    if (!newDate) return
    const exists = windows.some((w) => w.start === newDate && w.days === newDays)
    if (exists || windows.length >= 6) return
    setWindows((prev) => [...prev, { start: newDate, days: newDays }])
  }

  const exportUrl = (format: 'json' | 'csv') => {
    if (cmp.data?.id) {
      window.open(getComparisonExportUrl(cmp.data.id, format), '_blank')
    } else {
      const blob = new Blob([JSON.stringify(cmp.data, null, 2)], { type: 'application/json' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `comparison.${format}`
      a.click()
      URL.revokeObjectURL(a.href)
    }
  }

  return (
    <GlassCard id="compare" title="Site and date comparison">
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor={`cmp-date-${standalone ? 's' : 'p'}`} className="mb-1 block text-xs text-[var(--text-2)]">
            Window start (UTC)
          </label>
          <input
            id={`cmp-date-${standalone ? 's' : 'p'}`}
            type="date"
            className="field"
            value={newDate}
            onChange={(e) => setNewDate(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor={`cmp-days-${standalone ? 's' : 'p'}`} className="mb-1 block text-xs text-[var(--text-2)]">
            Window duration (days)
          </label>
          <select
            id={`cmp-days-${standalone ? 's' : 'p'}`}
            className="field !w-auto"
            value={newDays}
            onChange={(e) => setNewDays(Number(e.target.value))}
          >
            <option value={1}>1 day (24h)</option>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={28}>28 days (lunar day)</option>
          </select>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={!newDate || windows.length >= 6}
          onClick={addWindow}
        >
          <Plus size={14} /> Add window
        </button>
        {windows.length > 1 && (
          <button
            type="button"
            className="btn text-[var(--text-2)] hover:text-white"
            onClick={() => setWindows([{ start: initialDate, days: 1 }])}
          >
            Reset windows
          </button>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            className="btn btn-secondary !px-2.5 !py-1.5 text-xs"
            disabled={!rows.length}
            onClick={() => exportUrl('json')}
          >
            <Download size={13} /> JSON
          </button>
          <button
            type="button"
            className="btn btn-secondary !px-2.5 !py-1.5 text-xs"
            disabled={!rows.length}
            onClick={() => exportUrl('csv')}
          >
            <Download size={13} /> CSV
          </button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2 text-xs text-[var(--text-2)]">
        <span>Active windows:</span>
        {windows.map((w, i) => (
          <span key={`${w.start}-${w.days}-${i}`} className="mono rounded-[6px] border border-[var(--border)] bg-white/5 px-2 py-0.5">
            {w.start} ({w.days}d)
          </span>
        ))}
      </div>

      {!siteIds.length ? (
        <p className="text-[var(--text-2)]">Choose at least one site to compare.</p>
      ) : cmp.loading ? (
        <Skeleton className="h-48" />
      ) : cmp.error ? (
        <ErrorState message={cmp.error.message} onRetry={cmp.retry} />
      ) : !rows.length ? (
        <p className="text-[var(--text-2)]">No comparison data returned from backend.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-xs text-[var(--text-2)]">
                {th('name', 'Site')}
                {th('date', 'Window')}
                {th('mean_slope', 'Mean slope (deg)')}
                {th('mean_elevation_m', 'Elevation (m)')}
                {th('sunlit_h', 'Sunlit hours')}
                {th('earth_visible_h', 'Earth visible hours')}
                {th('hours_both_up', 'Overlap (both up)')}
                {th('quality', 'Data quality')}
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => {
                const rowKey = `${r.site_id}:${r.date}`
                const isBestSun = hasMultipleRows && r.sunlit_h > 0 && cmp.data?.best_by?.best_for_sunlight === rowKey
                const isBestEarth = hasMultipleRows && r.earth_visible_h > 0 && cmp.data?.best_by?.best_for_earth_visibility === rowKey
                const isLowestSlope = hasMultipleRows && r.mean_slope > 0 && cmp.data?.best_by?.lowest_slope === rowKey
                const isMostBothUp = hasMultipleRows && r.hours_both_up > 0 && cmp.data?.best_by?.most_hours_both_up === rowKey

                return (
                  <tr key={`${r.site_id}-${r.date}-${r.days}`} className="border-b border-[var(--border)]/60 last:border-0">
                    <td className="py-3 pr-4">
                      <button
                        type="button"
                        className="flex items-center gap-2 hover:underline"
                        onClick={() => openDrawer(`result:${r.site_id}`)}
                      >
                        <SiteChip index={idxOf(r.site_id)} />
                        {nameOf(r.site_id)}
                      </button>
                    </td>
                    <td className="mono pr-4 text-xs">
                      {formatDate(r.date)} ({r.days}d)
                    </td>
                    <td className="pr-4">
                      <div className={`mono inline-block ${hi(isLowestSlope)}`}>
                        {r.mean_slope != null ? `${r.mean_slope.toFixed(2)}°` : 'Unknown'}
                        {isLowestSlope && (
                          <span className="ml-2 rounded bg-emerald-500/20 px-1 py-0.5 font-[family-name:var(--font-body)] text-[10px] text-emerald-300">
                            Lowest slope
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="mono pr-4">
                      {r.mean_elevation_m != null ? `${r.mean_elevation_m.toFixed(1)} m` : 'Unknown'}
                    </td>
                    <td className="pr-4">
                      <div className={`mono inline-block text-[var(--sun)] ${hi(isBestSun)}`}>
                        {r.sunlit_h != null ? `${r.sunlit_h.toFixed(1)} h` : 'No data'}
                        {isBestSun && (
                          <span className="ml-2 rounded bg-amber-500/20 px-1 py-0.5 font-[family-name:var(--font-body)] text-[10px] text-amber-200">
                            Best for sunlight
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="pr-4">
                      <div className={`mono inline-block text-[var(--earth)] ${hi(isBestEarth)}`}>
                        {r.earth_visible_h != null ? `${r.earth_visible_h.toFixed(1)} h` : 'No data'}
                        {isBestEarth && (
                          <span className="ml-2 rounded bg-blue-500/20 px-1 py-0.5 font-[family-name:var(--font-body)] text-[10px] text-blue-200">
                            Best for Earth
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="pr-4">
                      <div className={`mono inline-block ${hi(isMostBothUp)}`}>
                        {r.hours_both_up != null ? `${r.hours_both_up.toFixed(1)} h` : 'Unknown'}
                        {isMostBothUp && (
                          <span className="ml-2 rounded bg-purple-500/20 px-1 py-0.5 font-[family-name:var(--font-body)] text-[10px] text-purple-200">
                            Most overlap
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <Chip label={qualityLabel[r.quality]} color={qualityColor[r.quality]} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {Boolean(cmp.data?.criteria_list && cmp.data.criteria_list.length > 0) && (
        <div className="mt-4 rounded-[10px] border border-[var(--border)] bg-black/20 p-3">
          <h4 className="text-xs font-medium text-[var(--text-1)]">Evaluation criteria & Thresholds</h4>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {cmp.data?.criteria_list?.map((c) => (
              <div key={c.metric} className="flex items-center justify-between rounded bg-white/5 px-2.5 py-1.5 text-xs">
                <span>{c.label}</span>
                <span className="mono text-[var(--text-2)]">Threshold: {c.threshold}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {cmp.data?.disclaimers && cmp.data.disclaimers.length > 0 && (
        <ul className="mt-4 list-disc space-y-0.5 pl-5 text-xs text-[var(--text-2)]">
          {cmp.data.disclaimers.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      )}

      <p className="mt-3 text-xs text-[var(--text-2)]">
        Best values are highlighted for planning comparison only when at least two rows are evaluated. This tool does not certify any site as safe.
      </p>
    </GlassCard>
  )
}
