import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { TriangleAlert } from 'lucide-react'
import type { Site } from '../../types'
import { getTerrain } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { useUI } from '../../store/ui'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import Skeleton from '../../components/Skeleton'
import SiteChip from '../../components/SiteChip'

type Props = { siteIds: string[]; sites: Site[]; nonce: number }

const tip = { background: '#0A0F1C', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, fontSize: 12 }

function Stat({ k, v }: { k: string; v: string }) {
  return <div><dt className="text-xs text-[var(--text-2)]">{k}</dt><dd className="mono mt-0.5 text-base">{v}</dd></div>
}

export default function TerrainPanel({ siteIds, sites, nonce }: Props) {
  const [active, setActive] = useState(siteIds[0])
  const openDrawer = useUI((u) => u.openDrawer)
  const siteId = siteIds.includes(active) ? active : siteIds[0]
  const t = useAsync(() => getTerrain(siteId), [siteId, nonce])

  return (
    <GlassCard id="terrain" title="Terrain panel">
      <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Site">
        {siteIds.map((id) => {
          const idx = sites.findIndex((s) => s.id === id)
          return (
            <button key={id} role="tab" aria-selected={id === siteId} onClick={() => setActive(id)}
              className={`btn !px-3 !py-1.5 text-sm ${id === siteId ? 'btn-secondary !border-[var(--earth)]' : 'btn-secondary'}`}>
              <SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? id}
            </button>
          )
        })}
      </div>

      {t.loading ? <Skeleton className="h-64" /> : t.error ? <ErrorState message={t.error.message} onRetry={t.retry} /> : !t.data ? (
        <p className="text-[var(--text-2)]">Data not available.</p>
      ) : (
        <>
          {t.data.dem.no_data && (
            <p className="mb-4 flex items-center gap-2 rounded-[10px] border border-[var(--border)] px-3 py-2 text-sm text-[var(--blocked)]"><TriangleAlert size={16} /> No-data cells inside the analysis radius.</p>
          )}
          <div>
            <h3 className="mb-2 text-[15px]">Slope distribution ({t.data.slope.units === 'deg' ? 'degrees' : 'percent'})</h3>
            <div className="h-56" role="img" aria-label="Slope histogram">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={t.data.slope.histogram} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis dataKey="bin" tick={{ fontSize: 12, fill: '#9AA4B8' }} unit={t.data.slope.units === 'deg' ? '°' : '%'} />
                  <YAxis tick={{ fontSize: 12, fill: '#9AA4B8' }} width={40} unit="%" />
                  <Tooltip contentStyle={tip} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                  <Bar dataKey="pct" name="Share of area (%)" fill="#9AA4B8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-5 md:grid-cols-4">
            <Stat k={`Mean slope (${t.data.slope.units})`} v={String(t.data.slope.mean)} />
            <Stat k={`Maximum slope (${t.data.slope.units})`} v={String(t.data.slope.max)} />
            <Stat k="Local relief (m)" v={String(t.data.relief_m)} />
            <Stat k="Mean elevation (m)" v={String(t.data.elevation.mean_m)} />
            <Stat k="DEM resolution" v={t.data.dem.resolution} />
            <Stat k="Coverage" v={t.data.dem.coverage} />
            <Stat k="Vertical reference" v={t.data.dem.vertical_reference} />
            <Stat k="No-data warning" v={t.data.dem.no_data ? 'Yes' : 'None'} />
          </dl>
          <div className="mt-4 flex items-center gap-3">
            <MethodChip method={t.data.label} />
            <button type="button" onClick={() => openDrawer(`terrain:${siteId}`)} className="text-xs text-[var(--earth)] hover:underline">Details</button>
          </div>
        </>
      )}
    </GlassCard>
  )
}
