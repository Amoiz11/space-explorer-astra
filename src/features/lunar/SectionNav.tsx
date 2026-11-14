import { useEffect, useState } from 'react'

const items = [
  ['summary', 'Summary'], ['horizon', 'Horizon'], ['sunlight', 'Sunlight'], ['earth', 'Earth'],
  ['solar', 'Solar'], ['terrain', 'Terrain'], ['compare', 'Compare'], ['details', 'Details'],
]

export default function SectionNav() {
  const [active, setActive] = useState('summary')
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-30% 0px -60% 0px' },
    )
    items.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [])

  return (
    <nav aria-label="Result sections" className="sticky top-[70px] z-20 -mx-1 overflow-x-auto rounded-full border border-[var(--border)] bg-[var(--bg-1)]/80 p-1 backdrop-blur-xl">
      <ul className="flex min-w-max gap-1">
        {items.map(([id, label]) => (
          <li key={id}>
            <a href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}
              className={`block rounded-full px-3 py-1 text-sm transition-colors ${active === id ? 'bg-white/12 text-white' : 'text-[var(--text-2)] hover:text-white'}`}>
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
