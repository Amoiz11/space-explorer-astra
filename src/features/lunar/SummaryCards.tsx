import type { Site, SiteResult } from '../../types'
import { useUI } from '../../store/ui'
import { maxElevation } from '../../utils/sites'
import CountUp from '../../components/CountUp'
import MethodChip from '../../components/MethodChip'
import SiteChip from '../../components/SiteChip'
import TiltCard from '../../components/TiltCard'

type MetricProps = { label: string; value: number | null; unit: string; color: string; sub?: string }

function Metric({ label, value, unit, color, sub }: MetricProps) {
  return (
    <div>
      <p className="text-xs text-[var(--text-2)]">{label}</p>
      <p className="mono mt-1 text-3xl font-semibold" style={{ color }}>
        {value === null ? <span className="text-base text-[var(--text-2)]">Unknown</span> : (
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
        const sun = r.windows.illumination.total_sunlit_h
        const earth = r.windows.earth_visibility.total_visible_h
        const range = days > 1
        return (
          <TiltCard key={r.siteId} className="p-5" glow>
            <div className="mb-5 flex items-center justify-between gap-2">
              <h3 className="flex items-center gap-2 text-[16px]"><SiteChip index={Math.max(idx, 0)} />{name}</h3>
              <div className="flex items-center gap-2">
                <MethodChip method={r.windows.label} />
                <button type="button" onClick={() => openDrawer(`result:${r.siteId}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-5">
              <Metric label={range ? 'Total sunlit hours' : 'Sunlit hours'} value={sun} unit="h" color="var(--sun)" sub={range ? `${(sun / days).toFixed(1)} h per day on average` : undefined} />
              <Metric label={range ? 'Total Earth visible hours' : 'Earth visible hours'} value={earth} unit="h" color="var(--earth)" sub={range ? `${(earth / days).toFixed(1)} h per day on average` : undefined} />
              <Metric label="Maximum Sun elevation" value={maxElevation(r.sunEarth.samples, 'sun')} unit="°" color="var(--sun)" />
              <Metric label="Maximum Earth elevation" value={maxElevation(r.sunEarth.samples, 'earth')} unit="°" color="var(--earth)" />
            </div>
          </TiltCard>
        )
      })}
    </div>
  )
}
