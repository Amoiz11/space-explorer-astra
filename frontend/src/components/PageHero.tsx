import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import HeroScene from './HeroScene'
import type { Planet3DProps } from './Planet3D'

type Props = {
  title: string
  subtitle?: string
  chips?: ReactNode
  actions?: ReactNode
  scene: Planet3DProps
  tall?: boolean
}

export default function PageHero({ title, subtitle, chips, actions, scene, tall }: Props) {
  return (
    <section
      className={`relative mb-8 overflow-hidden rounded-[22px] border border-[var(--border)] ${tall ? 'h-[420px] md:h-[480px]' : 'h-[320px] md:h-[380px]'}`}
      style={{
        background:
          'radial-gradient(ellipse 70% 60% at 50% 100%, rgba(120,150,220,0.14), transparent 70%), linear-gradient(180deg, #070B16, #05070D)',
      }}
    >
      <div className={scene.mode === 'side' ? 'absolute inset-y-0 right-0 w-full opacity-60 md:w-[60%] md:opacity-100' : 'absolute inset-0'}>
        <HeroScene {...scene} />
      </div>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="relative z-10 flex h-full flex-col px-6 pt-7 md:px-10 md:pt-9"
      >
        {chips && <div className="flex flex-wrap gap-2">{chips}</div>}
        <h1 className="display mt-4 text-4xl md:text-6xl">{title}</h1>
        {subtitle && <p className="mt-3 max-w-md text-[var(--text-2)]">{subtitle}</p>}
        {actions && <div className="mt-5 flex flex-wrap gap-3">{actions}</div>}
      </motion.div>
    </section>
  )
}
