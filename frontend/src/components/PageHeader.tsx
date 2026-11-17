/**
 * PageHeader – compact page title block.
 * Replaces the tall PageHero hero sections on all pages.
 * Title + one-liner subtitle + optional chip — no 3D scene.
 * The 3D/particle scene now lives in the fixed BackgroundScene (Layout).
 */
import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

type Props = {
  title: string
  subtitle?: string
  chip?: ReactNode
  actions?: ReactNode
}

export default function PageHeader({ title, subtitle, chip, actions }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-6 pt-2"
    >
      {chip && <div className="mb-2 flex flex-wrap gap-2">{chip}</div>}
      <h1
        className="display text-3xl font-bold tracking-tight md:text-4xl"
        style={{ letterSpacing: '-0.02em', lineHeight: 1.15 }}
      >
        {title}
      </h1>
      {subtitle && (
        <p className="mt-2 max-w-2xl text-sm text-[var(--text-2)] leading-relaxed">
          {subtitle}
        </p>
      )}
      {actions && <div className="mt-4 flex flex-wrap gap-3">{actions}</div>}
    </motion.div>
  )
}
