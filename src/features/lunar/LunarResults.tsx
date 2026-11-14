import { useState } from 'react'
import { motion } from 'framer-motion'
import type { Site, SiteResult } from '../../types'
import type { Analysis } from '../../store/lunar'
import { daysBetween } from '../../utils/dates'
import SummaryCards from './SummaryCards'
import HorizonChart from './HorizonChart'
import { EarthTimeline, SunlightTimeline } from './Timelines'
import SolarCard from './SolarCard'
import TerrainPanel from './TerrainPanel'
import ComparisonSection from './ComparisonSection'
import ResearchSection from './ResearchSection'
import SectionNav from './SectionNav'

type Props = { results: SiteResult[]; sites: Site[]; analysis: Analysis }

const wrap = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.3 } } }

export default function LunarResults({ results, sites, analysis }: Props) {
  const days = daysBetween(analysis.start, analysis.end)
  const [day, setDay] = useState(0)
  const timelineProps = { results, sites, start: analysis.start, days, day: Math.min(day, days - 1), setDay }

  return (
    <motion.div key={analysis.nonce} variants={wrap} initial="hidden" animate="show" className="space-y-6">
      <SectionNav />
      <motion.div variants={item} id="summary" className="scroll-mt-32">
        <SummaryCards results={results} sites={sites} days={days} />
      </motion.div>
      <motion.div variants={item}><HorizonChart results={results} sites={sites} /></motion.div>
      <motion.div variants={item}><SunlightTimeline {...timelineProps} /></motion.div>
      <motion.div variants={item}><EarthTimeline {...timelineProps} /></motion.div>
      <motion.div variants={item}><SolarCard results={results} sites={sites} analysis={analysis} /></motion.div>
      <motion.div variants={item}><TerrainPanel siteIds={analysis.siteIds} sites={sites} nonce={analysis.nonce} /></motion.div>
      <motion.div variants={item}>
        <ComparisonSection key={analysis.nonce} siteIds={analysis.siteIds} sites={sites} initialDate={analysis.start.slice(0, 10)} />
      </motion.div>
      <motion.div variants={item}><ResearchSection results={results} sites={sites} /></motion.div>
    </motion.div>
  )
}
