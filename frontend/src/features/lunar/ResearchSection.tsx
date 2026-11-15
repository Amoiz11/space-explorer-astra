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
        <Item title="SPICE kernels used">
          <p className="font-mono text-xs text-[var(--text-1)]">
            naif0012.tls, de421.bsp, pck00010.tpc, moon_pa_de421_1900-2050.bpc, moon_080317.tf, moon_assoc_me.tf
          </p>
          <p className="mt-1 text-xs text-[var(--text-2)]">Ephemeris DE421, Moon orientation frame MOON_ME_DE421.</p>
        </Item>
        <Item title="DEM product & Provenance">
          <div className="space-y-2 text-xs">
            <p><strong className="text-[var(--text-1)]">Product ID:</strong> <span className="mono">lola-dem-75s-240m</span> (240 m/pixel true at South Pole)</p>
            <p><strong className="text-[var(--text-1)]">PDS LID:</strong> <span className="mono break-all">urn:nasa:pds:lro_lola_rdr:data_gridded:ldem_75s_240m</span></p>
            <p><strong className="text-[var(--text-1)]">Vertical Reference:</strong> Reference sphere radius 1737.4 km; OFFSET = 1737400.0 m; HEIGHT = DN * 0.5 (metres relative to reference sphere)</p>
            <p><strong className="text-[var(--text-1)]">SHA-256 Checksum:</strong> <span className="mono break-all">d031efe2611b17dfbf3c158f5e15dc04cd5719349dcbf6384bb21fd97697c490</span></p>
          </div>
        </Item>
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
