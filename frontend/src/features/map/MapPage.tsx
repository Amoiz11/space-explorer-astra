import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getAllMissions, getExplorerLocations } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { useUI } from '../../store/ui'
import type { ExplorerPosition } from '../../types'
import Chip from '../../components/Chip'
import ErrorState from '../../components/ErrorState'
import GlassCard from '../../components/GlassCard'
import PageHero from '../../components/PageHero'
import Skeleton from '../../components/Skeleton'

export default function MapPage() {
  const { id = '' } = useParams()
  const explorerId = id || 'perseverance'
  const missions = useAsync(getAllMissions, [])
  const openDrawer = useUI((u) => u.openDrawer)

  // Resolve mission ID for this explorer
  const missionId = useMemo(() => {
    const m = (missions.data ?? []).find((item) => item.explorer_id === explorerId)
    return m ? m.id : 'mars-2020'
  }, [missions.data, explorerId])

  // Load all pages of locations (e.g. all 502 records)
  const pos = useAsync(() => getExplorerLocations(explorerId), [explorerId])

  // Layer toggle state (driven by backend layers + landing reference)
  const [enabledLayers, setEnabledLayers] = useState<Record<string, boolean>>({
    'traversed-route': true,
    'historical-positions': true,
    'landing-reference': true,
  })

  const [hoveredPoint, setHoveredPoint] = useState<ExplorerPosition | null>(null)
  const [solMin, setSolMin] = useState<string>('')
  const [solMax, setSolMax] = useState<string>('')

  const allPoints = pos.data ?? []

  // Filter points by sol range if specified
  const filtered = useMemo(() => {
    return allPoints.filter((p) => {
      if (solMin !== '' && p.sol !== null && p.sol !== undefined && p.sol < Number(solMin)) return false
      if (solMax !== '' && p.sol !== null && p.sol !== undefined && p.sol > Number(solMax)) return false
      return true
    })
  }, [allPoints, solMin, solMax])

  // Separate route points (traverse, sol >= 0, not placeholder) from landing reference points
  const routePoints = useMemo(() => {
    return filtered.filter(
      (p) => !p.is_placeholder && p.sol !== null && p.sol !== undefined && p.sol >= 0 && p.x !== null && p.y !== null
    )
  }, [filtered])

  const landingPoints = useMemo(() => {
    return filtered.filter(
      (p) => (p.is_placeholder || p.sol === -1 || p.sol === null) && p.x !== null && p.y !== null
    )
  }, [filtered])

  const validPoints = useMemo(() => {
    return filtered.filter((p) => p.x !== null && p.y !== null)
  }, [filtered])

  const latest = routePoints[routePoints.length - 1] ?? validPoints[validPoints.length - 1]

  // Coordinate projection bounds (X = East Longitude, Y = Planetocentric Latitude)
  // In PLACES: p.x is Planetocentric Latitude (~18.44°), p.y is East Longitude (~77.45°)
  const bounds = useMemo(() => {
    if (!validPoints.length) return null
    const lats = validPoints.map((p) => p.x as number)
    const lons = validPoints.map((p) => p.y as number)
    const minLat = Math.min(...lats)
    const maxLat = Math.max(...lats)
    const minLon = Math.min(...lons)
    const maxLon = Math.max(...lons)

    const latSpan = Math.max(0.0005, maxLat - minLat)
    const lonSpan = Math.max(0.0005, maxLon - minLon)

    // Add 10% padding
    return {
      minLat: minLat - latSpan * 0.1,
      maxLat: maxLat + latSpan * 0.1,
      minLon: minLon - lonSpan * 0.1,
      maxLon: maxLon + lonSpan * 0.1,
    }
  }, [validPoints])

  // SVG coordinate plot layout
  const W = 900
  const H = 500
  const padLeft = 85
  const padRight = 35
  const padTop = 35
  const padBottom = 55
  const plotW = W - padLeft - padRight
  const plotH = H - padTop - padBottom

  const projectX = (lon: number) => {
    if (!bounds) return padLeft + plotW / 2
    return padLeft + ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * plotW
  }

  const projectY = (lat: number) => {
    if (!bounds) return padTop + plotH / 2
    // SVG y-axis is inverted: higher latitude is nearer top
    return padTop + plotH - ((lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * plotH
  }

  // Generate tick marks
  const xTicks = useMemo(() => {
    if (!bounds) return []
    const count = 5
    const step = (bounds.maxLon - bounds.minLon) / (count - 1)
    return Array.from({ length: count }, (_, i) => bounds.minLon + i * step)
  }, [bounds])

  const yTicks = useMemo(() => {
    if (!bounds) return []
    const count = 5
    const step = (bounds.maxLat - bounds.minLat) / (count - 1)
    return Array.from({ length: count }, (_, i) => bounds.minLat + i * step)
  }, [bounds])

  const hasPlaceholder = allPoints.some((p) => p.is_placeholder)

  const toggleLayer = (layerKey: string) => {
    setEnabledLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }))
  }

  return (
    <div className="space-y-6">
      <PageHero
        title="Location Map"
        subtitle={`Planetocentric coordinate plot for ${explorerId}. Grounded in NASA PDS PLACES telemetry (${allPoints.length} locations loaded).`}
        chips={hasPlaceholder ? <Chip label="Placeholder data" color="var(--est)" /> : undefined}
        scene={{ body: 'mars', mode: 'rise' }}
      />

      {/* Layer Toggles & Filters */}
      <GlassCard>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-[var(--text-2)] uppercase tracking-wider mr-2">Layers:</span>
            {/* Traversed route toggle */}
            <button
              type="button"
              onClick={() => toggleLayer('traversed-route')}
              className={`btn btn-secondary !px-3 !py-1.5 text-xs ${
                enabledLayers['traversed-route'] ? '!border-[var(--earth)] !bg-[var(--earth)]/10 text-[var(--earth)]' : 'opacity-60'
              }`}
            >
              Route line (sol ≥ 0)
            </button>

            {/* Historical positions toggle */}
            <button
              type="button"
              onClick={() => toggleLayer('historical-positions')}
              className={`btn btn-secondary !px-3 !py-1.5 text-xs ${
                enabledLayers['historical-positions'] ? '!border-[var(--earth)] !bg-[var(--earth)]/10 text-[var(--earth)]' : 'opacity-60'
              }`}
            >
              Historical positions ({routePoints.length})
            </button>

            {/* Landing reference toggle */}
            <button
              type="button"
              onClick={() => toggleLayer('landing-reference')}
              className={`btn btn-secondary !px-3 !py-1.5 text-xs ${
                enabledLayers['landing-reference'] ? '!border-[var(--ok)] !bg-[var(--ok)]/10 text-[var(--ok)]' : 'opacity-60'
              }`}
            >
              Landing reference (site 1)
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <label htmlFor="sol-min" className="text-[var(--text-2)]">Sol from:</label>
              <input
                id="sol-min"
                type="number"
                min={0}
                placeholder="0"
                value={solMin}
                onChange={(e) => setSolMin(e.target.value)}
                className="field !w-20 !py-1 !text-xs"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label htmlFor="sol-max" className="text-[var(--text-2)]">to:</label>
              <input
                id="sol-max"
                type="number"
                min={0}
                placeholder="103"
                value={solMax}
                onChange={(e) => setSolMax(e.target.value)}
                className="field !w-20 !py-1 !text-xs"
              />
            </div>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-4 text-xs text-[var(--text-2)] border-t border-[var(--border)]/40 pt-3">
          <span className="flex items-center gap-1.5">
            <svg width="12" height="12"><circle cx="6" cy="6" r="4" fill="var(--earth)" /></svg>
            Rover traverse points (Estimated from PLACES best_interp)
          </span>
          <span className="flex items-center gap-1.5">
            <svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="none" stroke="var(--ok)" strokeWidth="2" /></svg>
            Landing reference site (excluded from route line)
          </span>
          <span>Click any point to inspect full provenance from NASA archive.</span>
        </div>
      </GlassCard>

      {/* Main Coordinate Plot & Sidebar */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="glass overflow-hidden p-0 relative">
          {pos.loading ? (
            <Skeleton className="h-[520px]" />
          ) : pos.error ? (
            <div className="p-6">
              <ErrorState message={pos.error.message} onRetry={pos.retry} />
            </div>
          ) : !bounds ? (
            <div className="p-12 text-center text-[var(--text-2)]">No position coordinates on record.</div>
          ) : (
            <div className="relative">
              <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full bg-[#060a14]" role="img" aria-label="Mars Planetocentric Coordinate Plot">
                {/* Background grid lines */}
                {xTicks.map((lon, i) => (
                  <line
                    key={`gx-${i}`}
                    x1={projectX(lon)}
                    x2={projectX(lon)}
                    y1={padTop}
                    y2={padTop + plotH}
                    stroke="rgba(255,255,255,0.06)"
                    strokeDasharray="2 2"
                  />
                ))}
                {yTicks.map((lat, i) => (
                  <line
                    key={`gy-${i}`}
                    x1={padLeft}
                    x2={padLeft + plotW}
                    y1={projectY(lat)}
                    y2={projectY(lat)}
                    stroke="rgba(255,255,255,0.06)"
                    strokeDasharray="2 2"
                  />
                ))}

                {/* Axes lines */}
                <line
                  x1={padLeft}
                  x2={padLeft + plotW}
                  y1={padTop + plotH}
                  y2={padTop + plotH}
                  stroke="rgba(255,255,255,0.3)"
                  strokeWidth="1.5"
                />
                <line
                  x1={padLeft}
                  x2={padLeft}
                  y1={padTop}
                  y2={padTop + plotH}
                  stroke="rgba(255,255,255,0.3)"
                  strokeWidth="1.5"
                />

                {/* X-axis tick labels (East Longitude) */}
                {xTicks.map((lon, i) => (
                  <g key={`tx-${i}`}>
                    <line
                      x1={projectX(lon)}
                      x2={projectX(lon)}
                      y1={padTop + plotH}
                      y2={padTop + plotH + 5}
                      stroke="rgba(255,255,255,0.4)"
                    />
                    <text
                      x={projectX(lon)}
                      y={padTop + plotH + 18}
                      fill="#9AA4B8"
                      fontSize="11"
                      fontFamily="monospace"
                      textAnchor="middle"
                    >
                      {lon.toFixed(4)}°E
                    </text>
                  </g>
                ))}
                <text
                  x={padLeft + plotW / 2}
                  y={padTop + plotH + 40}
                  fill="#E8ECF4"
                  fontSize="12"
                  textAnchor="middle"
                  fontWeight="500"
                >
                  East Longitude (°E, Planetocentric, IAU 2000)
                </text>

                {/* Y-axis tick labels (Planetocentric Latitude) */}
                {yTicks.map((lat, i) => (
                  <g key={`ty-${i}`}>
                    <line
                      x1={padLeft - 5}
                      x2={padLeft}
                      y1={projectY(lat)}
                      y2={projectY(lat)}
                      stroke="rgba(255,255,255,0.4)"
                    />
                    <text
                      x={padLeft - 8}
                      y={projectY(lat) + 4}
                      fill="#9AA4B8"
                      fontSize="11"
                      fontFamily="monospace"
                      textAnchor="end"
                    >
                      {lat.toFixed(4)}°N
                    </text>
                  </g>
                ))}
                <text
                  transform={`rotate(-90 ${padLeft - 55} ${padTop + plotH / 2})`}
                  x={padLeft - 55}
                  y={padTop + plotH / 2}
                  fill="#E8ECF4"
                  fontSize="12"
                  textAnchor="middle"
                  fontWeight="500"
                >
                  Planetocentric Latitude (°N)
                </text>

                {/* Traversed route line (sol >= 0, landing reference excluded) */}
                {enabledLayers['traversed-route'] && routePoints.length > 1 && (
                  <polyline
                    points={routePoints
                      .map((p) => `${projectX(p.y as number).toFixed(1)},${projectY(p.x as number).toFixed(1)}`)
                      .join(' ')}
                    fill="none"
                    stroke="var(--earth)"
                    strokeWidth="2"
                    strokeOpacity="0.75"
                  />
                )}

                {/* Landing reference points — rendered BEFORE traverse circles so circles sit on top in SVG z-order */}
                {enabledLayers['landing-reference'] &&
                  landingPoints.map((p) => {
                    const cx = projectX(p.y as number)
                    const cy = projectY(p.x as number)
                    return (
                      <g
                        key={p.id}
                        className="cursor-pointer"
                        onClick={() => openDrawer(`source:${p.product_id}`)}
                        onMouseEnter={() => setHoveredPoint(p)}
                        onMouseLeave={() => setHoveredPoint(null)}
                        tabIndex={0}
                        role="button"
                        aria-label="Landing site reference point"
                      >
                        <circle cx={cx} cy={cy} r="10" fill="none" stroke="var(--ok)" strokeWidth="2" />
                        <circle cx={cx} cy={cy} r="3" fill="var(--ok)" />
                        <line x1={cx - 14} x2={cx + 14} y1={cy} y2={cy} stroke="var(--ok)" strokeWidth="1" strokeDasharray="2 2" />
                        <line x1={cx} x2={cx} y1={cy - 14} y2={cy + 14} stroke="var(--ok)" strokeWidth="1" strokeDasharray="2 2" />
                        <text x={cx + 14} y={cy - 10} fill="var(--ok)" fontSize="11" fontWeight="bold">
                          Landing Ref
                        </text>
                      </g>
                    )
                  })}

                {/* Historical positions points — rendered last so they are on top of landing ref lines */}
                {enabledLayers['historical-positions'] &&
                  routePoints.map((p) => (
                    <circle
                      key={p.id}
                      cx={projectX(p.y as number)}
                      cy={projectY(p.x as number)}
                      r="4"
                      fill={p.label === 'Verified' ? 'var(--ok)' : 'var(--earth)'}
                      stroke="#060a14"
                      strokeWidth="1"
                      className="cursor-pointer transition-transform hover:scale-150"
                      onMouseEnter={() => setHoveredPoint(p)}
                      onMouseLeave={() => setHoveredPoint(null)}
                      onClick={() => openDrawer(`source:${p.product_id}`)}
                      tabIndex={0}
                      role="button"
                      aria-label={`Sol ${p.sol} position`}
                    />
                  ))}
              </svg>

              {/* Hover Tooltip */}
              {hoveredPoint && hoveredPoint.x !== null && hoveredPoint.y !== null && (
                <div
                  className="pointer-events-none absolute z-20 rounded-[8px] border border-[var(--border)] bg-[var(--bg-1)]/95 p-2.5 text-xs shadow-lg backdrop-blur"
                  style={{
                    left: `${Math.min(projectX(hoveredPoint.y) + 12, W - 200)}px`,
                    top: `${Math.max(projectY(hoveredPoint.x) - 70, 10)}px`,
                  }}
                >
                  <p className="font-semibold text-[var(--text-1)]">
                    {hoveredPoint.sol !== null && hoveredPoint.sol !== undefined && hoveredPoint.sol >= 0
                      ? `Sol ${hoveredPoint.sol}`
                      : 'Landing Reference Point'}
                  </p>
                  <p className="mono text-[11px] text-[var(--text-2)]">
                    {hoveredPoint.x.toFixed(6)}°N, {hoveredPoint.y.toFixed(6)}°E
                  </p>
                  {hoveredPoint.sclk && (
                    <p className="mono text-[10px] text-[var(--earth)]">SCLK: {hoveredPoint.sclk}</p>
                  )}
                  <p className="text-[10px] text-[var(--text-2)] mt-0.5">
                    Status: <span className="text-[var(--text-1)]">{hoveredPoint.label}</span>
                  </p>
                  <p className="text-[9px] text-[var(--earth)]">Click to open NASA archive provenance</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <aside className="space-y-4">
          <GlassCard title="Latest published position">
            {latest && latest.x !== null && latest.y !== null ? (
              <div className="space-y-2">
                <p className="mono text-lg font-bold text-[var(--text-1)]">
                  {latest.sol !== null && latest.sol !== undefined && latest.sol >= 0
                    ? `Sol ${latest.sol}`
                    : latest.date}
                </p>
                <dl className="mono space-y-1 text-xs">
                  <div>
                    <dt className="text-[var(--text-2)] font-[family-name:var(--font-body)]">Latitude</dt>
                    <dd>{latest.x.toFixed(6)}° N</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--text-2)] font-[family-name:var(--font-body)]">East Longitude</dt>
                    <dd>{latest.y.toFixed(6)}° E</dd>
                  </div>
                  {latest.sclk && (
                    <div>
                      <dt className="text-[var(--text-2)] font-[family-name:var(--font-body)]">Spacecraft Clock</dt>
                      <dd>{latest.sclk}</dd>
                    </div>
                  )}
                </dl>
                <div className="pt-2 flex flex-wrap items-center gap-2">
                  <Chip
                    label={latest.label || 'Estimated'}
                    color={latest.label === 'Verified' ? 'var(--ok)' : 'var(--est)'}
                  />
                  {latest.is_placeholder && <Chip label="Placeholder" color="var(--est)" />}
                </div>
                {latest.coordinate_frame && (
                  <p className="mt-2 text-xs text-[var(--text-2)] line-clamp-3" title={latest.coordinate_frame}>
                    Frame: {latest.coordinate_frame}
                  </p>
                )}
                <button
                  type="button"
                  className="mt-2 text-xs text-[var(--earth)] hover:underline block"
                  onClick={() => openDrawer(`source:${latest.product_id}`)}
                >
                  View NASA Provenance Record
                </button>
              </div>
            ) : (
              <p className="text-[var(--text-2)]">Data not available.</p>
            )}
          </GlassCard>

          <GlassCard title="Coordinate System Information">
            <div className="space-y-2 text-xs text-[var(--text-2)] leading-relaxed">
              <p>
                Coordinates are <span className="text-[var(--text-1)] font-semibold">Mars planetocentric</span> (east-positive latitude/longitude, IAU 2000), not Earth EPSG:4326.
              </p>
              <p>
                Route lines connect rover traverse points and strictly exclude landing reference markers.
              </p>
              <p className="mono text-[11px] text-[var(--text-2)] pt-1 border-t border-[var(--border)]">
                Mission: {missionId} • Product: urn:nasa:pds:mars2020_rover_places
              </p>
            </div>
          </GlassCard>

          <Link to={`/time-machine?explorer=${explorerId}`} className="btn btn-secondary w-full justify-center">
            Open Time Machine
          </Link>
        </aside>
      </div>
    </div>
  )
}
