import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Plus } from 'lucide-react'
import { createSite } from '../../services'

const empty = { name: '', v1: '', v2: '', frame: 'documented lunar frame', radius: '1000', notes: '' }

export default function AddSiteForm({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [f, setF] = useState(empty)
  const set = (k: keyof typeof empty) => (e: ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    const a = Number(f.v1), b = Number(f.v2), r = Number(f.radius)
    if (!f.name.trim() || f.v1 === '' || f.v2 === '' || Number.isNaN(a) || Number.isNaN(b) || Number.isNaN(r)) {
      setErr('Enter a name and valid numbers.')
      return
    }
    setBusy(true)
    setErr(null)
    try {
      await createSite({
        name: f.name.trim(),
        coordinates: { values: [a, b], units: 'deg', frame: f.frame.trim() || 'documented lunar frame' },
        analysis_radius_m: r,
        notes: f.notes.trim() || undefined,
      })
      onCreated()
      setF(empty)
      setOpen(false)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Could not add the site.')
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} className="btn btn-secondary mt-3 !px-3 !py-2 text-sm">
        <Plus size={14} /> Add site
      </button>
    )
  }
  return (
    <form onSubmit={submit} className="mt-3 space-y-2 rounded-[12px] border border-[var(--border)] p-3">
      <input className="field" placeholder="Site name" value={f.name} onChange={set('name')} aria-label="Site name" />
      <div className="grid grid-cols-2 gap-2">
        <input className="field" placeholder="Value 1 (deg)" value={f.v1} onChange={set('v1')} aria-label="Coordinate value 1 in degrees" />
        <input className="field" placeholder="Value 2 (deg)" value={f.v2} onChange={set('v2')} aria-label="Coordinate value 2 in degrees" />
      </div>
      <input className="field" placeholder="Coordinate frame" value={f.frame} onChange={set('frame')} aria-label="Coordinate frame" />
      <input className="field" placeholder="Analysis radius (m)" value={f.radius} onChange={set('radius')} aria-label="Analysis radius in metres" />
      <input className="field" placeholder="Notes (optional)" value={f.notes} onChange={set('notes')} aria-label="Notes" />
      <p className="text-xs text-[var(--text-2)]">Coordinates are kept as entered. They are not Earth latitude and longitude.</p>
      {err && <p className="text-xs text-[var(--blocked)]">{err}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={busy} className="btn btn-primary !px-3 !py-2 text-sm">{busy ? 'Saving...' : 'Save site'}</button>
        <button type="button" onClick={() => setOpen(false)} className="btn !px-3 !py-2 text-sm text-[var(--text-2)]">Cancel</button>
      </div>
    </form>
  )
}
