import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ExternalLink, X } from 'lucide-react'
import { getAllMissions, getExplorerImages } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate, formatTime } from '../../utils/format'
import type { ExplorerImage } from '../../types'
import Chip from '../../components/Chip'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'
import TiltCard from '../../components/TiltCard'

const thumb = (hue: number) => `linear-gradient(135deg, hsl(${hue} 45% 28%), hsl(${(hue + 40) % 360} 50% 12%))`

export default function GalleryPage() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const imgs = useAsync(() => getExplorerImages(id), [id])
  const missions = useAsync(getAllMissions, [])
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [cam, setCam] = useState('')
  const [open, setOpen] = useState<ExplorerImage | null>(null)

  useEffect(() => {
    if (!open) return
    const k = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(null)
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [open])

  const cams = useMemo(() => [...new Set((imgs.data ?? []).map((i) => i.camera))], [imgs.data])
  const list = (imgs.data ?? []).filter((i) => (!from || i.captured.slice(0, 10) >= from) && (!to || i.captured.slice(0, 10) <= to) && (!cam || i.camera === cam))

  return (
    <div className="space-y-6">
      <PageHero title="Image gallery" subtitle="Images from the selected explorer." chips={<Chip label="Mock data" color="var(--est)" />} scene={{ body: 'moon', mode: 'rise' }} />

      <div className="glass flex flex-wrap items-end gap-4 p-5">
        <div className="min-w-[180px]"><label htmlFor="gm" className="mb-1 block text-xs text-[var(--text-2)]">Mission</label>
          <select id="gm" className="field" value={id} onChange={(e) => nav(`/explorers/${e.target.value}/gallery`)}>
            {(missions.data ?? []).map((m) => <option key={m.id} value={m.explorer_id}>{m.name}</option>)}
            {!missions.data && <option value={id}>{id}</option>}
          </select></div>
        <div><label htmlFor="gf" className="mb-1 block text-xs text-[var(--text-2)]">From</label><input id="gf" type="date" className="field" value={from} onChange={(e) => setFrom(e.target.value)} /></div>
        <div><label htmlFor="gt" className="mb-1 block text-xs text-[var(--text-2)]">To</label><input id="gt" type="date" className="field" value={to} onChange={(e) => setTo(e.target.value)} /></div>
        <div className="min-w-[180px]"><label htmlFor="gc" className="mb-1 block text-xs text-[var(--text-2)]">Camera</label>
          <select id="gc" className="field" value={cam} onChange={(e) => setCam(e.target.value)}><option value="">All cameras</option>{cams.map((c) => <option key={c}>{c}</option>)}</select></div>
      </div>

      {imgs.loading ? <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-56" />)}</div>
        : imgs.error ? <ErrorState message={imgs.error.message} onRetry={imgs.retry} />
        : !list.length ? <EmptyState text="No images match these filters." /> : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {list.map((im) => (
            <button key={im.id} type="button" className="text-left" onClick={() => setOpen(im)}>
              <TiltCard className="overflow-hidden">
                <div className="aspect-[4/3]" style={{ background: thumb(im.hue) }} aria-hidden />
                <div className="space-y-0.5 p-3 text-xs">
                  <p className="text-sm">{im.camera}</p>
                  <p className="mono text-[var(--text-2)]">Captured {formatDate(im.captured)}</p>
                  <p className="mono text-[var(--text-2)]">{im.explorer} / {im.product_id}</p>
                </div>
              </TiltCard>
            </button>
          ))}
        </div>
      )}

      {open && (
        <div role="dialog" aria-label="Image" className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4" onClick={() => setOpen(null)}>
          <div className="glass w-full max-w-3xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="aspect-[16/10]" style={{ background: thumb(open.hue) }} />
            <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <div>
                <p>{open.camera}</p>
                <p className="mono text-xs text-[var(--text-2)]">Captured {formatDate(open.captured)} {formatTime(open.captured)} UTC. Product {open.product_id}</p>
              </div>
              <div className="flex gap-2">
                <a className="btn btn-secondary" href="https://pds.nasa.gov" target="_blank" rel="noreferrer"><ExternalLink size={14} /> Original archive link</a>
                <button type="button" className="btn btn-secondary" onClick={() => setOpen(null)} aria-label="Close"><X size={14} /></button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
