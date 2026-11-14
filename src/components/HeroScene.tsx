import { lazy, Suspense, useMemo } from 'react'
import type { Planet3DProps } from './Planet3D'

const Planet3D = lazy(() => import('./Planet3D'))

const FALLBACK_COLORS = { earth: '#4DA3FF', moon: '#9fb0c8', mars: '#E5835A' }

function StaticPlanet({ body, mode }: Planet3DProps) {
  const c = FALLBACK_COLORS[body]
  const rise = mode === 'rise'
  return (
    <div
      aria-hidden
      className="absolute left-1/2 aspect-square -translate-x-1/2 rounded-full"
      style={{
        width: rise ? '70%' : '55%',
        top: rise ? '70%' : '50%',
        marginTop: rise ? 0 : '-14%',
        background: `radial-gradient(circle at 35% 30%, ${c} 0%, #0c1830 45%, #05070d 75%)`,
        boxShadow: `0 0 80px ${c}33`,
      }}
    />
  )
}

export default function HeroScene(props: Planet3DProps) {
  const hasWebGL = useMemo(() => {
    try {
      const c = document.createElement('canvas')
      return !!(c.getContext('webgl2') || c.getContext('webgl'))
    } catch {
      return false
    }
  }, [])

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      {hasWebGL ? (
        <Suspense fallback={<StaticPlanet {...props} />}>
          <Planet3D {...props} />
        </Suspense>
      ) : (
        <StaticPlanet {...props} />
      )}
    </div>
  )
}
