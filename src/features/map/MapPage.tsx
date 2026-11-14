import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { MMGIS_URL } from '../../config/site'
import { getExplorerLocations } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import { useUI } from '../../store/ui'
import type { ExplorerPosition } from '../../types'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

type Layers = { landing: boolean; history: boolean; route: boolean; terrain: boolean; uncertainty: boolean }
const layerNames: [keyof Layers, string][] = [['landing', 'Landing site'], ['history', 'Historical positions'], ['route', 'Route'], ['terrain', 'Terrain'], ['uncertainty', 'Uncertainty']]

export default function MapPage() {
  const { id = '' } = useParams()
  const pos = useAsync(() => getExplorerLocations(id), [id])
  const openDrawer = useUI((u) => u.openDrawer)
  const [layers, setLayers] = useState<Layers>({ landing: true, history: true, route: true, terrain: true, uncertainty: false })
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')

  const filtered = useMemo(
    () => (pos.data ?? []).filter((p) => (!from || p.date >= from) && (!to || p.date <= to)),
    [pos.data, from, to],
  )
  const drawn = filtered.filter((p) => p.kind !== 'unknown' && p.x !== null && p.y !== null)
  const unknown = filtered.filter((p) => p.kind === 'unknown')
  const latest = drawn[drawn.length - 1]
  const X = (p: ExplorerPosition) => (p.x ?? 0) * 10
  const Y = (p: ExplorerPosition) => (p.y ?? 0) * 5

  return (
    <div className="space-y-6">
      <PageHero title="Location map" subtitle={`Positions for ${id}.`} chips={<Chip label="Mock data" color="var(--est)" />} scene={{ body: 'mars', mode: 'rise' }} />

      <GlassCard>
        <div className="flex flex-wrap items-end gap-4">
          <div><label htmlFor="mf" className="mb-1 block text-xs text-[var(--text-2)]">From</label><input id="mf" type="date" className="field" value={from} onChange={(e) => setFrom(e.target.value)} /></div>
          <div><label htmlFor="mt" className="mb-1 block text-xs text-[var(--text-2)]">To</label><input id="mt" type="date" className="field" value={to} onChange={(e) => setTo(e.target.value)} /></div>
          <fieldset className="flex flex-wrap gap-2"><legend className="sr-only">Layers</legend>
            {layerNames.map(([k, label]) => (
              <label key={k} className={`btn btn-secondary cursor-pointer !px-3 !py-1.5 text-sm ${layers[k] ? '!border-[var(--earth)]' : ''}`}>
                <input type="checkbox" className="sr-only" checked={layers[k]} onChange={() => setLayers({ ...layers, [k]: !layers[k] })} />{label}
              </label>
            ))}
          </fieldset>
        </div>
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-[var(--text-2)]" aria-label="Legend">
          <span className="flex items-center gap-2"><svg width="14" height="14"><circle cx="7" cy="7" r="5" fill="var(--text-1)" /></svg>Measured and localized</span>
          <span className="flex items-center gap-2"><svg width="14" height="14"><circle cx="7" cy="7" r="5" fill="none" stroke="var(--text-1)" strokeWidth="1.5" /></svg>Derived</span>
          <span className="flex items-center gap-2"><svg width="14" height="14"><circle cx="7" cy="7" r="5" fill="none" stroke="var(--est)" strokeWidth="1.5" strokeDasharray="2 2" /></svg>Interpolated</span>
          <span>Unknown positions are not drawn. They are listed on the right.</span>
        </div>
      </GlassCard>

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="glass overflow-hidden p-0">
          {MMGIS_URL ? (
            <iframe title="MMGIS map" src={MMGIS_URL} className="h-[520px] w-full border-0" />
          ) : pos.loading ? <Skeleton className="h-[520px]" /> : pos.error ? <div className="p-6"><ErrorState message={pos.error.message} onRetry={pos.retry} /></div> : (
            <svg viewBox="0 0 1000 500" className="h-auto w-full" role="img" aria-label="Placeholder map with explorer positions">
              <rect width="1000" height="500" fill="#070b16" />
              {layers.terrain && [60, 120, 190, 260].map((r, i) => <ellipse key={r} cx={300 + i * 140} cy={250 + (i % 2 ? 40 : -40)} rx={r * 1.6} ry={r} fill="none" stroke="rgba(255,255,255,0.05)" />)}
              {Array.from({ length: 9 }, (_, i) => <line key={`v${i}`} x1={i * 125} x2={i * 125} y1="0" y2="500" stroke="rgba(255,255,255,0.04)" />)}
              {Array.from({ length: 5 }, (_, i) => <line key={`h${i}`} y1={i * 125} y2={i * 125} x1="0" x2="1000" stroke="rgba(255,255,255,0.04)" />)}
              {layers.route && drawn.length > 1 && <polyline points={drawn.map((p) => `${X(p)},${Y(p)}`).join(' ')} fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" />}
              {layers.history && drawn.map((p) => (
                <g key={p.id} tabIndex={0} role="button" aria-label={`${p.kind} position on ${p.date}`} style={{ cursor: 'pointer' }}
                  onClick={() => openDrawer(`position:${p.product_id}`)} onKeyDown={(e) => e.key === 'Enter' && openDrawer(`position:${p.product_id}`)}>
                  {layers.uncertainty && p.kind !== 'measured' && <circle cx={X(p)} cy={Y(p)} r="22" fill="rgba(183,156,255,0.1)" />}
                  {p.kind === 'measured' && <circle cx={X(p)} cy={Y(p)} r="6" fill="var(--text-1)" />}
                  {p.kind === 'derived' && <circle cx={X(p)} cy={Y(p)} r="7" fill="none" stroke="var(--text-1)" strokeWidth="2" />}
                  {p.kind === 'interpolated' && <circle cx={X(p)} cy={Y(p)} r="7" fill="none" stroke="var(--est)" strokeWidth="2" strokeDasharray="3 3" />}
                </g>
              ))}
              {layers.landing && drawn[0] && (
                <g><circle cx={X(drawn[0])} cy={Y(drawn[0])} r="14" fill="none" stroke="var(--ok)" strokeWidth="2" /><text x={X(drawn[0]) + 20} y={Y(drawn[0]) - 12} fill="var(--ok)" fontSize="16">Landing site</text></g>
              )}
              <text x="16" y="484" fill="#9AA4B8" fontSize="14">Placeholder map. Set MMGIS_URL in src/config/site.ts to embed MMGIS.</text>
            </svg>
          )}
        </div>

        <aside className="space-y-4">
          <GlassCard title="Latest published position">
            {latest ? <><p className="mono">{formatDate(latest.date)}</p><button type="button" className="mt-2 text-xs text-[var(--earth)] hover:underline" onClick={() => openDrawer(`position:${latest.product_id}`)}>Details</button></> : <p className="text-[var(--text-2)]">Data not available.</p>}
          </GlassCard>
          <GlassCard title="Unknown positions">
            {unknown.length ? <ul className="mono space-y-1 text-xs">{unknown.map((p) => <li key={p.id}>{formatDate(p.date)}</li>)}</ul> : <p className="text-sm text-[var(--text-2)]">None in this range.</p>}
          </GlassCard>
          <Link to={`/time-machine?explorer=${id}`} className="btn btn-secondary w-full justify-center">Open Time Machine</Link>
        </aside>
      </div>
    </div>
  )
}
