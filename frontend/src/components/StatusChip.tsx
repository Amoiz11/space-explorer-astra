import type { MissionStatus } from '../types'
import Chip from './Chip'

const map: Record<MissionStatus, { label: string; color: string }> = {
  active: { label: 'Active', color: 'var(--ok)' },
  ended: { label: 'Mission ended', color: 'var(--unknown)' },
  inactive: { label: 'Inactive or communication unavailable', color: 'var(--text-1)' },
  unknown: { label: 'Unknown', color: 'var(--unknown)' },
}

export default function StatusChip({ status }: { status: MissionStatus }) {
  return <Chip label={map[status].label} color={map[status].color} />
}
