export default function Footer() {
  return (
    <footer className="relative z-10 mt-24 border-t border-[var(--border)] bg-[var(--bg-1)]/70 backdrop-blur-xl">
      <div className="mx-auto max-w-[1280px] space-y-3 px-4 py-8 text-xs text-[var(--text-2)] md:px-6">
        <p>Planning support tool. Not a flight-safety certification system.</p>
        <p>
          Credits: imagery and data courtesy of NASA (Blue Marble, Lunar Reconnaissance Orbiter, SPICE). Built by team
          Astra Motion for NASA Space Apps 2026.
        </p>
        <p className="flex flex-wrap gap-x-4 gap-y-1">
          <a className="hover:text-white" href="https://www.nasa.gov" target="_blank" rel="noreferrer">nasa.gov</a>
          <a className="hover:text-white" href="https://pds.nasa.gov" target="_blank" rel="noreferrer">NASA PDS</a>
          <a className="hover:text-white" href="https://naif.jpl.nasa.gov" target="_blank" rel="noreferrer">NASA NAIF SPICE</a>
          <a className="hover:text-white" href="https://trek.nasa.gov" target="_blank" rel="noreferrer">NASA Trek</a>
        </p>
      </div>
    </footer>
  )
}
