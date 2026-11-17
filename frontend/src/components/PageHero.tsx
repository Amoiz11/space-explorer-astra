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
      className={`relative mb-8 overflow-hidden rounded-[26px] border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.45)] backdrop-blur-xl ${
        tall ? 'h-[360px] md:h-[420px]' : 'h-[280px] md:h-[340px]'
      }`}
      style={{
        background:
          'radial-gradient(ellipse 70% 60% at 50% 100%, rgba(77,163,255,0.12), transparent 70%), linear-gradient(180deg, rgba(14,24,48,0.7), rgba(5,7,13,0.95))',
      }}
    >
      {/* 3D Celestial Body Globe Scene */}
      <div
        className={
          scene.mode === 'side'
            ? 'pointer-events-none absolute inset-y-0 right-0 w-full opacity-60 md:w-[58%] md:opacity-100'
            : 'pointer-events-none absolute inset-0'
        }
      >
        <HeroScene {...scene} />
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.05 }}
        className="relative z-10 flex h-full flex-col justify-center px-6 md:px-10 max-w-xl"
      >
        {chips && <div className="mb-2 flex flex-wrap gap-2">{chips}</div>}
        <h1
          className="display font-extrabold tracking-tight text-white drop-shadow-sm"
          style={{
            fontSize: 'clamp(2rem, 4vw + 0.5rem, 3.2rem)',
            letterSpacing: '-0.025em',
            lineHeight: 1.12,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2.5 text-sm sm:text-base text-[var(--text-2)] leading-relaxed font-normal">
            {subtitle}
          </p>
        )}
        {actions && <div className="mt-5 flex flex-wrap gap-3">{actions}</div>}
      </motion.div>
    </section>
  )
}
