import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAllMissions, getExplorerImages, getExplorerLocations, getMission } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import { useUI } from '../../store/ui'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

const DAY = 86400000

export default function TimeMachinePage() {
  const [params, setParams] = useSearchParams()
  const explorer = params.get('explorer') ?? 'perseverance'
  const missions = useAsync(getAllMissions, [])
  const openDrawer = useUI((u) => u.openDrawer)

  const data = useAsync(async () => {
    const [mission, positions, images] = await Promise.all([
      getMission(explorer),
      getExplorerLocations(explorer),
      getExplorerImages(explorer, { limit: 120 }),
    ])
    return { mission, positions, images }
  }, [explorer])

  // Determine whether positions have real UTC observed dates or if observed_at is null (sol-driven)
  const isSolDriven = useMemo(() => {
    const pos = data.data?.positions ?? []
    if (!pos.length) return false
    // If every position date is 'Sol N' or 'SCLK N' or 'Unknown', drive by sol
    return pos.every((p) => !p.date || p.date.startsWith('Sol') || p.date.startsWith('SCLK') || p.date === 'Unknown')
  }, [data.data?.positions])

  // Sol range for sol-driven scrub
  const solRange = useMemo(() => {
    if (!isSolDriven) return null
    const pos = data.data?.positions ?? []
    const validSols = pos
      .map((p) => p.sol)
      .filter((s): s is number => s !== null && s !== undefined && s >= 0)
    if (!validSols.length) return { min: 0, max: 100 }
    return { min: Math.min(...validSols), max: Math.max(...validSols) }
  }, [isSolDriven, data.data?.positions])

  // Date range for date-driven scrub
  const dateRange = useMemo(() => {
    if (isSolDriven) return null
    const m = data.data?.mission
    if (!m) return null
    const start = Date.parse(m.landing ?? m.launch ?? '2020-01-01')
    const end = Date.parse(m.last_communication ?? '2026-11-12')
    return { start, days: Math.max(1, Math.round((end - start) / DAY)) }
  }, [isSolDriven, data.data?.mission])

  const [currentSol, setCurrentSol] = useState(0)
  const [dayOffset, setDayOffset] = useState(0)

  useEffect(() => {
    if (solRange) {
      // Start at sol 10 or min sol
      setCurrentSol(Math.min(solRange.max, Math.max(solRange.min, 10)))
    } else {
      setDayOffset(0)
    }
  }, [explorer, solRange])

  const body = (() => {
    if (data.loading) return <Skeleton className="h-64" />
    if (data.error) return <ErrorState message={data.error.message} onRetry={data.retry} />
    if (!data.data?.mission) return <p className="text-[var(--text-2)]">Data not available.</p>

    const { mission, positions, images } = data.data

    if (isSolDriven && solRange) {
      // ─── SOL-DRIVEN MODE (e.g. Perseverance with PLACES records) ────────────
      const rec = positions.find((p) => p.sol === currentSol)
      const lastBefore = [...positions]
        .filter((p) => p.sol !== null && p.sol !== undefined && p.sol < currentSol && p.kind !== 'unknown')
        .sort((a, b) => (a.sol ?? 0) - (b.sol ?? 0))
        .pop()

      // Images within 3 sols of currentSol
      const nearImages = images.filter(
        (im) => im.sol !== null && im.sol !== undefined && Math.abs(im.sol - currentSol) <= 3
      )

      const totalSols = Math.max(1, solRange.max - solRange.min)
      const solPct = (s: number) => Math.min(100, Math.max(0, ((s - solRange.min) / totalSols) * 100))

      return (
        <div className="space-y-6">
          <GlassCard>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs text-[var(--text-2)]">Time on Mars</p>
                <p className="mono text-2xl font-bold text-[var(--text-1)]">Sol {currentSol}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-[var(--text-2)]">Spacecraft Clock (SCLK)</p>
                <p className="mono text-sm text-[var(--earth)]">{rec?.sclk ? `SCLK ${rec.sclk}` : 'Unknown'}</p>
              </div>
            </div>

            <div className="relative mt-4 pt-5">
              <div aria-hidden className="absolute inset-x-0 top-0 h-4">
                {images.map((im) =>
                  im.sol !== null && im.sol !== undefined ? (
                    <span
                      key={im.id}
                      title={`${im.camera} on Sol ${im.sol}`}
                      className="absolute top-2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[var(--earth)]"
                      style={{ left: `${solPct(im.sol)}%` }}
                    />
                  ) : null
                )}
              </div>
              <input
                type="range"
                min={solRange.min}
                max={solRange.max}
                value={currentSol}
                onChange={(e) => setCurrentSol(Number(e.target.value))}
                className="w-full accent-[var(--earth)]"
                aria-label="Mission sol"
              />
              <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]">
                <span>Sol {solRange.min}</span>
                <span>Sol {solRange.max}</span>
              </div>
            </div>
            <p className="mt-2 flex gap-4 text-xs text-[var(--text-2)]">
              <span className="flex items-center gap-1.5">
                <i className="h-2 w-2 rounded-full bg-[var(--earth)]" />
                Images on record
              </span>
              <span>Scrubbing driven by Sol (observed_at timestamp is null in PDS PLACES telemetry).</span>
            </p>
          </GlassCard>

          <div className="grid gap-6 lg:grid-cols-3">
            <GlassCard title="Position on Sol">
              {rec && rec.x !== null && rec.y !== null ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="mono font-semibold">Sol {rec.sol}</span>
                    <Chip
                      label={rec.label === 'Verified' ? 'Verified' : 'Estimated'}
                      color={rec.label === 'Verified' ? 'var(--ok)' : 'var(--est)'}
                    />
                  </div>
                  <dl className="mono space-y-1.5 text-xs">
                    <div>
                      <dt className="font-[family-name:var(--font-body)] text-[var(--text-2)]">Planetocentric Latitude</dt>
                      <dd>{rec.x.toFixed(6)}° N</dd>
                    </div>
                    <div>
                      <dt className="font-[family-name:var(--font-body)] text-[var(--text-2)]">East Longitude</dt>
                      <dd>{rec.y.toFixed(6)}° E</dd>
                    </div>
                    {rec.sclk && (
                      <div>
                        <dt className="font-[family-name:var(--font-body)] text-[var(--text-2)]">SCLK Timestamp</dt>
                        <dd>{rec.sclk}</dd>
                      </div>
                    )}
                  </dl>
                  {rec.coordinate_frame && (
                    <div className="border-t border-[var(--border)] pt-2 text-[11px] text-[var(--text-2)]">
                      <span className="font-semibold block mb-0.5">Coordinate Frame:</span>
                      <p className="line-clamp-2" title={rec.coordinate_frame}>{rec.coordinate_frame}</p>
                    </div>
                  )}
                  {rec.product_id && (
                    <div className="text-[11px] text-[var(--text-2)]">
                      <span className="font-semibold block mb-0.5">Product ID:</span>
                      <p className="mono truncate" title={rec.product_id}>{rec.product_id}</p>
                      <button
                        type="button"
                        onClick={() => openDrawer(`source:${rec.product_id}`)}
                        className="mt-1 text-xs text-[var(--earth)] hover:underline"
                      >
                        View Source Provenance
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-[var(--text-1)]">No record for Sol {currentSol}</p>
                  <p className="text-sm text-[var(--text-2)]">Nothing is filled in between records.</p>
                  {lastBefore && (
                    <p className="mt-3 text-sm text-[var(--text-2)]">
                      Last recorded position: <span className="mono text-[var(--text-1)]">Sol {lastBefore.sol} {lastBefore.sclk ? `(SCLK ${lastBefore.sclk})` : ''}</span>
                    </p>
                  )}
                </div>
              )}
            </GlassCard>

            <GlassCard title="Mission key events">
              {mission.events.length ? (
                <ul className="divide-y divide-[var(--border)]">
                  {mission.events.map((e, i) => (
                    <li key={i} className="flex justify-between gap-3 py-2 text-sm">
                      <span>{e.title}</span>
                      <span className="mono text-xs text-[var(--text-2)]">{formatDate(e.date)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[var(--text-2)]">No events on record.</p>
              )}
            </GlassCard>

            <GlassCard title={`Images around Sol ${currentSol} (±3 sols)`}>
              {nearImages.length ? (
                <div className="grid grid-cols-2 gap-2">
                  {nearImages.slice(0, 4).map((im) => (
                    <div key={im.id} className="overflow-hidden rounded-[8px] border border-[var(--border)] bg-[#070b16]">
                      {im.image_url ? (
                        <img src={im.image_url} alt={im.camera} className="aspect-square w-full object-cover" />
                      ) : (
                        <div className="flex aspect-square items-center justify-center text-xs text-[var(--text-2)]">
                          {im.camera}
                        </div>
                      )}
                      <div className="p-1.5 text-[10px]">
                        <span className="font-semibold block truncate">{im.camera}</span>
                        <span className="mono text-[var(--text-2)]">Sol {im.sol}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-sm text-[var(--text-1)]">No images within 3 sols</p>
                  <p className="text-xs text-[var(--text-2)]">Nothing is interpolated between camera captures.</p>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )
    }

    // ─── DATE-DRIVEN MODE (when observed UTC dates are present) ───────────────
    if (!dateRange) return <p className="text-[var(--text-2)]">Date range unavailable.</p>
    const selMs = dateRange.start + dayOffset * DAY
    const iso = new Date(selMs).toISOString().slice(0, 10)
    const rec = positions.find((p) => p.date === iso)
    const lastBefore = [...positions].filter((p) => p.date < iso && p.kind !== 'unknown').pop()
    const events = mission.events.filter((e) => e.date <= iso).slice(-4).reverse()
    const near = images.filter((i) => Math.abs(Date.parse(i.captured) - selMs) <= 5 * DAY)
    const pct = (ms: number) => Math.min(100, Math.max(0, ((ms - dateRange.start) / (dateRange.days * DAY)) * 100))

    return (
      <div className="space-y-6">
        <GlassCard>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-[var(--text-2)]">Date</p>
            <p className="mono text-2xl">{formatDate(iso)}</p>
          </div>
          <div className="relative mt-4 pt-5">
            <div aria-hidden className="absolute inset-x-0 top-0 h-4">
              {mission.events.map((e, i) => (
                <span
                  key={i}
                  title={e.title}
                  className="absolute top-0 h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-[var(--sun)]"
                  style={{ left: `${pct(Date.parse(e.date))}%` }}
                />
              ))}
              {images.map((im) => (
                <span
                  key={im.id}
                  className="absolute top-3 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[var(--earth)]"
                  style={{ left: `${pct(Date.parse(im.captured))}%` }}
                />
              ))}
            </div>
            <input
              type="range"
              min={0}
              max={dateRange.days}
              value={dayOffset}
              onChange={(e) => setDayOffset(Number(e.target.value))}
              className="w-full accent-[var(--earth)]"
              aria-label="Mission date"
            />
            <div className="mono mt-1 flex justify-between text-[11px] text-[var(--text-2)]">
              <span>{formatDate(new Date(dateRange.start).toISOString())}</span>
              <span>{formatDate(new Date(dateRange.start + dateRange.days * DAY).toISOString())}</span>
            </div>
          </div>
          <p className="mt-2 flex gap-4 text-xs text-[var(--text-2)]">
            <span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[var(--sun)]" />Events</span>
            <span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-[var(--earth)]" />Images</span>
          </p>
        </GlassCard>

        <div className="grid gap-6 lg:grid-cols-3">
          <GlassCard title="Position">
            {rec && rec.kind !== 'unknown' ? (
              <div className="space-y-3">
                <p className="mt-3 text-sm">Position type: <span className="text-[var(--text-1)]">{rec.kind}</span></p>
                <dl className="mono space-y-1 text-xs">
                  <div><dt className="text-[var(--text-2)]">Latitude</dt><dd>{rec.x?.toFixed(5)}°</dd></div>
                  <div><dt className="text-[var(--text-2)]">Longitude</dt><dd>{rec.y?.toFixed(5)}°</dd></div>
                </dl>
              </div>
            ) : (
              <>
                <p className="text-[var(--text-1)]">No record for this date</p>
                <p className="mt-1 text-sm text-[var(--text-2)]">Nothing is filled in between records.</p>
                {lastBefore && <p className="mt-3 text-sm text-[var(--text-2)]">Last recorded position: <span className="mono text-[var(--text-1)]">{formatDate(lastBefore.date)}</span></p>}
              </>
            )}
          </GlassCard>
          <GlassCard title="Events up to this date">
            {events.length ? <ul className="divide-y divide-[var(--border)]">{events.map((e, i) => <li key={i} className="flex justify-between gap-3 py-2 text-sm"><span>{e.title}</span><span className="mono text-xs text-[var(--text-2)]">{formatDate(e.date)}</span></li>)}</ul> : <p className="text-[var(--text-2)]">No record for this date</p>}
          </GlassCard>
          <GlassCard title="Images within 5 days">
            {near.length ? (
              <div className="grid grid-cols-3 gap-2">
                {near.slice(0, 6).map((im) => (
                  <div key={im.id} className="overflow-hidden rounded-[8px] border border-[var(--border)]">
                    {im.image_url ? (
                      <img src={im.image_url} alt={im.camera} className="aspect-square w-full object-cover" />
                    ) : (
                      <div className="aspect-square bg-[#070b16] p-2 text-[10px] text-[var(--text-2)]">{im.camera}</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[var(--text-2)]">No record for this date</p>
            )}
          </GlassCard>
        </div>
      </div>
    )
  })()

  const isPlaceholder = data.data?.positions?.some((p) => p.is_placeholder) || data.data?.mission?.is_placeholder

  return (
    <div className="space-y-6">
      <PageHero
        title="Mission Time Machine"
        subtitle="Scrub through a mission and see what is on record."
        chips={isPlaceholder ? <Chip label="Placeholder data" color="var(--est)" /> : undefined}
        scene={{ body: 'earth', mode: 'side', moon: true }}
      />
      <div className="max-w-xs">
        <label htmlFor="tm-ex" className="mb-1 block text-xs text-[var(--text-2)]">Explorer</label>
        <select
          id="tm-ex"
          className="field"
          value={explorer}
          onChange={(e) => setParams({ explorer: e.target.value })}
        >
          {(missions.data ?? []).map((m) => (
            <option key={m.id} value={m.explorer_id}>{m.name}</option>
          ))}
          {!missions.data && <option value={explorer}>{explorer}</option>}
        </select>
      </div>
      {body}
    </div>
  )
}
