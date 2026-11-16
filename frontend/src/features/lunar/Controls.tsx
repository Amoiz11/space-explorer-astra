import type { Site } from '../../types'
import { useLunarStore, type PanelInputs } from '../../store/lunar'
import { useUI } from '../../store/ui'
import { formatHour } from '../../utils/format'
import SiteChip from '../../components/SiteChip'
import Skeleton from '../../components/Skeleton'
import ErrorState from '../../components/ErrorState'
import Button from '../../components/Button'

const labelCls = 'mb-1 block text-xs text-[var(--text-2)]'

type Props = { sites: Site[] | null; loading: boolean; error: Error | null; onRetry: () => void; onAnalyse: () => void }

export default function Controls({ sites, loading, error, onRetry, onAnalyse }: Props) {
  const s = useLunarStore()
  const openDrawer = useUI((u) => u.openDrawer)

  const days = s.rangeOn ? (Date.parse(s.dateEnd) - Date.parse(s.date)) / 86400000 + 1 : 1
  const canAnalyse = s.selectedSites.length > 0 && !!s.date && (!s.rangeOn || (!!s.dateEnd && days >= 1 && days <= 31))

  return (
    <div className="glass space-y-6 p-5">
      <section>
        <h2 className="mb-3 text-[15px]">Candidate sites</h2>
        {error && !sites ? (
          <ErrorState message={error.message} onRetry={onRetry} />
        ) : loading && !sites ? (
          <Skeleton className="h-40" />
        ) : !sites?.length ? (
          <p className="text-sm text-[var(--text-2)]">No sites yet. Add one below.</p>
        ) : (
          <ul className="space-y-1">
            {sites.map((site, i) => {
              const checked = s.selectedSites.includes(site.id)
              const full = !checked && s.selectedSites.length >= 5
              return (
                <li key={site.id} className={`flex items-start gap-3 rounded-[10px] p-2 transition ${checked ? 'bg-white/[0.06]' : 'hover:bg-white/5'}`}>
                  <input type="checkbox" id={`site-${site.id}`} checked={checked} disabled={full} onChange={() => s.toggleSite(site.id)} className="mt-1 accent-[var(--earth)]" />
                  <label htmlFor={`site-${site.id}`} className="min-w-0 flex-1 cursor-pointer">
                    <span className="flex items-center gap-2 text-sm"><SiteChip index={i} />{site.name}</span>
                    {site.coordinates ? (
                      <>
                        <span className="mono mt-1 block text-xs text-[var(--text-2)]">{site.coordinates.values.join(', ')} {site.coordinates.units}</span>
                        <span className="block text-xs text-[var(--text-2)]">{site.coordinates.frame}</span>
                      </>
                    ) : (
                      <span className="mt-1 block text-xs text-[var(--text-2)]">Coordinates: Unknown</span>
                    )}
                  </label>
                  <button type="button" onClick={() => openDrawer(`site:${site.id}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
                </li>
              )
            })}
          </ul>
        )}
        <p className="mt-2 text-xs text-[var(--text-2)]">Up to 5 sites at once.</p>
      </section>

      <section>
        <label htmlFor="lunar-date" className={labelCls}>Date (UTC)</label>
        <input id="lunar-date" type="date" value={s.date} onChange={(e) => s.setDate(e.target.value)} className="field" />
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={s.rangeOn} onChange={(e) => s.setRangeOn(e.target.checked)} className="accent-[var(--earth)]" />
          Date range (max 31 days)
        </label>
        {s.rangeOn && (
          <div className="mt-2">
            <label htmlFor="lunar-date-end" className={labelCls}>End date (UTC)</label>
            <input id="lunar-date-end" type="date" min={s.date} value={s.dateEnd} onChange={(e) => s.setDateEnd(e.target.value)} className="field" />
            {!canAnalyse && s.selectedSites.length > 0 && <p className="mt-1 text-xs text-[var(--blocked)]">End date must be after the start, within 31 days.</p>}
          </div>
        )}
      </section>

      <section>
        <label htmlFor="lunar-time" className={labelCls}>
          Time (UTC): <span className="mono text-[var(--text-1)]">{formatHour(s.timeOfDay)}</span>
        </label>
        <input id="lunar-time" type="range" min={0} max={24} step={0.25} value={s.timeOfDay} onChange={(e) => s.setTime(Number(e.target.value))} className="w-full accent-[var(--earth)]" />
        <p className="text-xs text-[var(--text-2)]">Moves the scrubber on the charts.</p>
      </section>

      <section>
        <h2 className="mb-2 text-[15px]">Observer & Earth model</h2>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="obs-height" className={labelCls}>Observer height (m)</label>
            <input
              id="obs-height"
              type="number"
              min="0"
              step="any"
              value={s.observerHeightM}
              onChange={(e) => s.setObserverHeightM(Number(e.target.value))}
              className="field"
            />
          </div>
          <div>
            <label htmlFor="earth-disk" className={labelCls}>Earth disk</label>
            <select
              id="earth-disk"
              value={s.earthDisk}
              onChange={(e) => s.setEarthDisk(e.target.value as 'center' | 'upper_limb')}
              className="field"
            >
              <option value="center">Center</option>
              <option value="upper_limb">Upper limb</option>
            </select>
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-1 text-[15px]">Solar panel (optional)</h2>
        <p className="mb-3 text-xs text-[var(--text-2)]">Without these the app shows illumination opportunity only.</p>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="panel-area" className={labelCls}>Area (m²)</label>
            <input id="panel-area" type="number" min="0" step="any" value={s.panelInputs.areaM2} onChange={(e) => s.setPanel({ areaM2: e.target.value })} className="field" />
          </div>
          <div>
            <label htmlFor="panel-eff" className={labelCls}>Efficiency (%)</label>
            <input id="panel-eff" type="number" min="0" max="100" step="any" value={s.panelInputs.efficiencyPct} onChange={(e) => s.setPanel({ efficiencyPct: e.target.value })} className="field" />
          </div>
        </div>
        <label htmlFor="panel-orient" className={`${labelCls} mt-3`}>Orientation</label>
        <select id="panel-orient" value={s.panelInputs.orientation} onChange={(e) => s.setPanel({ orientation: e.target.value as PanelInputs['orientation'] })} className="field">
          <option value="horizontal">Horizontal</option>
          <option value="tilted">Tilted</option>
        </select>
        {s.panelInputs.orientation === 'tilted' && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <label htmlFor="panel-tilt" className={labelCls}>Tilt (°)</label>
              <input id="panel-tilt" type="number" min="0" max="90" step="any" value={s.panelInputs.tiltDeg} onChange={(e) => s.setPanel({ tiltDeg: e.target.value })} className="field" />
            </div>
            <div>
              <label htmlFor="panel-az" className={labelCls}>Azimuth (°)</label>
              <input id="panel-az" type="number" min="0" max="360" step="any" value={s.panelInputs.panelAzimuthDeg} onChange={(e) => s.setPanel({ panelAzimuthDeg: e.target.value })} className="field" />
            </div>
          </div>
        )}
        <label className="mt-3 flex items-center gap-2 text-xs text-[var(--text-2)]">
          <input
            type="checkbox"
            checked={s.panelInputs.trackSunAzimuth}
            onChange={(e) => s.setPanel({ trackSunAzimuth: e.target.checked })}
            className="accent-[var(--earth)]"
          />
          Track Sun azimuth (continuous tracking)
        </label>
      </section>

      <Button type="button" variant="primary" disabled={!canAnalyse} onClick={() => { s.runAnalysis(); onAnalyse() }} className="w-full justify-center !py-3">
        Analyse
      </Button>
    </div>
  )
}
