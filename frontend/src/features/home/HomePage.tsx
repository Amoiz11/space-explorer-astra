import { motion, MotionConfig, type Variants } from 'framer-motion'
import { ArrowRight, Bot, Images, Moon, Rocket } from 'lucide-react'
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

/** Only the modules that still exist after removing Time Machine */
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
      {/* ── Compact hero (no tall hero block; background is the fixed scene) ── */}
      <section className="pt-8 pb-10 md:pt-14 md:pb-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl"
        >
          <h1
            className="display font-bold tracking-tight"
            style={{
              fontSize: 'clamp(2.2rem, 5vw + 1rem, 4rem)',
              lineHeight: 1.1,
              letterSpacing: '-0.03em',
            }}
          >
            Lunar Landing Site Navigator
          </h1>
          <p className="mt-4 max-w-md text-base leading-relaxed text-[var(--text-2)]">
            {SITE_TAGLINE}
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button to="/lunar" variant="primary" size="lg">
              Start exploring <ArrowRight size={16} />
            </Button>
            <Button to="/missions" variant="secondary" size="lg">
              Browse missions
            </Button>
          </div>
        </motion.div>
      </section>

      {/* ── Stats ── */}
      <section>
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

      {/* ── Modules ── */}
      <section className="mt-14">
        <h2
          className="mb-5 font-bold tracking-tight text-[var(--text-1)]"
          style={{ fontSize: 'clamp(1.1rem, 2vw + 0.5rem, 1.5rem)', letterSpacing: '-0.01em' }}
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
            <TiltCard to="/lunar" glow className="relative flex h-full min-h-[280px] flex-col justify-end overflow-hidden p-7">
              <Moon size={30} strokeWidth={1.4} className="mb-3 text-[var(--earth)]" />
              <h3
                className="font-bold tracking-tight text-[var(--text-1)]"
                style={{ fontSize: 'clamp(1.4rem, 2.5vw + 0.5rem, 2rem)', letterSpacing: '-0.02em' }}
              >
                Lunar Landing Navigator
              </h3>
              <p className="mt-2 max-w-md text-sm text-[var(--text-2)] leading-relaxed">
                Compare candidate sites by terrain, continuous illumination, and Direct-to-Earth line-of-sight.
              </p>
            </TiltCard>
          </motion.div>

          {modules.map((m) => (
            <motion.div key={m.to} variants={item}>
              <TiltCard to={m.to} className="h-full p-6">
                <m.icon size={22} strokeWidth={1.5} className="mb-4 text-[var(--earth)]" />
                <h3
                  className="font-semibold tracking-tight text-[var(--text-1)]"
                  style={{ fontSize: '1rem', letterSpacing: '-0.01em' }}
                >
                  {m.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--text-2)]">{m.text}</p>
              </TiltCard>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Data provenance ── */}
      <section className="mt-14">
        <GlassCard title="Latest published data provenance">
          <div className="space-y-3 text-sm text-[var(--text-2)]">
            <p>
              All planetary coordinates, telemetry, and camera images displayed across this navigator are retrieved
              directly from official published NASA archives (PDS Geosciences Node, NAIF SPICE, and JPL raw mission streams).
            </p>
            <div className="grid gap-4 pt-2 md:grid-cols-3">
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-bold text-white">NASA PDS PLACES</p>
                <p className="mt-1 text-xs">502 localized traverse records from Mars 2020 best_interp.csv</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-bold text-white">NASA LRO LOLA DEM</p>
                <p className="mt-1 text-xs">240 m/pixel south polar elevation model (75°S to 90°S)</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-white/5 p-4">
                <p className="font-bold text-white">NASA Mars 2020 Raw Feed</p>
                <p className="mt-1 text-xs">Verified instrument images with official NASA hotlinks</p>
              </div>
            </div>
          </div>
        </GlassCard>
      </section>
    </MotionConfig>
  )
}
