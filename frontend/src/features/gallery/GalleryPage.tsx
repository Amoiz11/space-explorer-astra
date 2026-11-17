import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ExternalLink, ImageOff, X } from 'lucide-react'
import { getAllMissions, getExplorerImages } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate, formatTime } from '../../utils/format'
import type { ExplorerImage } from '../../types'
import Chip from '../../components/Chip'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import PageHeader from '../../components/PageHeader'
import Skeleton from '../../components/Skeleton'
import TiltCard from '../../components/TiltCard'

function ImageTile({ im, onClick }: { im: ExplorerImage; onClick: () => void }) {
  const [imgFailed, setImgFailed] = useState(false)

  return (
    <button type="button" className="text-left" onClick={onClick}>
      <TiltCard className="overflow-hidden">
        <div className="relative aspect-[4/3] bg-[#0c1222] flex items-center justify-center overflow-hidden">
          {im.image_url && !imgFailed ? (
            <img
              src={im.image_url}
              alt={`${im.camera} image sol ${im.sol ?? 'unknown'}`}
              loading="lazy"
              onError={() => setImgFailed(true)}
              className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
            />
          ) : (
            <div className="flex flex-col items-center justify-center p-4 text-center text-[var(--text-2)]">
              <ImageOff size={24} className="mb-2 opacity-50" />
              <span className="mono text-[11px] font-semibold">{im.camera}</span>
              <span className="mono text-[10px] opacity-75">{im.sol !== null ? `Sol ${im.sol}` : 'Archive Record'}</span>
            </div>
          )}
          {im.is_placeholder && (
            <span className="absolute top-2 right-2">
              <Chip label="Placeholder data" color="var(--est)" />
            </span>
          )}
        </div>
        <div className="space-y-1 p-3 text-xs">
          <div className="flex items-center justify-between gap-1">
            <span className="font-semibold text-[var(--text-1)]">{im.camera}</span>
            <Chip
              label={im.label || 'Verified'}
              color={im.label === 'Verified' ? 'var(--ok)' : 'var(--est)'}
            />
          </div>
          <p className="mono text-[var(--text-2)]">
            {im.sol !== null && im.sol !== undefined ? `Sol ${im.sol} • ` : ''}
            {formatDate(im.captured)}
          </p>
          <p className="mono text-[10px] text-[var(--text-2)] truncate" title={im.product_id}>
            {im.product_id}
          </p>
          <p className="text-[10px] text-[var(--text-2)]">Credit: NASA / JPL-Caltech</p>
        </div>
      </TiltCard>
    </button>
  )
}

export default function GalleryPage() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const missions = useAsync(getAllMissions, [])
  const imgs = useAsync(() => getExplorerImages(id, { limit: 120 }), [id])
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [cam, setCam] = useState('')
  const [solFilter, setSolFilter] = useState('')
  const [visibleCount, setVisibleCount] = useState(24)
  const [open, setOpen] = useState<ExplorerImage | null>(null)

  useEffect(() => {
    if (!open) return
    const k = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(null)
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [open])

  const cams = useMemo(() => [...new Set((imgs.data ?? []).map((i) => i.camera))].sort(), [imgs.data])

  const list = useMemo(() => {
    return (imgs.data ?? []).filter((i) => {
      if (from && i.captured.slice(0, 10) < from) return false
      if (to && i.captured.slice(0, 10) > to) return false
      if (cam && i.camera !== cam) return false
      if (solFilter !== '' && i.sol !== null && i.sol !== undefined && i.sol !== Number(solFilter)) return false
      return true
    })
  }, [imgs.data, from, to, cam, solFilter])

  const hasPlaceholder = (imgs.data ?? []).some((i) => i.is_placeholder)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Image gallery"
        subtitle={`Images from ${id || 'explorer'}. Grounded in official NASA mission image archives.`}
        chip={hasPlaceholder ? <Chip label="Placeholder data" color="var(--est)" /> : undefined}
      />

      <div className="glass flex flex-wrap items-end gap-4 p-5">
        <div className="min-w-[180px]">
          <label htmlFor="gm" className="mb-1 block text-xs text-[var(--text-2)]">Mission / Explorer</label>
          <select id="gm" className="field" value={id} onChange={(e) => nav(`/explorers/${e.target.value}/gallery`)}>
            {(missions.data ?? []).map((m) => (
              <option key={m.id} value={m.explorer_id}>{m.name}</option>
            ))}
            {!missions.data && <option value={id}>{id}</option>}
          </select>
        </div>
        <div>
          <label htmlFor="gf" className="mb-1 block text-xs text-[var(--text-2)]">From</label>
          <input id="gf" type="date" className="field" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div>
          <label htmlFor="gt" className="mb-1 block text-xs text-[var(--text-2)]">To</label>
          <input id="gt" type="date" className="field" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="min-w-[140px]">
          <label htmlFor="gsol" className="mb-1 block text-xs text-[var(--text-2)]">Sol</label>
          <input
            id="gsol"
            type="number"
            min={0}
            className="field"
            placeholder="All sols"
            value={solFilter}
            onChange={(e) => setSolFilter(e.target.value)}
          />
        </div>
        <div className="min-w-[180px]">
          <label htmlFor="gc" className="mb-1 block text-xs text-[var(--text-2)]">Camera</label>
          <select id="gc" className="field" value={cam} onChange={(e) => setCam(e.target.value)}>
            <option value="">All cameras</option>
            {cams.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {imgs.loading ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-64" />)}
        </div>
      ) : imgs.error ? (
        <ErrorState message={imgs.error.message} onRetry={imgs.retry} />
      ) : !imgs.data?.length ? (
        <EmptyState text="No image records in the database yet" />
      ) : !list.length ? (
        <EmptyState text="No images match these filters." />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {list.slice(0, visibleCount).map((im) => (
              <ImageTile key={im.id} im={im} onClick={() => setOpen(im)} />
            ))}
          </div>
          {visibleCount < list.length && (
            <div className="flex justify-center pt-2">
              <button
                type="button"
                className="btn btn-secondary px-6"
                onClick={() => setVisibleCount((prev) => prev + 24)}
              >
                Load more images ({list.length - visibleCount} remaining)
              </button>
            </div>
          )}
        </div>
      )}

      {open && (
        <div
          role="dialog"
          aria-label="Image details"
          className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4"
          onClick={() => setOpen(null)}
        >
          <div className="glass w-full max-w-3xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="relative aspect-[16/10] bg-[#070b16] flex items-center justify-center overflow-hidden">
              {open.image_url ? (
                <img
                  src={open.image_url}
                  alt={`${open.camera} sol ${open.sol ?? ''}`}
                  className="max-h-full max-w-full object-contain"
                />
              ) : (
                <div className="p-8 text-center text-[var(--text-2)]">
                  <ImageOff size={40} className="mx-auto mb-2 opacity-50" />
                  <p className="font-semibold">{open.camera}</p>
                </div>
              )}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[var(--text-1)]">{open.camera}</span>
                  <Chip label={open.label || 'Verified'} color={open.label === 'Verified' ? 'var(--ok)' : 'var(--est)'} />
                  {open.is_placeholder && <Chip label="Placeholder data" color="var(--est)" />}
                </div>
                <p className="mono text-xs text-[var(--text-2)]">
                  {open.sol !== null && open.sol !== undefined ? `Sol ${open.sol} • ` : ''}
                  Captured {formatDate(open.captured)} {formatTime(open.captured)} UTC
                </p>
                <p className="mono text-[11px] text-[var(--text-2)] break-all">
                  Product ID: {open.product_id}
                </p>
                <p className="text-xs text-[var(--text-2)]">Credit: NASA / JPL-Caltech</p>
              </div>
              <div className="flex gap-2">
                <a
                  className="btn btn-secondary"
                  href={open.image_url || 'https://mars.nasa.gov/mars2020/multimedia/raw-images/'}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink size={14} /> Original NASA archive link
                </a>
                <button type="button" className="btn btn-secondary" onClick={() => setOpen(null)} aria-label="Close">
                  <X size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
