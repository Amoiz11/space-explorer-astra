import { motion, MotionConfig, type Variants } from 'framer-motion'
import { ArrowRight, Bot, Images, Moon, Rocket } from 'lucide-react'
import HeroScene from '../../components/HeroScene'
import StatCard from '../../components/StatCard'
import GlassCard from '../../components/GlassCard'
import Skeleton from '../../components/Skeleton'
import ErrorState from '../../components/ErrorState'
import TiltCard from '../../components/TiltCard'
import Button from '../../components/Button'
import { getAllMissions, getRovers, getSites, getExplorerImages } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { SITE_TAGLINE } from '../../config/site'

const container: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }
const item: Variants = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } }

const modules = [
  { to: '/missions', title: 'Missions', text: 'Browse Mars and Moon missions with verified parameters.', icon: Rocket },
  { to: '/gallery', title: 'Image Gallery', text: 'NASA raw instrument camera imagery and archives.', icon: Images },
  { to: '/assistant', title: 'AI Assistant', text: 'Ask questions with official NASA citations.', icon: Bot },
]

export default function HomePage() {
  const missions = useAsync(getAllMissions, [])
  const rovers = useAsync(getRovers, [])
  const sites = useAsync(getSites, [])
  const images = useAsync(() => getExplorerImages('perseverance'), [])

  const loading = missions.loading || rovers.loading || sites.loading
  const error = missions.error ?? rovers.error ?? sites.error
  const retry = () => { missions.retry(); rovers.retry(); sites.retry(); images.retry() }

  return (
    <MotionConfig reducedMotion="user">
      {/* ── Hero Section with 3D Earth & Moon Globe ── */}
      <section className="relative flex min-h-[calc(100svh-7.5rem)] items-center overflow-hidden py-8">
        {/* 3D Interactive Globe Scene */}
        <div className="absolute inset-y-0 right-0 w-full opacity-60 md:w-[68%] md:opacity-100 pointer-events-none">
          <HeroScene body="earth" mode="side" moon />
        </div>

        {/* Hero Content with Bold, Modern Typography */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--earth)]/30 bg-[var(--earth)]/10 px-3.5 py-1 text-xs font-semibold text-[var(--earth)] shadow-[0_0_16px_rgba(77,163,255,0.2)] backdrop-blur-md mb-6">
            <span className="h-2 w-2 rounded-full bg-[var(--earth)] animate-pulse" />
            NASA Space Apps • Autonomous Landing Analytics
          </div>

          <h1
            className="display font-extrabold tracking-tight text-white drop-shadow-md"
            style={{
              fontSize: 'clamp(2.6rem, 5.5vw + 1rem, 4.4rem)',
              lineHeight: 1.08,
              letterSpacing: '-0.035em',
            }}
          >
            Lunar Landing <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-white via-[#C9D1E0] to-[var(--earth)] bg-clip-text text-transparent">
              Site Navigator
            </span>
          </h1>

          <p className="mt-5 max-w-lg text-base sm:text-lg leading-relaxed text-[var(--text-2)] font-normal">
            {SITE_TAGLINE}
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3.5">
            <Button to="/lunar" variant="primary" size="lg" className="shadow-[0_0_24px_rgba(77,163,255,0.35)] font-semibold">
              Start exploring <ArrowRight size={17} />
            </Button>
            <Button to="/missions" variant="secondary" size="lg" className="font-medium">
              Browse missions
            </Button>
          </div>
        </motion.div>
      </section>

      {/* ── Real Counts Stats ── */}
      <section className="mt-4">
        {error ? (
          <ErrorState message={error.message} onRetry={retry} />
        ) : loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}
          </div>
        ) : (
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 gap-4 md:grid-cols-4"
          >
            <motion.div variants={item}>
              <StatCard label="Missions" value={missions.data?.length ?? 'Unknown'} note="Official NASA archive" />
            </motion.div>
            <motion.div variants={item}>
              <StatCard label="Explorers" value={rovers.data?.length ?? 'Unknown'} note="Active & historical rovers" />
            </motion.div>
            <motion.div variants={item}>
              <StatCard label="Candidate sites" value={sites.data?.length ?? 'Unknown'} note="Moon south pole zones" />
            </motion.div>
            <motion.div variants={item}>
              <StatCard label="Imported images" value={images.data?.length ?? 'Unknown'} note="NASA Perseverance raw feed" />
            </motion.div>
          </motion.div>
        )}
      </section>

      {/* ── Modules Grid ── */}
      <section className="mt-16">
        <h2
          className="mb-6 font-bold tracking-tight text-[var(--text-1)]"
          style={{ fontSize: 'clamp(1.25rem, 2.5vw + 0.5rem, 1.75rem)', letterSpacing: '-0.02em' }}
        >
          Explore modules
        </h2>
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-60px' }}
          className="grid gap-4 md:grid-cols-3"
        >
          {/* Featured – Lunar Navigator */}
          <motion.div variants={item} className="md:col-span-2 md:row-span-2">
            <TiltCard to="/lunar" glow className="relative flex h-full min-h-[290px] flex-col justify-end overflow-hidden p-8 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
              <Moon size={34} strokeWidth={1.5} className="mb-4 text-[var(--earth)]" />
              <h3
                className="font-bold tracking-tight text-white"
                style={{ fontSize: 'clamp(1.5rem, 2.8vw + 0.5rem, 2.2rem)', letterSpacing: '-0.025em' }}
              >
                Lunar Landing Navigator
              </h3>
              <p className="mt-2.5 max-w-md text-sm sm:text-base text-[var(--text-2)] leading-relaxed">
                Compare candidate sites by terrain, continuous illumination, and Direct-to-Earth line-of-sight.
              </p>
            </TiltCard>
          </motion.div>

          {modules.map((m) => (
            <motion.div key={m.to} variants={item}>
              <TiltCard to={m.to} className="h-full p-6 border border-white/10 hover:border-white/20 transition-all">
                <m.icon size={24} strokeWidth={1.5} className="mb-4 text-[var(--earth)]" />
                <h3
                  className="font-bold tracking-tight text-[var(--text-1)]"
                  style={{ fontSize: '1.05rem', letterSpacing: '-0.01em' }}
                >
                  {m.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-2)]">{m.text}</p>
              </TiltCard>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Latest Published Data Provenance ── */}
      <section className="mt-16">
        <GlassCard title="Latest published data provenance">
          <div className="space-y-3.5 text-sm text-[var(--text-2)] leading-relaxed">
            <p>
              All planetary coordinates, telemetry, and camera images displayed across this navigator are retrieved
              directly from official published NASA archives (PDS Geosciences Node, NAIF SPICE, and JPL raw mission streams).
            </p>
            <div className="grid gap-4 pt-2 md:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-sm">
                <p className="font-bold text-white tracking-tight">NASA PDS PLACES</p>
                <p className="mt-1 text-xs text-[var(--text-2)]">502 localized traverse records from Mars 2020 best_interp.csv</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-sm">
                <p className="font-bold text-white tracking-tight">NASA LRO LOLA DEM</p>
                <p className="mt-1 text-xs text-[var(--text-2)]">240 m/pixel south polar elevation model (75°S to 90°S)</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 shadow-sm backdrop-blur-sm">
                <p className="font-bold text-white tracking-tight">NASA Mars 2020 Raw Feed</p>
                <p className="mt-1 text-xs text-[var(--text-2)]">Verified instrument images with official NASA hotlinks</p>
              </div>
            </div>
          </div>
        </GlassCard>
      </section>
    </MotionConfig>
  )
}
