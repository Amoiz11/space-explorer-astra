import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { Menu, Orbit, Sparkles, X } from 'lucide-react'
import { SITE_NAME } from '../config/site'
import { useUI } from '../store/ui'

const links = [
  { to: '/', label: 'Home' },
  { to: '/lunar', label: 'Lunar Navigator' },
  { to: '/missions', label: 'Missions' },
  { to: '/gallery', label: 'Gallery' },
]

export default function Nav() {
  const [open, setOpen] = useState(false)
  const openAssistant = useUI((u) => u.openAssistant)

  return (
    <header className="sticky top-3 z-30 mx-auto w-full max-w-[1280px] px-3 sm:px-4 md:px-6">
      <div className="relative flex h-14 md:h-16 items-center justify-between px-3.5 md:px-5 rounded-full border border-white/10 bg-white/[0.05] shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_8px_32px_rgba(0,0,0,0.37)] backdrop-blur-[16px] supports-[not(backdrop-filter:blur(1px))]:bg-[#070B16]">
        {/* Left: Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 font-[family-name:var(--font-heading)] text-[15px] font-semibold text-white transition-opacity hover:opacity-90"
        >
          <span className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/5 shadow-inner">
            <Orbit size={18} className="text-[var(--earth)]" />
          </span>
          <span className="hidden sm:inline tracking-tight">{SITE_NAME}</span>
        </Link>

        {/* Center: Glass Nav Links Pill */}
        <nav
          className="hidden md:flex absolute left-1/2 -translate-x-1/2 items-center gap-1 rounded-full border border-white/10 bg-white/[0.03] p-1 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
          aria-label="Main navigation"
        >
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `rounded-full px-3.5 py-1.5 text-xs font-medium transition-all duration-150 border ${
                  isActive
                    ? 'bg-white/15 text-white border-[var(--earth)]/40 shadow-[0_0_16px_rgba(77,163,255,0.3)]'
                    : 'border-transparent text-[var(--text-2)] hover:border-white/20 hover:text-white'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* Right: Glass "Ask AI" button + mobile hamburger */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={openAssistant}
            aria-label="Ask AI Assistant"
            className="flex items-center gap-1.5 rounded-full border border-white/15 bg-white/[0.06] px-3.5 py-1.5 text-xs font-medium text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_2px_8px_rgba(0,0,0,0.2)] backdrop-blur-md transition-all hover:border-[var(--earth)]/50 hover:bg-[var(--earth)]/10 hover:text-[var(--earth)] hover:shadow-[0_0_16px_rgba(77,163,255,0.25)] active:scale-95"
          >
            <Sparkles size={14} className="text-[var(--earth)]" />
            <span>Ask AI</span>
          </button>

          <button
            type="button"
            className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/5 text-[var(--text-2)] hover:text-white md:hidden"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {open && (
        <div className="mt-2 flex flex-col gap-1.5 rounded-3xl border border-white/10 bg-[var(--bg-0)]/95 p-4 shadow-2xl backdrop-blur-2xl md:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `rounded-2xl px-4 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-white/15 text-white border border-[var(--earth)]/40 shadow-[0_0_12px_rgba(77,163,255,0.25)]'
                    : 'text-[var(--text-2)] hover:text-white'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => {
              setOpen(false)
              openAssistant()
            }}
            className="mt-1 flex items-center justify-center gap-2 rounded-2xl border border-[var(--earth)]/40 bg-[var(--earth)]/10 py-2.5 text-sm font-medium text-[var(--earth)]"
          >
            <Sparkles size={16} />
            <span>Ask AI Assistant</span>
          </button>
        </div>
      )}
    </header>
  )
}
