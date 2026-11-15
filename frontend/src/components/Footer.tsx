export default function Footer() {
  return (
    <footer className="relative z-10 mt-24 border-t border-[var(--border)] bg-[var(--bg-1)]/70 backdrop-blur-xl">
      <div className="mx-auto max-w-[1280px] space-y-3 px-4 py-8 text-xs text-[var(--text-2)] md:px-6">
        <p className="font-medium text-[var(--text-1)]">
          Planning support tool, not safety certification.
        </p>
        <p>
          Data and telemetry credits: NASA Lunar Reconnaissance Orbiter (LRO) LOLA polar digital elevation models, NASA NAIF SPICE ephemeris kernels (JPL), NASA Planetary Data System (PDS) PLACES Mars 2020 localization archive, and NASA JPL-Caltech mission imagery (Mars Perseverance raw and calibrated instrument images).
        </p>
        <p className="flex flex-wrap gap-x-4 gap-y-1">
          <a className="hover:text-white" href="https://imbrium.mit.edu/" target="_blank" rel="noreferrer">NASA LRO LOLA PDS</a>
          <a className="hover:text-white" href="https://naif.jpl.nasa.gov" target="_blank" rel="noreferrer">NAIF SPICE (JPL)</a>
          <a className="hover:text-white" href="https://pds-geosciences.wustl.edu/missions/mars2020/places.htm" target="_blank" rel="noreferrer">NASA PDS PLACES</a>
          <a className="hover:text-white" href="https://mars.nasa.gov/mars2020/multimedia/raw-images/" target="_blank" rel="noreferrer">NASA Perseverance Raw Imagery</a>
          <a className="hover:text-white" href="https://www.nasa.gov" target="_blank" rel="noreferrer">NASA.gov</a>
        </p>
      </div>
    </footer>
  )
}
