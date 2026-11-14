import type { MouseEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = { to?: string; className?: string; glow?: boolean; tilt?: boolean; children: ReactNode }

export default function TiltCard({ to, className = '', glow, tilt = true, children }: Props) {
  const move = (e: MouseEvent<HTMLElement>) => {
    const el = e.currentTarget
    const r = el.getBoundingClientRect()
    const x = e.clientX - r.left
    const y = e.clientY - r.top
    el.style.setProperty('--mx', `${x}px`)
    el.style.setProperty('--my', `${y}px`)
    if (tilt && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      el.style.transform = `perspective(900px) rotateX(${(0.5 - y / r.height) * 5}deg) rotateY(${(x / r.width - 0.5) * 6}deg)`
    }
  }
  const leave = (e: MouseEvent<HTMLElement>) => {
    e.currentTarget.style.transform = ''
  }
  const cls = `glass spot ${glow ? 'glass-glow' : ''} ${className}`
  const style = { transition: 'transform 160ms ease-out, border-color 120ms, box-shadow 200ms' }

  if (to) {
    return (
      <Link to={to} className={`block ${cls}`} style={style} onMouseMove={move} onMouseLeave={leave}>
        {children}
      </Link>
    )
  }
  return (
    <div className={cls} style={style} onMouseMove={move} onMouseLeave={leave}>
      {children}
    </div>
  )
}
