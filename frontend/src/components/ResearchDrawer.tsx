import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { getSource } from '../services'
import { useUI } from '../store/ui'
import { useAsync } from '../utils/useAsync'
import { formatDateTime } from '../utils/format'
import Chip from './Chip'
import ErrorState from './ErrorState'
import MethodChip from './MethodChip'
import Skeleton from './Skeleton'

const confColor = { Verified: 'var(--ok)', Historical: 'var(--earth)', Estimated: 'var(--est)', Unknown: 'var(--unknown)' }

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="border-b border-[var(--border)] py-3">
      <dt className="text-xs text-[var(--text-2)]">{k}</dt>
      <dd className="mt-1 text-sm">{v}</dd>
    </div>
  )
}

function Body({ target }: { target: string }) {
  const src = useAsync(() => getSource(target), [target])
  if (src.loading) return <div className="space-y-3"><Skeleton className="h-10" /><Skeleton className="h-10" /><Skeleton className="h-10" /></div>
  if (src.error) return <ErrorState message={src.error.message} onRetry={src.retry} />
  const s = src.data
  if (!s) return <p className="text-[var(--text-2)]">Data not available.</p>
  return (
    <dl>
      <Row k="Source" v={<a className="text-[var(--earth)] hover:underline" href={s.link} target="_blank" rel="noreferrer">{s.name}</a>} />
      <Row k="Product ID and version" v={<span className="mono">{s.product_id} / {s.version}</span>} />
      <Row k="Observation time" v={formatDateTime(s.observed)} />
      <Row k="Retrieval time" v={formatDateTime(s.retrieved)} />
      <Row k="Coordinate frame and units" v={`${s.frame}. ${s.units}`} />
      <Row k="Method" v={<MethodChip method={s.method} />} />
      <Row k="Uncertainty" v={s.uncertainty} />
      <Row k="Processing notes" v={s.notes} />
      <Row k="Confidence" v={<Chip label={s.confidence} color={confColor[s.confidence]} />} />
      {s.pds_lid && <Row k="PDS LID" v={<span className="mono break-all text-xs">{s.pds_lid}</span>} />}
      {s.vertical_reference && <Row k="Vertical reference" v={<span className="text-xs leading-relaxed">{s.vertical_reference}</span>} />}
      {s.sha256_checksum && <Row k="SHA-256 Checksum" v={<span className="mono break-all text-xs">{s.sha256_checksum}</span>} />}
    </dl>
  )
}

export default function ResearchDrawer() {
  const { drawerOpen, drawerTarget, closeDrawer } = useUI()
  const btn = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!drawerOpen) return
    btn.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && closeDrawer()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [drawerOpen, closeDrawer])

  return (
    <AnimatePresence>
      {drawerOpen && drawerTarget && (
        <>
          <motion.div
            className="fixed inset-0 z-50 bg-black/50"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={closeDrawer}
          />
          <motion.aside
            role="dialog"
            aria-label="Research details"
            className="fixed right-0 top-0 z-50 h-full w-full max-w-[420px] overflow-y-auto border-l border-[var(--border)] bg-[var(--bg-1)] p-6"
            initial={{ x: 440 }} animate={{ x: 0 }} exit={{ x: 440 }}
            transition={{ duration: 0.25 }}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg">Research details</h2>
              <button ref={btn} onClick={closeDrawer} aria-label="Close" className="rounded-[10px] border border-[var(--border)] p-2"><X size={16} /></button>
            </div>
            <Body target={drawerTarget} />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
