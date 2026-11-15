import { create } from 'zustand'
import { toRange } from '../utils/dates'

export type PanelInputs = {
  areaM2: string
  efficiencyPct: string
  orientation: 'horizontal' | 'tilted'
  tiltDeg: string
  panelAzimuthDeg: string
  trackSunAzimuth: boolean
}

export type Analysis = {
  siteIds: string[]
  start: string
  end: string
  nonce: number
  panel: PanelInputs
  observerHeightM: number
  earthDisk: 'center' | 'upper_limb'
}

type State = {
  selectedSites: string[]
  date: string
  rangeOn: boolean
  dateEnd: string
  timeOfDay: number
  observerHeightM: number
  earthDisk: 'center' | 'upper_limb'
  panelInputs: PanelInputs
  analysis: Analysis | null
  toggleSite: (id: string) => void
  setDate: (d: string) => void
  setRangeOn: (v: boolean) => void
  setDateEnd: (d: string) => void
  setTime: (h: number) => void
  setObserverHeightM: (h: number) => void
  setEarthDisk: (d: 'center' | 'upper_limb') => void
  setPanel: (p: Partial<PanelInputs>) => void
  runAnalysis: () => void
}

export const useLunarStore = create<State>()((set) => ({
  selectedSites: [],
  date: '2026-12-25',
  rangeOn: false,
  dateEnd: '2026-12-31',
  timeOfDay: 12,
  observerHeightM: 0,
  earthDisk: 'center',
  panelInputs: {
    areaM2: '',
    efficiencyPct: '',
    orientation: 'horizontal',
    tiltDeg: '0',
    panelAzimuthDeg: '0',
    trackSunAzimuth: false,
  },
  analysis: null,

  toggleSite: (id) =>
    set((s) => {
      if (s.selectedSites.includes(id)) return { selectedSites: s.selectedSites.filter((x) => x !== id) }
      if (s.selectedSites.length >= 5) return {}
      return { selectedSites: [...s.selectedSites, id] }
    }),
  setDate: (date) => set({ date }),
  setRangeOn: (rangeOn) => set({ rangeOn }),
  setDateEnd: (dateEnd) => set({ dateEnd }),
  setTime: (timeOfDay) => set({ timeOfDay }),
  setObserverHeightM: (observerHeightM) => set({ observerHeightM: Math.max(0, observerHeightM) }),
  setEarthDisk: (earthDisk) => set({ earthDisk }),
  setPanel: (p) => set((s) => ({ panelInputs: { ...s.panelInputs, ...p } })),
  runAnalysis: () =>
    set((s) => {
      const { start, end } = toRange(s.date, s.rangeOn ? s.dateEnd : null)
      return {
        analysis: {
          siteIds: [...s.selectedSites],
          start,
          end,
          nonce: (s.analysis?.nonce ?? 0) + 1,
          panel: { ...s.panelInputs },
          observerHeightM: s.observerHeightM,
          earthDisk: s.earthDisk,
        },
      }
    }),
}))
