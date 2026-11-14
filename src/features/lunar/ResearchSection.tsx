import type { Site, SiteResult } from '../../types'
import { useUI } from '../../store/ui'
import Disclaimer from '../../components/Disclaimer'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'

type Props = { results: SiteResult[]; sites: Site[] }

function Item({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="group border-b border-[var(--border)] py-3 last:border-0">
      <summary className="flex cursor-pointer list-none items-center justify-between text-sm">
        {title}<span aria-hidden className="text-[var(--text-2)] transition group-open:rotate-45">+</span>
      </summary>
      <div className="mt-3 text-sm text-[var(--text-2)]">{children}</div>
    </details>
  )
}

export default function ResearchSection({ results, sites }: Props) {
  const openDrawer = useUI((u) => u.openDrawer)
  const name = (id: string) => sites.find((s) => s.id === id)?.name ?? id
  return (
    <div id="details" className="scroll-mt-32 space-y-4">
      <GlassCard title="Research details">
        <Item title="Sources">
          <ul className="space-y-2">
            {results.map((r) => (
              <li key={r.siteId} className="flex flex-wrap items-center gap-3">
                <span className="text-[var(--text-1)]">{name(r.siteId)}</span>
                <span className="mono">{r.sunEarth.source_product_id}</span>
                <button type="button" className="text-xs text-[var(--earth)] hover:underline" onClick={() => openDrawer(`result:${r.siteId}`)}>Open details</button>
              </li>
            ))}
          </ul>
        </Item>
        <Item title="SPICE kernel version">Mock kernel set (v0). The backend team reports the real kernel version here.</Item>
        <Item title="DEM product and resolution">Mock elevation product. See the terrain panel for resolution, coverage and vertical reference.</Item>
        <Item title="Method">Sun and Earth positions are modelled. Terrain values are derived from an elevation model. Windows are derived from the positions and the terrain horizon.</Item>
        <Item title="Uncertainty">{results[0]?.windows.uncertainty ?? 'Unknown'}</Item>
        <Item title="Label per result">
          <ul className="space-y-2">
            {results.map((r) => (
              <li key={r.siteId} className="flex flex-wrap items-center gap-2">
                <span className="text-[var(--text-1)]">{name(r.siteId)}</span>
                <span>Geometry</span><MethodChip method={r.sunEarth.method} />
                <span>Windows</span><MethodChip method={r.windows.label} />
              </li>
            ))}
          </ul>
        </Item>
      </GlassCard>
      <Disclaimer />
    </div>
  )
}
