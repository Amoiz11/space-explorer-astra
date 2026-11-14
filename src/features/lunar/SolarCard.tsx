import type { Site, SiteResult } from '../../types'
import type { Analysis } from '../../store/lunar'
import { estimateSolar } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDateTime } from '../../utils/format'
import { useUI } from '../../store/ui'
import CountUp from '../../components/CountUp'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import Skeleton from '../../components/Skeleton'
import SiteChip from '../../components/SiteChip'

type Props = { results: SiteResult[]; sites: Site[]; analysis: Analysis }

export default function SolarCard({ results, sites, analysis }: Props) {
  const openDrawer = useUI((u) => u.openDrawer)
  const area = Number(analysis.panel.areaM2)
  const eff = Number(analysis.panel.efficiencyPct)
  const hasInputs = area > 0 && eff > 0
  const tilt = analysis.panel.orientation === 'tilted' ? Number(analysis.panel.tiltDeg) || 0 : 0

  const est = useAsync(async () => {
    if (!hasInputs) return null
    return Promise.all(
      results.map(async (r) => ({
        siteId: r.siteId,
        est: await estimateSolar(r.siteId, { panel_area_m2: area, efficiency: eff / 100, tilt_deg: tilt, start: analysis.start, end: analysis.end }),
      })),
    )
  }, [analysis.nonce])

  return (
    <GlassCard id="solar" title="Solar estimate">
      {!hasInputs ? (
        <p className="text-[var(--text-2)]">Illumination opportunity only. Add panel inputs for an energy estimate.</p>
      ) : est.loading ? (
        <Skeleton className="h-32" />
      ) : est.error ? (
        <ErrorState message={est.error.message} onRetry={est.retry} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {est.data?.map(({ siteId, est: e }) => {
            const idx = sites.findIndex((s) => s.id === siteId)
            return (
              <div key={siteId} className="rounded-[14px] border border-[var(--border)] bg-black/20 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? siteId}</h3>
                  <div className="flex items-center gap-2">
                    <MethodChip method={e.label} />
                    <button type="button" onClick={() => openDrawer(`result:${siteId}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
                  </div>
                </div>
                <p className="mono text-3xl font-semibold text-[var(--sun)]"><CountUp value={e.energy} /> <span className="text-sm font-normal text-[var(--text-2)]">{e.units}</span></p>
                <p className="mt-1 text-xs text-[var(--text-2)]">Estimated energy. Sunlight is not guaranteed electrical power.</p>
                <h4 className="mt-4 text-xs text-[var(--text-2)]">Assumptions</h4>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">{e.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
                <h4 className="mt-4 text-xs text-[var(--text-2)]">Shadow periods ({e.shadow_periods.length})</h4>
                <ul className="mono mt-1 max-h-24 space-y-0.5 overflow-auto text-xs">
                  {e.shadow_periods.slice(0, 8).map((p) => <li key={p.start}>{formatDateTime(p.start)} to {formatDateTime(p.end)}</li>)}
                  {!e.shadow_periods.length && <li className="text-[var(--text-2)]">None in this period</li>}
                </ul>
                <p className="mt-4 text-xs text-[var(--text-2)]">Uncertainty: {e.uncertainty}</p>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}
