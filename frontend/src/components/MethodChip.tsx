import type { Method } from '../types'
import Chip from './Chip'

const colors: Record<Method, string> = {
  measured: 'var(--ok)',
  derived: 'var(--text-1)',
  modelled: 'var(--est)',
  unknown: 'var(--unknown)',
}

export default function MethodChip({ method }: { method: Method }) {
  return <Chip label={method} color={colors[method]} />
}
