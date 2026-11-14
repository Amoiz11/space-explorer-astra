import { useEffect, useRef, useState } from 'react'

export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(600)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(() => setW(Math.max(240, el.clientWidth)))
    ro.observe(el)
    setW(Math.max(240, el.clientWidth))
    return () => ro.disconnect()
  }, [])
  return { ref, width: w }
}
