import { Link } from 'react-router-dom'
import { motion, MotionConfig, type Variants } from 'framer-motion'
import { ArrowRight, Bot, History, Images, Moon, Rocket } from 'lucide-react'
import HeroScene from '../../components/HeroScene'
import StatCard from '../../components/StatCard'
import GlassCard from '../../components/GlassCard'
import Skeleton from '../../components/Skeleton'
import ErrorState from '../../components/ErrorState'
import TiltCard from '../../components/TiltCard'
import Chip from '../../components/Chip'
import { getAllMissions, getRovers, getSites, getExplorerImages } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { SITE_TAGLINE } from '../../config/site'

const container: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }
const item: Variants = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } }

const modules = [
  { to: '/missions', title: 'Missions', text: 'Browse Mars and Moon missions with verified parameters.', icon: Rocket },
  { to: '/time-machine', title: 'Time Machine', text: 'Scrub through rover odometry and published sols.', icon: History },
  { to: '/gallery', title: 'Image Gallery', text: 'NASA raw instrument camera imagery and archives.', icon: Images },
  { to: '/assistant', title: 'AI Assistant', text: 'Ask questions with official NASA citations.', icon: Bot },
]

function HorizonArt() {
  return (
    <svg viewBox="0 0 320 120" className="absolute right-4 top-4 hidden w-[56%] opacity-90 md:block" aria-hidden>
      <defs>
        <linearGradient id="hz" x1="0" x2="1"><stop offset="0" stopColor="#fff" stopOpacity="0" /><stop offset=".5" stopColor="#fff" stopOpacity=".7" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></linearGradient>
      </defs>
      <path d="M0 96 C40 88 70 100 110 92 S190 84 230 94 S290 90 320 96 L320 120 L0 120Z" fill="rgba(255,255,255,0.05)" />
      <line x1="0" y1="96" x2="320" y2="96" stroke="url(#hz)" strokeWidth="1.5" />
      <path d="M20 80 Q110 20 200 70" fill="none" stroke="var(--sun)" strokeOpacity=".35" strokeDasharray="3 4" />
      <path d="M90 84 Q190 36 290 64" fill="none" stroke="var(--earth)" strokeOpacity=".35" strokeDasharray="3 4" />
      <circle cx="150" cy="38" r="16" fill="var(--sun)" opacity=".15" /><circle cx="150" cy="38" r="5" fill="var(--sun)" />
      <circle cx="236" cy="50" r="13" fill="var(--earth)" opacity=".15" /><circle cx="236" cy="50" r="4" fill="var(--earth)" />
    </svg>
  )
}

export default function HomePage() {
  const missions = useAsync(getAllMissions, [])
  const rovers = useAsync(getRovers, [])
  const sites = useAsync(getSites, [])
  const images = useAsync(() => getExplorerImages('perseverance'), [])

  const loading = missions.loading || rovers.loading || sites.loading
  const error = missions.error ?? rovers.error ?? sites.error
  const retry = () => { missions.retry(); rovers.retry(); sites.retry(); images.retry() }

  const first = sites.data?.[0]
  const isPlaceholder = missions.data?.length ? missions.data.some((m) => m.is_placeholder) : false

  return (
    <MotionConfig reducedMotion="user">
      {/* Hero */}
      <section className="relative flex min-h-[calc(100svh-7rem)] items-center">
        <div className="absolute inset-y-0 right-0 w-full opacity-50 md:w-[64%] md:opacity-100">
          <HeroScene body="earth" mode="side" moon />
        </div>

        {first && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.0, duration: 0.5 }}
            className="glass absolute right-[14%] top-[16%] z-10 hidden px-4 py-3 md:block"
          >
            <p className="text-xs text-[var(--text-2)]">Candidate landing site</p>
            <p className="mt-0.5 text-base">{first.name}</p>
            {first.coordinates ? (
              <p className="mono mt-1 text-xs text-[var(--text-2)]">{first.coordinates.values.join(', ')} {first.coordinates.units}</p>
            ) : (
              <p className="mt-1 text-xs text-[var(--text-2)]">Coordinates: Unknown</p>
            )}
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="flex flex-wrap gap-2">
            <Chip label="NASA Space Apps 2026" />
            {isPlaceholder && <Chip label="Placeholder data" color="var(--est)" />}
          </div>
          <h1 className="display mt-6 text-5xl md:text-[64px]">Lunar Landing Site Navigator</h1>
          <p className="mt-6 max-w-md text-base text-[var(--text-2)]">{SITE_TAGLINE}</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/lunar" className="btn btn-primary">Start exploring <ArrowRight size={16} /></Link>
            <Link to="/missions" className="btn btn-secondary">Browse missions</Link>
          </div>
        </motion.div>
      </section>

      {/* Real Counts Stats */}
      <section className="mt-6">
        {error ? (
          <ErrorState message={error.message} onRetry={retry} />
        ) : loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
        ) : (
          <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <motion.div variants={item}><StatCard label="Missions" value={missions.data?.length ?? 'Unknown'} note="Official NASA archive" /></motion.div>
            <motion.div variants={item}><StatCard label="Explorers" value={rovers.data?.length ?? 'Unknown'} note="Active & historical rovers" /></motion.div>
            <motion.div variants={item}><StatCard label="Candidate sites" value={sites.data?.length ?? 'Unknown'} note="Moon south pole zones" /></motion.div>
            <motion.div variants={item}><StatCard label="Imported images" value={images.data?.length ?? 'Unknown'} note="NASA Perseverance raw feed" /></motion.div>
          </motion.div>
        )}
      </section>

      {/* Modules */}
      <section className="mt-16">
        <h2 className="mb-6 text-2xl">Explore modules</h2>
        <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true, margin: '-60px' }} className="grid gap-4 md:grid-cols-3">
          <motion.div variants={item} className="md:col-span-2 md:row-span-2">
            <TiltCard to="/lunar" glow className="relative flex h-full min-h-[300px] flex-col justify-end overflow-hidden p-7">
              <HorizonArt />
              <Moon size={34} strokeWidth={1.4} className="mb-4 text-[var(--earth)]" />
              <h3 className="text-3xl">Lunar Landing Navigator</h3>
              <p className="mt-2 max-w-md text-[var(--text-2)]">Compare candidate sites by terrain, continuous illumination, and Direct-to-Earth line-of-sight.</p>
            </TiltCard>
          </motion.div>
          {modules.map((m) => (
            <motion.div key={m.to} variants={item}>
              <TiltCard to={m.to} className="h-full p-6">
                <m.icon size={22} strokeWidth={1.5} className="mb-4 text-[var(--earth)]" />
                <h3 className="text-[16px]">{m.title}</h3>
                <p className="mt-2 text-sm text-[var(--text-2)]">{m.text}</p>
              </TiltCard>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Latest Published Provenance */}
      <section className="mt-16">
        <GlassCard title="Latest published data provenance">
          <div className="space-y-3 text-sm text-[var(--text-2)]">
            <p>
              All planetary coordinates, telemetry, and camera images displayed across this navigator are retrieved directly from official published NASA archives (PDS Geosciences Node, NAIF SPICE, and JPL raw mission streams).
            </p>
            <div className="grid gap-4 pt-2 md:grid-cols-3">
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-medium text-white">NASA PDS PLACES</p>
                <p className="mt-1 text-xs">502 localized traverse records from Mars 2020 best_interp.csv</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-medium text-white">NASA LRO LOLA DEM</p>
                <p className="mt-1 text-xs">240 m/pixel south polar elevation model (75°S to 90°S)</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-medium text-white">NASA Mars 2020 Raw Feed</p>
                <p className="mt-1 text-xs">Verified instrument images with official NASA hotlinks</p>
              </div>
            </div>
          </div>
        </GlassCard>
      </section>
    </MotionConfig>
  )
}
