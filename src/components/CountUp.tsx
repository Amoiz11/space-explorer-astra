import { useEffect, useState } from 'react'

type Props = { value: number; decimals?: number; ms?: number }

export default function CountUp({ value, decimals = 0, ms = 600 }: Props) {
  const [v, setV] = useState(0)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setV(value)
      return
    }
    let raf = 0
    const start = performance.now()
    const tick = (now: number) => {
      const p = Math.min((now - start) / ms, 1)
      setV(value * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, ms])

  return <>{v.toFixed(decimals)}</>
}
