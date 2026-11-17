import CountUp from './CountUp'
import TiltCard from './TiltCard'

type Props = { label: string; value: number | string; note?: string }

export default function StatCard({ label, value, note }: Props) {
  return (
    <TiltCard tilt={false} className="p-5">
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--text-2)]">{label}</p>
      <p className="mono mt-2 text-3xl font-bold tracking-tight text-[var(--text-1)]">
        {typeof value === 'number' ? <CountUp value={value} /> : value}
      </p>
      {note && <p className="mt-1 text-xs text-[var(--text-2)]">{note}</p>}
    </TiltCard>
  )
}
