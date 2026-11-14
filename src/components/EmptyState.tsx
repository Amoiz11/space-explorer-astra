export default function EmptyState({ text }: { text: string }) {
  return (
    <div className="glass flex flex-col items-center px-6 py-16 text-center">
      <svg width="180" height="90" viewBox="0 0 180 90" aria-hidden>
        <defs>
          <linearGradient id="es-g" x1="0" x2="1"><stop offset="0" stopColor="#fff" stopOpacity="0" /><stop offset=".5" stopColor="#fff" stopOpacity=".6" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></linearGradient>
        </defs>
        <rect x="0" y="60" width="180" height="30" fill="rgba(255,255,255,0.04)" />
        <line x1="0" y1="60" x2="180" y2="60" stroke="url(#es-g)" strokeWidth="2" />
        <circle cx="52" cy="46" r="14" fill="var(--sun)" opacity=".15" />
        <circle cx="52" cy="46" r="6" fill="var(--sun)" />
        <circle cx="124" cy="34" r="10" fill="var(--earth)" opacity=".15" />
        <circle cx="124" cy="34" r="4" fill="var(--earth)" />
      </svg>
      <p className="mt-6 text-[var(--text-2)]">{text}</p>
    </div>
  )
}
