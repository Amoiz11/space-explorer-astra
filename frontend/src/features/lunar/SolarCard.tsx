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
  const panelAzimuth = Number(analysis.panel.panelAzimuthDeg) || 0
  const trackSun = Boolean(analysis.panel.trackSunAzimuth)
  const obsHeight = analysis.observerHeightM || 0

  const est = useAsync(async () => {
    return Promise.all(
      results.map(async (r) => ({
        siteId: r.siteId,
        est: await estimateSolar(r.siteId, {
          panel_area_m2: hasInputs ? area : 0,
          efficiency: hasInputs ? eff / 100 : 0,
          tilt_deg: tilt,
          panel_azimuth_deg: panelAzimuth,
          track_sun_azimuth: trackSun,
          observer_height_m: obsHeight,
          start: analysis.start,
          end: analysis.end,
        }),
      })),
    )
  }, [
    analysis.nonce,
    hasInputs,
    area,
    eff,
    tilt,
    panelAzimuth,
    trackSun,
    obsHeight,
    analysis.start,
    analysis.end,
  ])

  return (
    <GlassCard id="solar" title="Solar estimate & Illumination opportunity">
      {!hasInputs && (
        <div className="mb-4 rounded-[10px] border border-blue-500/30 bg-blue-500/10 p-3 text-xs text-blue-200">
          ℹ️ <strong>Illumination opportunity only:</strong> Panel inputs (area, efficiency, tilt) are not configured. Power generation is not computed (LL-26). Showing solar illumination opportunity from the 240 m DEM and DE421 ephemeris.
        </div>
      )}

      {est.loading ? (
        <Skeleton className="h-48" />
      ) : est.error ? (
        <ErrorState message={est.error.message} onRetry={est.retry} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {est.data?.map(({ siteId, est: e }) => {
            const idx = sites.findIndex((s) => s.id === siteId)
            const siteName = sites[idx]?.name ?? siteId
            const opp = e.illumination_opportunity

            return (
              <div key={siteId} className="rounded-[14px] border border-[var(--border)] bg-black/20 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{siteName}</h3>
                  <div className="flex items-center gap-2">
                    <MethodChip method={e.label} />
                    <button type="button" onClick={() => openDrawer(`result:${siteId}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
                  </div>
                </div>

                {hasInputs ? (
                  <div>
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="mono text-3xl font-semibold text-[var(--sun)]">
                        {e.energy_kwh !== null && e.energy_kwh !== undefined ? (
                          <span><CountUp value={e.energy_kwh} /> <span className="text-sm font-normal text-[var(--text-2)]">kWh</span></span>
                        ) : (
                          <span><CountUp value={e.energy} /> <span className="text-sm font-normal text-[var(--text-2)]">{e.units}</span></span>
                        )}
                      </span>
                      {e.energy_kwh !== null && e.energy_kwh !== undefined && (
                        <span className="mono text-xs text-[var(--text-2)]">({e.energy.toFixed(1)} Wh)</span>
                      )}
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">Mean power:</span>{' '}
                        <span className="mono text-[var(--text-1)]">{e.mean_power_w !== null && e.mean_power_w !== undefined ? `${e.mean_power_w.toFixed(1)} W` : 'Unknown'}</span>
                      </div>
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">Peak power:</span>{' '}
                        <span className="mono text-[var(--text-1)]">{e.peak_power_w !== null && e.peak_power_w !== undefined ? `${e.peak_power_w.toFixed(1)} W` : 'Unknown'}</span>
                      </div>
                    </div>

                    {e.per_day_energy && e.per_day_energy.length > 0 && (
                      <div className="mt-3">
                        <h4 className="text-xs text-[var(--text-2)]">Daily energy breakdown</h4>
                        <div className="mt-1 max-h-32 overflow-auto rounded-[8px] border border-[var(--border)] bg-black/30 p-2">
                          <table className="w-full text-left text-xs">
                            <thead>
                              <tr className="border-b border-[var(--border)] text-[var(--text-2)]">
                                <th className="py-1">Date</th>
                                <th className="text-right">Energy (kWh)</th>
                                <th className="text-right">Peak (W)</th>
                                <th className="text-right">Mean (W)</th>
                              </tr>
                            </thead>
                            <tbody>
                              {e.per_day_energy.map((d) => (
                                <tr key={d.date} className="mono border-b border-[var(--border)]/40 last:border-0">
                                  <td className="py-1">{d.date}</td>
                                  <td className="text-right text-[var(--sun)]">{d.energy_kwh?.toFixed(3) ?? (d.energy_wh / 1000).toFixed(3)}</td>
                                  <td className="text-right">{d.peak_power_w?.toFixed(1) ?? '—'}</td>
                                  <td className="text-right">{d.mean_power_w?.toFixed(1) ?? '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ) : opp ? (
                  <div>
                    <h4 className="text-xs font-medium text-[var(--text-2)]">Illumination opportunity:</h4>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">Any part lit:</span>{' '}
                        <span className="mono text-[var(--sun)] font-medium">{opp.hours_any_part_lit.toFixed(1)} h</span>
                      </div>
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">Fully lit:</span>{' '}
                        <span className="mono text-[var(--sun)] font-medium">{opp.hours_fully_lit.toFixed(1)} h</span>
                      </div>
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">In shadow:</span>{' '}
                        <span className="mono text-[var(--text-1)]">{opp.hours_shadow.toFixed(1)} h</span>
                      </div>
                      <div className="rounded-[8px] bg-white/5 p-2">
                        <span className="text-[var(--text-2)]">Lit fraction:</span>{' '}
                        <span className="mono text-[var(--text-1)]">{Math.round(opp.fraction_of_period * 100)}%</span>
                      </div>
                    </div>
                  </div>
                ) : null}

                <h4 className="mt-4 text-xs text-[var(--text-2)]">Shadow periods ({e.shadow_periods.length})</h4>
                <ul className="mono mt-1 max-h-24 space-y-0.5 overflow-auto text-xs">
                  {e.shadow_periods.slice(0, 8).map((p, i) => (
                    <li key={`${p.start}-${i}`}>
                      {formatDateTime(p.start)} to {formatDateTime(p.end)}
                      {p.duration_hours !== undefined && (
                        <span className="text-[var(--text-2)]"> ({p.duration_hours.toFixed(1)} h)</span>
                      )}
                    </li>
                  ))}
                  {!e.shadow_periods.length && <li className="text-[var(--text-2)]">None in this period</li>}
                </ul>

                <h4 className="mt-4 text-xs text-[var(--text-2)]">Assumptions</h4>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs text-[var(--text-2)]">
                  {e.assumptions.map((a) => <li key={a}>{a}</li>)}
                </ul>

                <p className="mt-3 text-xs text-[var(--text-2)]">Uncertainty: {e.uncertainty}</p>
                <p className="mt-2 text-xs italic text-[var(--text-2)]">
                  Disclaimers: Sunlight is not guaranteed electrical power. Planning support tool, not safety certification.
                </p>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}
