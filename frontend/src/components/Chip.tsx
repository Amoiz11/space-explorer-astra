type Props = { label: string; color?: string; className?: string }

export default function Chip({ label, color = 'var(--text-2)', className = '' }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${className}`}
      style={{ color, borderColor: 'var(--border)', background: 'rgba(255,255,255,0.03)' }}
    >
      {label}
    </span>
  )
}
