import { siteColor, siteLetter } from '../utils/sites'

export default function SiteChip({ index }: { index: number }) {
  return (
    <span
      aria-hidden
      className="inline-flex h-5 w-5 items-center justify-center rounded-md text-[11px] font-semibold text-[#05070D]"
      style={{ background: siteColor(index) }}
    >
      {siteLetter(index)}
    </span>
  )
}
