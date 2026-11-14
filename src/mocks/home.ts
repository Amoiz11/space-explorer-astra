import type { Body, Dataset, ImportRow } from '../types'

export const bodiesMock: Body[] = [
  { id: 'mars', name: 'Mars', missionCount: 4 },
  { id: 'moon', name: 'Moon', missionCount: 2 },
]

export const datasetsMock: Dataset[] = [
  { id: 'ds-01', name: 'Lunar elevation tiles', source: 'NASA LRO', updated: '2026-11-10' },
  { id: 'ds-02', name: 'Sun and Earth ephemeris kernels', source: 'NASA NAIF SPICE', updated: '2026-11-09' },
  { id: 'ds-03', name: 'Lunar imagery index', source: 'NASA LROC', updated: '2026-11-06' },
  { id: 'ds-04', name: 'Mission status feed', source: 'NASA PDS', updated: '2026-11-12' },
]

export const importsMock: ImportRow[] = [
  { id: 'imp-01', dataset: 'Lunar elevation tiles', status: 'ok', warnings: 0, rejected: 0, when: '2026-11-10T08:00:00Z' },
  { id: 'imp-02', dataset: 'Sun and Earth ephemeris kernels', status: 'warning', warnings: 3, rejected: 0, when: '2026-11-09T21:30:00Z' },
  { id: 'imp-03', dataset: 'Lunar imagery index', status: 'ok', warnings: 0, rejected: 2, when: '2026-11-06T12:10:00Z' },
  { id: 'imp-04', dataset: 'Mission status feed', status: 'failed', warnings: 1, rejected: 14, when: '2026-11-12T03:45:00Z' },
]
