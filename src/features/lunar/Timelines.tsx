import type { EarthWindow, IlluminationWindow, Site, SiteResult } from '../../types'
import { addDaysIso } from '../../utils/dates'
import { formatTime } from '../../utils/format'
import GlassCard from '../../components/GlassCard'
import MethodChip from '../../components/MethodChip'
import SiteChip from '../../components/SiteChip'
import TimelineBand from './TimelineBand'
import WindowsTable from './WindowsTable'

type Props = { results: SiteResult[]; sites: Site[]; start: string; days: number; day: number; setDay: (n: number) => void }

const DAY = 86400000
const clip = <T extends { start: string; end: string }>(w: T, d0: number): (T & { cs: string; ce: string; ch: number }) | null => {
  const s = Math.max(Date.parse(w.start), d0)
  const e = Math.min(Date.parse(w.end), d0 + DAY)
  if (e <= s) return null
  return { ...w, cs: new Date(s).toISOString(), ce: new Date(e).toISOString(), ch: Math.round(((e - s) / 3600000) * 100) / 100 }
}

function DayPicker({ days, day, setDay }: { days: number; day: number; setDay: (n: number) => void }) {
  if (days <= 1) return null
  return (
    <label className="flex items-center gap-2 text-xs text-[var(--text-2)]">
      Day
      <select className="field !w-auto !py-1" value={day} onChange={(e) => setDay(Number(e.target.value))} aria-label="Day of the range">
        {Array.from({ length: days }, (_, i) => <option key={i} value={i}>{i + 1} of {days}</option>)}
      </select>
    </label>
  )
}

export function SunlightTimeline({ results, sites, start, days, day, setDay }: Props) {
  const dayStart = addDaysIso(start, day)
  const d0 = Date.parse(dayStart)
  return (
    <GlassCard id="sunlight" title="Illumination timeline" action={<DayPicker days={days} day={day} setDay={setDay} />}>
      <div className="space-y-6">
        {results.map((r) => {
          const idx = sites.findIndex((s) => s.id === r.siteId)
          const rows = r.windows.illumination.windows.map((w) => clip<IlluminationWindow>(w, d0)).filter((w) => w !== null)
          return (
            <div key={r.siteId}>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? r.siteId}</h3>
                <MethodChip method={r.windows.label} />
              </div>
              <TimelineBand windows={r.windows.illumination.windows} dayStart={dayStart} onColor="var(--sun)" offColor="rgba(0,0,0,0.45)" label="Sunlit windows (amber), shadow (dark)" />
              <p className="mb-1 text-xs text-[var(--text-2)]">Amber is sunlit. Dark is shadow.</p>
              <WindowsTable
                rows={rows}
                empty="No sunlit window on this day."
                columns={[
                  { header: 'Start (UTC)', cell: (w) => formatTime(w.cs) },
                  { header: 'End (UTC)', cell: (w) => formatTime(w.ce) },
                  { header: 'Duration', cell: (w) => `${w.ch} h`, align: 'right' },
                ]}
              />
            </div>
          )
        })}
      </div>
    </GlassCard>
  )
}

export function EarthTimeline({ results, sites, start, days, day, setDay }: Props) {
  const dayStart = addDaysIso(start, day)
  const d0 = Date.parse(dayStart)
  return (
    <GlassCard id="earth" title="Communication timeline" action={<DayPicker days={days} day={day} setDay={setDay} />}>
      <p className="mb-4 rounded-[10px] border border-[var(--border)] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-2)]">
        Geometric visibility only. Not a guaranteed radio link.
      </p>
      <div className="space-y-6">
        {results.map((r) => {
          const idx = sites.findIndex((s) => s.id === r.siteId)
          const rows = r.windows.earth_visibility.windows.map((w) => clip<EarthWindow>(w, d0)).filter((w) => w !== null)
          return (
            <div key={r.siteId}>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="flex items-center gap-2 text-[15px]"><SiteChip index={Math.max(idx, 0)} />{sites[idx]?.name ?? r.siteId}</h3>
                <MethodChip method={r.windows.label} />
              </div>
              <TimelineBand windows={r.windows.earth_visibility.windows} dayStart={dayStart} onColor="var(--ok)" offColor="rgba(255,107,107,0.28)" label="Earth visible (green), blocked or below horizon (red)" />
              <p className="mb-1 text-xs text-[var(--text-2)]">Green means Earth is above the horizon and not obstructed. Red means blocked or below the horizon.</p>
              <WindowsTable
                rows={rows}
                empty="Earth is not visible on this day."
                columns={[
                  { header: 'Start (UTC)', cell: (w) => formatTime(w.cs) },
                  { header: 'End (UTC)', cell: (w) => formatTime(w.ce) },
                  { header: 'Duration', cell: (w) => `${w.ch} h`, align: 'right' },
                  { header: 'Earth azimuth', cell: (w) => `${w.earth_az}°`, align: 'right' },
                  { header: 'Earth elevation', cell: (w) => `${w.earth_el}°`, align: 'right' },
                  { header: 'Obstruction', cell: (w) => (w.obstruction === 'clear' ? 'Clear' : w.obstruction === 'blocked' ? 'Blocked' : 'Unknown') },
                ]}
              />
            </div>
          )
        })}
      </div>
      <div className="mt-6 rounded-[12px] border border-[var(--border)] p-4">
        <h3 className="text-[15px]">Relay satellite communication</h3>
        <p className="mt-1 text-sm text-[var(--text-2)]">Data not available. Relay windows appear here when the backend provides them.</p>
      </div>
    </GlassCard>
  )
}
