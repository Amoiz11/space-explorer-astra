import { useState } from 'react'
import { useLunarStore } from '../../store/lunar'
import { formatTime } from '../../utils/format'

type Seg = { start: string; end: string }
type Props = { windows: Seg[]; dayStart: string; onColor: string; offColor: string; label: string }

const DAY = 86400000

export default function TimelineBand({ windows, dayStart, onColor, offColor, label }: Props) {
  const time = useLunarStore((s) => s.timeOfDay)
  const [hover, setHover] = useState<string | null>(null)
  const d0 = Date.parse(dayStart)
  const segs = windows
    .map((w) => ({ s: Math.max(Date.parse(w.start), d0), e: Math.min(Date.parse(w.end), d0 + DAY) }))
    .filter((w) => w.e > w.s)
  const pct = (ms: number) => ((ms - d0) / DAY) * 100

  return (
    <div>
      <div
        className="relative h-9 overflow-hidden rounded-[10px] border border-[var(--border)]"
        style={{ background: offColor }}
        role="img"
        aria-label={`${label}: ${segs.length} windows`}
      >
        {segs.map((w) => {
          const key = `${w.s}`
          return (
            <div
              key={key}
              className="absolute inset-y-0 cursor-pointer transition-[filter] hover:brightness-125"
              style={{ left: `${pct(w.s)}%`, width: `${pct(w.e) - pct(w.s)}%`, background: onColor }}
              onMouseEnter={() => setHover(`${formatTime(new Date(w.s).toISOString())} to ${formatTime(new Date(w.e).toISOString())} UTC`)}
              onMouseLeave={() => setHover(null)}
              title={`${formatTime(new Date(w.s).toISOString())} to ${formatTime(new Date(w.e).toISOString())} UTC`}
            />
          )
        })}
        <div className="pointer-events-none absolute inset-y-0 w-px bg-white" style={{ left: `${(time / 24) * 100}%` }} />
      </div>
      <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]">
        {[0, 6, 12, 18, 24].map((h) => <span key={h}>{String(h).padStart(2, '0')}:00</span>)}
      </div>
      <p className="mt-1 h-4 text-xs text-[var(--text-2)]" aria-live="polite">{hover ?? ''}</p>
    </div>
  )
}
