/**
 * BackgroundScene – fixed full-viewport ambient layer.
 * Mounted once in Layout; stays behind all page content.
 * Features:
 *  - Canvas star field (existing BackgroundParticles logic, capped dpr 1.5)
 *  - Soft route-based CSS tint overlay (cool blue / warm orange)
 *  - prefers-reduced-motion → static stars, no animation
 *  - Pauses rAF when tab is hidden
 *  - Lower particle count on narrow screens
 */
import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

type Tint = 'lunar' | 'mars' | 'default'

function routeTint(pathname: string): Tint {
  if (pathname.startsWith('/lunar')) return 'lunar'
  if (pathname.startsWith('/missions') || pathname.startsWith('/time-machine')) return 'mars'
  return 'default'
}

const TINT_STYLES: Record<Tint, string> = {
  lunar:
    'radial-gradient(ellipse 70% 60% at 60% 20%, rgba(100,180,255,0.07) 0%, transparent 70%), radial-gradient(ellipse 50% 40% at 20% 80%, rgba(140,160,255,0.05) 0%, transparent 70%)',
  mars:
    'radial-gradient(ellipse 70% 60% at 65% 20%, rgba(230,120,60,0.08) 0%, transparent 70%), radial-gradient(ellipse 50% 40% at 10% 80%, rgba(200,80,30,0.05) 0%, transparent 70%)',
  default:
    'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(77,163,255,0.07) 0%, transparent 70%)',
}

type Star = { x: number; y: number; r: number; a: number; vx: number; vy: number; ph: number }

export default function BackgroundScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const tintRef = useRef<HTMLDivElement>(null)
  const { pathname } = useLocation()

  /* ── star-field canvas ── */
  useEffect(() => {
    const canvas = canvasRef.current!
    const ctx = canvas.getContext('2d')!
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    // Cap dpr at 1.5 for perf
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
    // Fewer particles on narrow screens
    const count = window.innerWidth < 480 ? 25 : window.innerWidth < 768 ? 45 : 80

    let w = 0, h = 0, raf = 0
    let last = performance.now()
    let mx = 0, my = 0, tx = 0, ty = 0
    let stars: Star[] = []

    const init = () => {
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: 0.4 + Math.random() * 1.2,
        a: 0.15 + Math.random() * 0.5,
        // slow gentle drift
        vx: (Math.random() - 0.5) * 2.5,
        vy: (Math.random() - 0.5) * 2.5,
        ph: Math.random() * Math.PI * 2,
      }))
    }

    const draw = (now: number, dt: number) => {
      ctx.clearRect(0, 0, w, h)
      mx += (tx - mx) * 0.03
      my += (ty - my) * 0.03
      for (const s of stars) {
        if (!reduce) {
          s.x += s.vx * dt
          s.y += s.vy * dt
          if (s.x < -5) s.x = w + 5
          if (s.x > w + 5) s.x = -5
          if (s.y < -5) s.y = h + 5
          if (s.y > h + 5) s.y = -5
        }
        const twinkle = reduce ? 1 : 0.65 + 0.35 * Math.sin(now / 1200 + s.ph)
        const depth = s.r / 1.6
        ctx.globalAlpha = s.a * twinkle * 0.35 // overall opacity kept low (~0.35)
        ctx.fillStyle = '#E8ECF4'
        ctx.beginPath()
        ctx.arc(s.x + mx * 10 * depth, s.y + my * 10 * depth, s.r, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalAlpha = 1
    }

    const resize = () => {
      w = window.innerWidth
      h = window.innerHeight
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = w + 'px'
      canvas.style.height = h + 'px'
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      init()
      draw(performance.now(), 0)
    }

    const loop = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.1)
      last = now
      draw(now, dt)
      raf = requestAnimationFrame(loop)
    }

    const onMouse = (e: MouseEvent) => {
      tx = e.clientX / window.innerWidth - 0.5
      ty = e.clientY / window.innerHeight - 0.5
    }

    const onVisibility = () => {
      if (reduce) return
      if (document.hidden) {
        cancelAnimationFrame(raf)
      } else {
        last = performance.now()
        raf = requestAnimationFrame(loop)
      }
    }

    resize()
    window.addEventListener('resize', resize, { passive: true })
    document.addEventListener('visibilitychange', onVisibility)
    if (!reduce) {
      window.addEventListener('mousemove', onMouse, { passive: true })
      raf = requestAnimationFrame(loop)
    }

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMouse)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [])

  /* ── route tint (CSS transition handles the fade) ── */
  const tint = routeTint(pathname)

  return (
    <>
      {/* Star canvas – fixed behind everything */}
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0"
      />

      {/* Tint overlay – fades between routes */}
      <div
        ref={tintRef}
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 transition-[background] duration-700"
        style={{ background: TINT_STYLES[tint] }}
      />

      {/* Dark gradient at bottom for readability */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-0 h-48"
        style={{
          background:
            'linear-gradient(to top, var(--bg-0) 0%, transparent 100%)',
        }}
      />
    </>
  )
}
