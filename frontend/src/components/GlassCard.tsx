import type { ReactNode } from 'react'

type Props = { title?: string; glow?: boolean; className?: string; action?: ReactNode; id?: string; children: ReactNode }

export default function GlassCard({ title, glow, className = '', action, id, children }: Props) {
  return (
    <section id={id} className={`glass scroll-mt-32 p-5 md:p-6 ${glow ? 'glass-glow' : ''} ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-[17px]">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}
