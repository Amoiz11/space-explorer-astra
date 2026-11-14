export const DISCLAIMERS = [
  'Geometric visibility is not a guaranteed radio link.',
  'Sunlight is not guaranteed electrical power.',
  'This is a planning support tool. It does not certify any site as safe.',
  'DEM resolution does not allow detection of small rocks or micro-hazards.',
]

export default function Disclaimer() {
  return (
    <div className="glass p-5" role="note" aria-label="Disclaimers">
      <h2 className="mb-3 text-[15px]">Disclaimers</h2>
      <ul className="space-y-2 text-sm text-[var(--text-2)]">
        {DISCLAIMERS.map((d) => (
          <li key={d} className="flex gap-2"><span aria-hidden className="mt-2 h-1 w-1 shrink-0 rounded-full bg-[var(--text-2)]" />{d}</li>
        ))}
      </ul>
    </div>
  )
}
