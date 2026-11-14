import { Link } from 'react-router-dom'
import { motion, MotionConfig, type Variants } from 'framer-motion'
import { ArrowRight, Bot, GitCompare, History, Images, Moon, Rocket } from 'lucide-react'
import HeroScene from '../../components/HeroScene'
import StatCard from '../../components/StatCard'
import GlassCard from '../../components/GlassCard'
import Skeleton from '../../components/Skeleton'
import ErrorState from '../../components/ErrorState'
import TiltCard from '../../components/TiltCard'
import Chip from '../../components/Chip'
import { getAllMissions, getBodies, getDatasets, getSites } from '../../services'
import { useAsync } from '../../utils/useAsync'
import { formatDate } from '../../utils/format'
import { SITE_TAGLINE } from '../../config/site'

const container: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }
const item: Variants = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } }

const modules = [
  { to: '/missions', title: 'Missions', text: 'Browse Mars and Moon missions.', icon: Rocket },
  { to: '/time-machine', title: 'Time Machine', text: 'Scrub through a mission timeline.', icon: History },
  { to: '/explorers/perseverance/gallery', title: 'Image Gallery', text: 'Images from explorers.', icon: Images },
  { to: '/compare', title: 'Compare', text: 'Compare missions side by side.', icon: GitCompare },
  { to: '/assistant', title: 'AI Assistant', text: 'Ask questions with cited sources.', icon: Bot },
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
  const bodies = useAsync(getBodies, [])
  const missions = useAsync(getAllMissions, [])
  const datasets = useAsync(getDatasets, [])
  const sites = useAsync(getSites, [])
  const loading = bodies.loading || datasets.loading || missions.loading
  const error = bodies.error ?? datasets.error ?? missions.error
  const retry = () => { bodies.retry(); datasets.retry(); missions.retry() }

  const dates = (datasets.data ?? []).map((d) => d.updated).sort().reverse()
  const first = sites.data?.[0]

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
            <p className="text-xs text-[var(--text-2)]">Featured site (mock)</p>
            <p className="mt-0.5 text-base">{first.name}</p>
            <p className="mono mt-1 text-xs text-[var(--text-2)]">{first.coordinates.values.join(', ')} {first.coordinates.units}</p>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="flex flex-wrap gap-2">
            <Chip label="NASA Space Apps 2026" />
            <Chip label="Mock data" color="var(--est)" />
          </div>
          <h1 className="display mt-6 text-5xl md:text-[64px]">Lunar Landing Site Navigator</h1>
          <p className="mt-6 max-w-md text-base text-[var(--text-2)]">{SITE_TAGLINE}</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/lunar" className="btn btn-primary">Start exploring <ArrowRight size={16} /></Link>
            <Link to="/missions" className="btn btn-secondary">Browse missions</Link>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="mt-6">
        {error ? (
          <ErrorState message={error.message} onRetry={retry} />
        ) : loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
        ) : (
          <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <motion.div variants={item}><StatCard label="Supported bodies" value={bodies.data?.length ? bodies.data.length : 'Unknown'} /></motion.div>
            <motion.div variants={item}><StatCard label="Missions" value={missions.data?.length ? missions.data.length : 'Unknown'} /></motion.div>
            <motion.div variants={item}><StatCard label="Datasets updated recently" value={datasets.data?.length ? datasets.data.length : 'Unknown'} /></motion.div>
            <motion.div variants={item}><StatCard label="Data freshness" value={dates[0] ? formatDate(dates[0]) : 'Unknown'} note="Date of last import" /></motion.div>
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
              <p className="mt-2 max-w-md text-[var(--text-2)]">Compare landing sites and dates by sunlight and Earth visibility.</p>
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

      {/* Datasets */}
      <section className="mt-16">
        <GlassCard title="Recently updated datasets">
          {loading ? <Skeleton className="h-24" /> : error ? <p className="text-[var(--text-2)]">Data not available.</p>
            : !datasets.data?.length ? <p className="text-[var(--text-2)]">No datasets yet.</p> : (
            <ul className="divide-y divide-[var(--border)]">
              {datasets.data.map((d) => (
                <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <div><p className="text-sm">{d.name}</p><p className="text-xs text-[var(--text-2)]">{d.source}</p></div>
                  <span className="mono text-xs text-[var(--text-2)]">{formatDate(d.updated)}</span>
                </li>
              ))}
            </ul>
          )}
        </GlassCard>
      </section>
    </MotionConfig>
  )
}
