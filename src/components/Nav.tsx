import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { Menu, Orbit, X } from 'lucide-react'
import { SITE_NAME } from '../config/site'
import { useRole } from '../store/ui'
import Chip from './Chip'

const links = [
  { to: '/', label: 'Home' },
  { to: '/lunar', label: 'Lunar Navigator' },
  { to: '/missions', label: 'Missions' },
  { to: '/time-machine', label: 'Time Machine' },
  { to: '/explorers/perseverance/gallery', label: 'Gallery' },
  { to: '/compare', label: 'Compare' },
  { to: '/assistant', label: 'Assistant' },
]

export default function Nav() {
  const [open, setOpen] = useState(false)
  const role = useRole()

  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-[var(--bg-0)]/60 backdrop-blur-xl">
      <div className="mx-auto flex h-[68px] max-w-[1280px] items-center justify-between gap-3 px-4 md:px-6">
        <Link to="/" className="flex items-center gap-2.5 font-[family-name:var(--font-heading)] text-[16px] font-semibold">
          <span className="grid h-9 w-9 place-items-center rounded-xl border border-[var(--border)] bg-white/5">
            <Orbit size={18} className="text-[var(--earth)]" />
          </span>
          <span className="hidden sm:inline">{SITE_NAME}</span>
        </Link>

        <nav
          className="hidden items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--bg-1)]/70 p-1 backdrop-blur-xl lg:flex"
          aria-label="Main"
        >
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `rounded-full px-3.5 py-1.5 text-sm transition-colors ${isActive ? 'bg-white/12 text-white' : 'text-[var(--text-2)] hover:text-white'}`
              }
            >
              {l.label}
            </NavLink>
          ))}
          {role === 'Admin' && (
            <NavLink to="/admin?role=admin" className="rounded-full px-3.5 py-1.5 text-sm text-[var(--text-2)] hover:text-white">
              Admin
            </NavLink>
          )}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Chip label="Mock data" color="var(--est)" />
          <Chip label={role} />
        </div>

        <button className="rounded-[10px] border border-[var(--border)] p-2 lg:hidden" aria-label={open ? 'Close menu' : 'Open menu'} onClick={() => setOpen((o) => !o)}>
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="fixed inset-0 top-[68px] z-40 flex flex-col gap-2 bg-[var(--bg-0)]/95 p-6 backdrop-blur-xl lg:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) => `rounded-[12px] px-4 py-3 text-lg ${isActive ? 'bg-white/10' : 'text-[var(--text-2)]'}`}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      )}
    </header>
  )
}
