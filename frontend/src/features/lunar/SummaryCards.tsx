import type { Site, SiteResult } from '../../types'
import { useUI } from '../../store/ui'
import { maxElevation } from '../../utils/sites'
import CountUp from '../../components/CountUp'
import MethodChip from '../../components/MethodChip'
import SiteChip from '../../components/SiteChip'
import TiltCard from '../../components/TiltCard'

type MetricProps = { label: string; value: number | null; unit: string; color: string; sub?: string; emptyText?: string }

function Metric({ label, value, unit, color, sub, emptyText }: MetricProps) {
  return (
    <div>
      <p className="text-xs text-[var(--text-2)]">{label}</p>
      <p className="mono mt-1 text-3xl font-semibold" style={{ color }}>
        {value === null ? (
          <span className="text-sm font-normal text-[var(--text-2)]">{emptyText ?? 'Unknown'}</span>
        ) : (
          <><CountUp value={value} decimals={1} /><span className="ml-1 text-sm font-normal text-[var(--text-2)]">{unit}</span></>
        )}
      </p>
      {sub && <p className="mt-0.5 text-xs text-[var(--text-2)]">{sub}</p>}
    </div>
  )
}

type Props = { results: SiteResult[]; sites: Site[]; days: number }

export default function SummaryCards({ results, sites, days }: Props) {
  const openDrawer = useUI((s) => s.openDrawer)
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {results.map((r) => {
        const idx = sites.findIndex((s) => s.id === r.siteId)
        const name = sites[idx]?.name ?? r.siteId
        const hasSeries = r.sunEarth.samples.length > 0
        const sunAny = hasSeries ? r.windows.illumination.hours_any_part_lit : null
        const sunFull = hasSeries ? r.windows.illumination.hours_fully_lit : null
        const earth = hasSeries ? r.windows.earth_visibility.total_visible_h : null
        const range = days > 1
        const maxSun = maxElevation(r.sunEarth.samples, 'sun')
        const maxEarth = maxElevation(r.sunEarth.samples, 'earth')
        const sunSub = !hasSeries
          ? undefined
          : maxSun !== null && maxSun <= 0
          ? 'Sun stays below the horizon on this day'
          : range && sunAny !== null
          ? `${(sunAny / days).toFixed(1)} h per day on avg`
          : undefined
        const earthSub = !hasSeries
          ? undefined
          : maxEarth !== null && maxEarth <= 0
          ? 'Earth stays below the horizon on this day'
          : range && earth !== null
          ? `${(earth / days).toFixed(1)} h per day on avg`
          : undefined

        return (
          <TiltCard key={r.siteId} className="p-5" glow>
            <div className="mb-5 flex items-center justify-between gap-2">
              <h3 className="flex items-center gap-2 text-[16px]"><SiteChip index={Math.max(idx, 0)} />{name}</h3>
              <div className="flex items-center gap-2">
                <MethodChip method={r.windows.label} />
                <button type="button" onClick={() => openDrawer(`result:${r.siteId}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Metric
                label={range ? 'Total any-part-lit hours' : 'Any-part-lit hours'}
                value={sunAny}
                unit="h"
                color="var(--sun)"
                sub={sunSub}
                emptyText="No data returned"
              />
              <Metric
                label={range ? 'Total fully-lit hours' : 'Fully-lit hours'}
                value={sunFull}
                unit="h"
                color="var(--sun)"
                sub={sunFull !== null ? `Illuminated fraction: ${Math.round(r.windows.illumination.illuminated_fraction * 100)}%` : undefined}
                emptyText="No data returned"
              />
              <Metric
                label={range ? 'Total Earth visible hours' : 'Earth visible hours'}
                value={earth}
                unit="h"
                color="var(--earth)"
                sub={earthSub}
                emptyText="No data returned"
              />
              <Metric
                label="Direct-to-Earth status"
                value={null}
                unit=""
                color="var(--earth)"
                emptyText={
                  !hasSeries
                    ? 'No data returned'
                    : r.windows.earth_visibility.total_visible_h > 0
                    ? `Clear (${r.windows.earth_visibility.total_visible_h.toFixed(1)}h)`
                    : r.windows.earth_visibility.blocked_by_terrain_hours > 0
                    ? 'Blocked by terrain'
                    : 'Below horizon'
                }
                sub="Relay comms not modelled"
              />
              <Metric
                label="Maximum Sun elevation"
                value={maxSun}
                unit="°"
                color="var(--sun)"
                emptyText="No data returned"
              />
              <Metric
                label="Maximum Earth elevation"
                value={maxEarth}
                unit="°"
                color="var(--earth)"
                emptyText="No data returned"
              />
            </div>
          </TiltCard>
        )
      })}
    </div>
  )
}
